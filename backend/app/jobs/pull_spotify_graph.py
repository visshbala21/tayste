"""Primary discovery: expand candidate pool via related-artists graph.

Uses Soundcharts related artists (which works on Starter tier) as primary.
Falls back to Spotify related-artists if Soundcharts is unavailable.
"""
import asyncio
import logging
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.tables import Label, Artist, PlatformAccount, RosterMembership
from app.models.base import new_uuid
from app.connectors.spotify import SpotifyConnector
from app.connectors.soundcharts import SoundchartsConnector
from app.jobs.discover import is_likely_slop
from app.services.emerging import EmergingSignals, evaluate_emerging_artist

logger = logging.getLogger(__name__)
ALLOWED_CAREER_STAGES = {"emerging", "developing"}
PROFILE_LOOKUP_CONCURRENCY = 10


async def _discover_via_soundcharts(
    db,
    sc: SoundchartsConnector,
    spotify: SpotifyConnector,
    label_id: str,
    label_name: str,
) -> int:
    """Walk Soundcharts related-artists graph from roster artists with SC accounts."""
    result = await db.execute(
        select(PlatformAccount.platform_id, PlatformAccount.artist_id)
        .join(RosterMembership, RosterMembership.artist_id == PlatformAccount.artist_id)
        .where(
            RosterMembership.label_id == label_id,
            RosterMembership.is_active == True,
            PlatformAccount.platform == "soundcharts",
        )
    )
    roster_sc = result.all()
    if not roster_sc:
        logger.info(f"No roster artists with Soundcharts accounts for {label_name}")
        return 0

    max_candidates = 50
    discovered = 0
    seen_uuids: set[str] = set()
    spotify_stats_cache: dict[str, dict] = {}

    # --- Gather all related-artist calls in parallel ---
    async def _fetch_related(sc_uuid: str):
        try:
            return await sc.get_related_artists(sc_uuid, limit=20)
        except Exception as e:
            logger.warning(f"SC related artists failed for {sc_uuid}: {e}")
            return None

    hop1_results = await asyncio.gather(
        *[_fetch_related(sc_uuid) for sc_uuid, _ in roster_sc]
    )

    # Collect all unique candidates needing profile checks
    candidates_needing_profile: list[tuple[dict, str, str]] = []  # (artist_data, rel_uuid, name)
    for related in hop1_results:
        if not related:
            continue
        for artist_data in related:
            rel_uuid = artist_data.get("sc_uuid", "")
            name = artist_data.get("name", "")
            if not rel_uuid or not name:
                continue
            if rel_uuid in seen_uuids:
                continue
            seen_uuids.add(rel_uuid)
            if is_likely_slop(name):
                continue
            candidates_needing_profile.append((artist_data, rel_uuid, name))

    # Batch profile lookups with semaphore
    sem = asyncio.Semaphore(PROFILE_LOOKUP_CONCURRENCY)

    async def _fetch_profile(sc_uuid: str):
        async with sem:
            try:
                return await sc.get_artist_profile(sc_uuid)
            except Exception:
                return None

    profiles = await asyncio.gather(
        *[_fetch_profile(rel_uuid) for _, rel_uuid, _ in candidates_needing_profile]
    )

    # Process results sequentially (DB writes need serial access)
    for (artist_data, rel_uuid, name), profile in zip(candidates_needing_profile, profiles):
        if discovered >= max_candidates:
            break
        if profile:
            career_stage = (profile.get("career_stage") or "").lower()
            if career_stage and career_stage not in ALLOWED_CAREER_STAGES:
                continue

        # Skip if SC UUID already exists
        existing = await db.execute(
            select(PlatformAccount).where(
                PlatformAccount.platform == "soundcharts",
                PlatformAccount.platform_id == rel_uuid,
            )
        )
        if existing.scalar_one_or_none():
            continue

        # Skip if artist name already exists
        existing_name = await db.execute(
            select(Artist).where(Artist.name == name)
        )
        if existing_name.scalar_one_or_none():
            continue

        # Get cross-platform IDs (single API call per artist)
        try:
            ids = await sc.get_artist_identifiers(rel_uuid)
        except Exception:
            ids = {}

        spotify_id = ids.get("spotify")
        spotify_stats = {}
        spotify_followers = None
        spotify_popularity = None
        if spotify_id and spotify.available:
            if spotify_id not in spotify_stats_cache:
                try:
                    fetched = await spotify.get_artist_stats_bulk([spotify_id])
                except Exception:
                    fetched = {}
                spotify_stats_cache[spotify_id] = fetched.get(spotify_id) or {}
            spotify_stats = spotify_stats_cache.get(spotify_id) or {}
            spotify_followers = spotify_stats.get("followers")
            spotify_popularity = spotify_stats.get("popularity")

        emerging = evaluate_emerging_artist(
            EmergingSignals(
                name=name,
                bio=(profile or {}).get("description"),
                career_stage=(profile or {}).get("career_stage"),
                spotify_followers=spotify_followers,
                spotify_popularity=spotify_popularity,
                total_followers=spotify_followers,
            ),
            strict=False,
        )
        if not emerging.is_emerging:
            continue

        artist = Artist(
            id=new_uuid(),
            name=name,
            bio=(profile or {}).get("description"),
            image_url=artist_data.get("image_url"),
            genre_tags=(profile or {}).get("genres") or [],
            is_candidate=True,
        )
        db.add(artist)
        await db.flush()

        # Soundcharts account
        db.add(PlatformAccount(
            id=new_uuid(), artist_id=artist.id, platform="soundcharts",
            platform_id=rel_uuid,
            platform_url=f"https://app.soundcharts.com/app/artist/{artist_data.get('slug') or rel_uuid}",
            platform_metadata={
                "career_stage": (profile or {}).get("career_stage"),
                "growth_level": (profile or {}).get("growth_level"),
                "genres": (profile or {}).get("genres") or [],
                "emerging_reasons": list(emerging.reasons),
            },
        ))

        # Spotify account from cross-platform IDs
        if spotify_id:
            sp_existing = await db.execute(
                select(PlatformAccount).where(
                    PlatformAccount.platform == "spotify",
                    PlatformAccount.platform_id == spotify_id,
                )
            )
            if not sp_existing.scalar_one_or_none():
                db.add(PlatformAccount(
                    id=new_uuid(), artist_id=artist.id, platform="spotify",
                    platform_id=spotify_id,
                    platform_url=f"https://open.spotify.com/artist/{spotify_id}",
                    platform_metadata={
                        "followers": spotify_followers,
                        "popularity": spotify_popularity,
                        "genres": spotify_stats.get("genres") or [],
                    },
                ))

        # YouTube account from cross-platform IDs
        yt_id = ids.get("youtube")
        if yt_id:
            yt_existing = await db.execute(
                select(PlatformAccount).where(
                    PlatformAccount.platform == "youtube",
                    PlatformAccount.platform_id == yt_id,
                )
            )
            if not yt_existing.scalar_one_or_none():
                db.add(PlatformAccount(
                    id=new_uuid(), artist_id=artist.id, platform="youtube",
                    platform_id=yt_id,
                    platform_url=f"https://youtube.com/channel/{yt_id}",
                ))

        discovered += 1

    return discovered


