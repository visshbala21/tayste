"""Cross-reference Spotify artists with Soundcharts for enrichment.

Soundcharts trending discovery (POST /top/artists) is disabled to avoid
403 noise on Starter tiers. Candidate discovery happens via related-artist
graph (pull_spotify_graph.py).
"""
import asyncio
import logging
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.tables import Label, Artist, PlatformAccount
from app.models.base import new_uuid
from app.connectors.soundcharts import SoundchartsConnector
from app.jobs.discover import is_likely_slop

logger = logging.getLogger(__name__)

MAX_CANDIDATES_PER_LABEL = 100
ALLOWED_CAREER_STAGES = {"emerging", "developing"}
CROSSREF_CONCURRENCY = 10


async def _crossref_with_soundcharts(db, sc: SoundchartsConnector):
    """Cross-reference artists that have Spotify accounts but no Soundcharts account.

    This ensures artists discovered via Spotify graph get Soundcharts UUIDs
    so they can be enriched with time-series data.
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

    # Pre-fetch existing SC platform IDs to avoid per-task DB queries
    result = await db.execute(
        select(PlatformAccount.platform_id).where(
            PlatformAccount.platform == "soundcharts"
        )
    )
    existing_sc_uuids: set[str] = {r[0] for r in result.all()}

    sem = asyncio.Semaphore(CROSSREF_CONCURRENCY)
    linked = 0
    lock = asyncio.Lock()  # Protect linked counter and DB writes

    async def _crossref_one(artist_id: str, spotify_id: str):
        nonlocal linked
        async with sem:
            try:
                sc_artist = await sc.get_artist_by_platform_id("spotify", spotify_id)
            except Exception:
                return
            if not sc_artist or not sc_artist.get("sc_uuid"):
                return

            sc_uuid = sc_artist["sc_uuid"]

            async with lock:
                # Check we don't already have this SC UUID
                if sc_uuid in existing_sc_uuids:
                    return

                # Double-check DB in case another task just inserted
                existing = await db.execute(
                    select(PlatformAccount).where(
                        PlatformAccount.platform == "soundcharts",
                        PlatformAccount.platform_id == sc_uuid,
                    )
                )
                if existing.scalar_one_or_none():
                    existing_sc_uuids.add(sc_uuid)
                    return

                sc_account = PlatformAccount(
                    id=new_uuid(),
                    artist_id=artist_id,
                    platform="soundcharts",
                    platform_id=sc_uuid,
                    platform_url=f"https://app.soundcharts.com/app/artist/{sc_artist.get('slug') or sc_uuid}",
                )
                db.add(sc_account)
                existing_sc_uuids.add(sc_uuid)
                linked += 1

    await asyncio.gather(
        *[_crossref_one(aid, sp_id) for aid, sp_id in unlinked],
        return_exceptions=True,
    )

    await db.flush()
    if linked:
        logger.info(f"Cross-referenced {linked} artists with Soundcharts")


async def run():
    logger.info("Starting Soundcharts cross-referencing...")
    async with async_session_factory() as db:
        # Cross-reference all artists that have Spotify but no Soundcharts account
        sc = SoundchartsConnector()
        await _crossref_with_soundcharts(db, sc)

        await db.commit()
    logger.info("Soundcharts cross-referencing complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
