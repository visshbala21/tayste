"""Discovery job: find new candidate artists via Soundcharts rising charts,
with fallback to legacy discover.py + Soundcharts cross-referencing.

When SC discovery endpoint (POST /top/artists) is available, uses it directly.
When gated (403), falls back to legacy discover.py for candidate finding, then
cross-references all newly discovered artists with Soundcharts so they can be
enriched with time-series data.
"""
import asyncio
import logging
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.tables import Label, Artist, PlatformAccount
from app.models.base import new_uuid
from app.connectors.soundcharts import SoundchartsConnector
from app.jobs.discover import discover_for_label, is_likely_slop

logger = logging.getLogger(__name__)

MAX_CANDIDATES_PER_LABEL = 100


async def _crossref_with_soundcharts(db, sc: SoundchartsConnector):
    """Cross-reference artists that have Spotify accounts but no Soundcharts account.

    This ensures artists discovered via legacy discover.py or Spotify graph
    get Soundcharts UUIDs so they can be enriched with time-series data.
    """
    if not sc.available:
        return

    # Find artists with Spotify account but no Soundcharts account
    result = await db.execute(
        select(PlatformAccount.artist_id, PlatformAccount.platform_id).where(
            PlatformAccount.platform == "spotify",
            ~PlatformAccount.artist_id.in_(
                select(PlatformAccount.artist_id).where(
                    PlatformAccount.platform == "soundcharts"
                )
            ),
        )
    )
    unlinked = result.all()
    if not unlinked:
        return

    linked = 0
    for artist_id, spotify_id in unlinked:
        try:
            sc_artist = await sc.get_artist_by_platform_id("spotify", spotify_id)
        except Exception:
            continue
        if not sc_artist or not sc_artist.get("sc_uuid"):
            continue

        sc_uuid = sc_artist["sc_uuid"]
        # Check we don't already have this SC UUID for another artist
        existing = await db.execute(
            select(PlatformAccount).where(
                PlatformAccount.platform == "soundcharts",
                PlatformAccount.platform_id == sc_uuid,
            )
        )
        if existing.scalar_one_or_none():
            continue

        sc_account = PlatformAccount(
            id=new_uuid(),
            artist_id=artist_id,
            platform="soundcharts",
            platform_id=sc_uuid,
            platform_url=f"https://app.soundcharts.com/app/artist/{sc_artist.get('slug') or sc_uuid}",
        )
        db.add(sc_account)
        linked += 1

    await db.flush()
    if linked:
        logger.info(f"Cross-referenced {linked} artists with Soundcharts")


async def pull_for_label(db, label_id: str):
    """Discover candidate artists for a label via Soundcharts."""
    label = await db.get(Label, label_id)
    if not label:
        return

    sc = SoundchartsConnector()

    # Fallback to legacy discovery if Soundcharts unavailable
    if not sc.available:
        logger.info(f"Soundcharts unavailable, falling back to legacy discover for {label.name}")
        await discover_for_label(db, label_id)
        return

    # Extract genre targets from label
    genres = []
    if label.genre_tags:
        if isinstance(label.genre_tags, dict):
            genres.extend(label.genre_tags.get("primary", []))
            genres.extend(label.genre_tags.get("secondary", []))
        elif isinstance(label.genre_tags, list):
            genres.extend(label.genre_tags)
    if label.label_dna and isinstance(label.label_dna, dict):
        dna_genres = label.label_dna.get("sonic_tags") or label.label_dna.get("genres") or []
        for g in dna_genres:
            if g not in genres:
                genres.append(g)

    if not genres:
        logger.warning(f"No genres for label {label.name}, using label name as fallback search")
        genres = [label.name]

    discovered = 0

    for genre in genres:
        if discovered >= MAX_CANDIDATES_PER_LABEL:
            break

        try:
            rising = await sc.get_rising_artists(
                genre=genre,
                limit=50,
                platform="spotify",
                metric_type="followers",
                sort_by="percent",
                period="month",
            )
        except Exception as e:
            logger.error(f"Soundcharts get_rising_artists failed for genre '{genre}': {e}")
            if sc._is_circuit_open():
                logger.info(f"Circuit breaker open, falling back to legacy discover for {label.name}")
                await discover_for_label(db, label_id)
                return
            continue

        for artist_data in rising:
            if discovered >= MAX_CANDIDATES_PER_LABEL:
                break

            name = artist_data.get("name", "")
            sc_uuid = artist_data.get("sc_uuid", "")
            if not name or not sc_uuid:
                continue
            if is_likely_slop(name):
                continue

            # Skip if we already have this Soundcharts UUID
            existing = await db.execute(
                select(PlatformAccount).where(
                    PlatformAccount.platform == "soundcharts",
                    PlatformAccount.platform_id == sc_uuid,
                )
            )
            if existing.scalar_one_or_none():
                continue

            # Create artist
            artist = Artist(
                id=new_uuid(),
                name=name,
                image_url=artist_data.get("image_url"),
                genre_tags=artist_data.get("genres") or [],
                is_candidate=True,
            )
            db.add(artist)
            await db.flush()

            # Create Soundcharts platform account
            sc_account = PlatformAccount(
                id=new_uuid(),
                artist_id=artist.id,
                platform="soundcharts",
                platform_id=sc_uuid,
                platform_url=f"https://app.soundcharts.com/app/artist/{artist_data.get('slug') or sc_uuid}",
            )
            db.add(sc_account)

            # Resolve cross-platform IDs via single identifiers call
            try:
                ids = await sc.get_artist_identifiers(sc_uuid)
            except Exception:
                ids = {}

            spotify_id = ids.get("spotify")
            if spotify_id:
                sp_existing = await db.execute(
                    select(PlatformAccount).where(
                        PlatformAccount.platform == "spotify",
                        PlatformAccount.platform_id == spotify_id,
                    )
                )
                if not sp_existing.scalar_one_or_none():
                    sp_account = PlatformAccount(
                        id=new_uuid(),
                        artist_id=artist.id,
                        platform="spotify",
                        platform_id=spotify_id,
                        platform_url=f"https://open.spotify.com/artist/{spotify_id}",
                    )
                    db.add(sp_account)

            yt_id = ids.get("youtube")
            if yt_id:
                yt_existing = await db.execute(
                    select(PlatformAccount).where(
                        PlatformAccount.platform == "youtube",
                        PlatformAccount.platform_id == yt_id,
                    )
                )
                if not yt_existing.scalar_one_or_none():
                    yt_account = PlatformAccount(
                        id=new_uuid(),
                        artist_id=artist.id,
                        platform="youtube",
                        platform_id=yt_id,
                        platform_url=f"https://youtube.com/channel/{yt_id}",
                    )
                    db.add(yt_account)

            discovered += 1

    await db.flush()
    logger.info(f"Discovered {discovered} Soundcharts candidates for label {label.name}")

    if discovered == 0:
        logger.warning(f"No SC candidates for {label.name}, trying legacy discover as fallback")
        await discover_for_label(db, label_id)


async def run():
    logger.info("Starting Soundcharts candidate discovery...")
    async with async_session_factory() as db:
        result = await db.execute(select(Label.id))
        label_ids = [r[0] for r in result.all()]
        for lid in label_ids:
            try:
                await pull_for_label(db, lid)
            except Exception as e:
                logger.error(f"SC discovery failed for label {lid}: {e}")

        # Cross-reference all artists that have Spotify but no Soundcharts account
        sc = SoundchartsConnector()
        await _crossref_with_soundcharts(db, sc)

        await db.commit()
    logger.info("Soundcharts candidate discovery complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