async def _discover_via_spotify(db, spotify: SpotifyConnector, sc: SoundchartsConnector, label_id: str, label_name: str) -> int:
    """Fallback: walk Spotify related-artists graph (requires user-auth OAuth token)."""
    result = await db.execute(
        select(PlatformAccount.platform_id, PlatformAccount.artist_id)
        .join(RosterMembership, RosterMembership.artist_id == PlatformAccount.artist_id)
        .where(
            RosterMembership.label_id == label_id,
            RosterMembership.is_active == True,
            PlatformAccount.platform == "spotify",
        )
    )
    roster_spotify = result.all()
    if not roster_spotify:
        return 0

    discovered = 0
    seen_spotify_ids: set[str] = set()

    # --- Gather all related-artist calls in parallel ---
    async def _fetch_spotify_related(spotify_id: str):
        try:
            return await spotify.get_related_artists(spotify_id)
        except Exception as e:
            logger.warning(f"Spotify related artists failed for {spotify_id}: {e}")
            return None

    hop1_results = await asyncio.gather(
        *[_fetch_spotify_related(sp_id) for sp_id, _ in roster_spotify]
    )

    # Process results sequentially (DB writes via single session)
    for related in hop1_results:
        if not related:
            continue

        for artist_data in related:
            sp_id = artist_data.get("platform_id")
            name = artist_data.get("name", "")
            if not sp_id or not name:
                continue
            if sp_id in seen_spotify_ids:
                continue
            seen_spotify_ids.add(sp_id)

            if is_likely_slop(name):
                continue

            followers = artist_data.get("followers") or 0
            popularity = artist_data.get("popularity") or 0
            sc_uuid = None
            sc_slug = None
            sc_profile = None
            if sc.available:
                try:
                    sc_artist = await sc.get_artist_by_platform_id("spotify", sp_id)
                    if sc_artist and sc_artist.get("sc_uuid"):
                        sc_uuid = sc_artist["sc_uuid"]
                        sc_slug = sc_artist.get("slug")
                        sc_profile = await sc.get_artist_profile(sc_uuid)
                except Exception:
                    sc_uuid = None
                    sc_slug = None
                    sc_profile = None

            emerging = evaluate_emerging_artist(
                EmergingSignals(
                    name=name,
                    bio=(sc_profile or {}).get("description"),
                    career_stage=(sc_profile or {}).get("career_stage"),
                    spotify_followers=followers,
                    spotify_popularity=popularity,
                    total_followers=followers,
                ),
                strict=False,
            )
            if not emerging.is_emerging:
                continue

            existing = await db.execute(
                select(PlatformAccount).where(
                    PlatformAccount.platform == "spotify",
                    PlatformAccount.platform_id == sp_id,
                )
            )
            if existing.scalar_one_or_none():
                continue

            existing_name = await db.execute(
                select(Artist).where(Artist.name == name)
            )
            if existing_name.scalar_one_or_none():
                continue

            artist = Artist(
                id=new_uuid(), name=name,
                bio=(sc_profile or {}).get("description"),
                image_url=artist_data.get("image_url"),
                genre_tags=artist_data.get("genres") or [],
                is_candidate=True,
            )
            db.add(artist)
            await db.flush()

            db.add(PlatformAccount(
                id=new_uuid(), artist_id=artist.id, platform="spotify",
                platform_id=sp_id,
                platform_url=artist_data.get("platform_url"),
                platform_metadata={
                    "followers": followers,
                    "popularity": popularity,
                    "genres": artist_data.get("genres") or [],
                    "emerging_reasons": list(emerging.reasons),
                },
            ))

            # Cross-reference with Soundcharts
            if sc_uuid:
                db.add(PlatformAccount(
                    id=new_uuid(), artist_id=artist.id, platform="soundcharts",
                    platform_id=sc_uuid,
                    platform_url=f"https://app.soundcharts.com/app/artist/{sc_slug or sc_uuid}",
                    platform_metadata={
                        "career_stage": (sc_profile or {}).get("career_stage"),
                        "growth_level": (sc_profile or {}).get("growth_level"),
                        "genres": (sc_profile or {}).get("genres") or [],
                    },
                ))

            discovered += 1

    return discovered


