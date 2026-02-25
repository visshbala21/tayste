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

logger = logging.getLogger(__name__)


async def _discover_via_soundcharts(db, sc: SoundchartsConnector, label_id: str, label_name: str) -> int:
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

    discovered = 0
    seen_uuids: set[str] = set()

    for sc_uuid, _roster_artist_id in roster_sc:
        try:
            related = await sc.get_related_artists(sc_uuid, limit=40)
        except Exception as e:
            logger.warning(f"SC related artists failed for {sc_uuid}: {e}")
            continue

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

            # Get cross-platform IDs
            try:
                ids = await sc.get_artist_identifiers(rel_uuid)
            except Exception:
                ids = {}

            # Get profile for genres/image
            try:
                profile = await sc.get_artist_profile(rel_uuid)
            except Exception:
                profile = None

            artist = Artist(
                id=new_uuid(),
                name=name,
                image_url=artist_data.get("image_url") or (profile.get("image_url") if profile else None),
                genre_tags=(profile.get("genres") if profile else None) or [],
                is_candidate=True,
            )
            db.add(artist)
            await db.flush()

            # Soundcharts account
            db.add(PlatformAccount(
                id=new_uuid(), artist_id=artist.id, platform="soundcharts",
                platform_id=rel_uuid,
                platform_url=f"https://app.soundcharts.com/app/artist/{artist_data.get('slug') or rel_uuid}",
            ))

            # Spotify account from cross-platform IDs
            spotify_id = ids.get("spotify")
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

    for spotify_id, _roster_artist_id in roster_spotify:
        try:
            related = await spotify.get_related_artists(spotify_id)
        except Exception as e:
            logger.warning(f"Spotify related artists failed for {spotify_id}: {e}")
            continue

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
                image_url=artist_data.get("image_url"),
                genre_tags=artist_data.get("genres") or [],
                is_candidate=True,
            )
            db.add(artist)
            await db.flush()

            db.add(PlatformAccount(
                id=new_uuid(), artist_id=artist.id, platform="spotify",
                platform_id=sp_id, platform_url=artist_data.get("platform_url"),
            ))

            # Cross-reference with Soundcharts
            if sc.available:
                try:
                    sc_artist = await sc.get_artist_by_platform_id("spotify", sp_id)
                    if sc_artist and sc_artist.get("sc_uuid"):
                        db.add(PlatformAccount(
                            id=new_uuid(), artist_id=artist.id, platform="soundcharts",
                            platform_id=sc_artist["sc_uuid"],
                            platform_url=f"https://app.soundcharts.com/app/artist/{sc_artist.get('slug') or sc_artist['sc_uuid']}",
                        ))
                except Exception:
                    pass

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
        discovered = await _discover_via_soundcharts(db, sc, label_id, label.name)

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