async def pull_graph_for_label(db, label_id: str):
    """Discover candidates via related-artists graph for a label's roster."""
    label = await db.get(Label, label_id)
    if not label:
        return

    sc = SoundchartsConnector()
    spotify = SpotifyConnector()
    discovered = 0

    # Primary: Soundcharts related artists (works on Starter tier)
    if sc.available:
        discovered = await _discover_via_soundcharts(db, sc, spotify, label_id, label.name)

    # Fallback: Spotify related artists (needs user-auth OAuth, may 403 with client credentials)
    if discovered == 0 and spotify.available:
        logger.info(f"SC discovery found 0, trying Spotify graph fallback for {label.name}")
        discovered = await _discover_via_spotify(db, spotify, sc, label_id, label.name)

    await db.flush()
    logger.info(f"Discovered {discovered} candidates via related-artist graph for label {label.name}")


async def run():
    logger.info("Starting related-artist graph discovery...")
    async with async_session_factory() as db:
        result = await db.execute(select(Label.id))
        label_ids = [r[0] for r in result.all()]
        for lid in label_ids:
            try:
                await pull_graph_for_label(db, lid)
            except Exception as e:
                logger.error(f"Graph discovery failed for label {lid}: {e}")
        await db.commit()
    logger.info("Related-artist graph discovery complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
