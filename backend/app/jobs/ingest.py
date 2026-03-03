"""Ingestion job: pull latest metrics and build embeddings."""
import asyncio
import logging
from datetime import datetime
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.tables import Artist, PlatformAccount, Snapshot
from app.models.base import new_uuid
from app.connectors.spotify import SpotifyConnector
from app.services.embeddings import build_metric_vector, store_embedding

logger = logging.getLogger(__name__)


async def ingest_artist(db, artist_id: str):
    """Rebuild artist embedding from all available snapshots.

    YouTube metrics are sourced from Soundcharts enrichment, not direct YouTube API calls.
    """
    result = await db.execute(
        select(Snapshot).where(Snapshot.artist_id == artist_id)
        .order_by(Snapshot.captured_at.asc())
    )
    snapshots = result.scalars().all()
    if not snapshots:
        return
    snap_dicts = [
        {
            "followers": s.followers, "views": s.views, "likes": s.likes,
            "comments": s.comments, "engagement_rate": s.engagement_rate,
        }
        for s in snapshots
    ]
    vec = build_metric_vector(snap_dicts)
    if vec is not None:
        await store_embedding(db, artist_id, vec)


async def run():
    logger.info("Starting ingestion job...")
    async with async_session_factory() as db:
        # Batch ingest Spotify accounts to minimize API calls
        spotify = SpotifyConnector()
        if spotify.available:
            result = await db.execute(
                select(PlatformAccount).where(PlatformAccount.platform == "spotify")
            )
            spotify_accounts = result.scalars().all()
            spotify_ids = [a.platform_id for a in spotify_accounts if a.platform_id]
            try:
                stats_map = await spotify.get_artist_stats_bulk(list(dict.fromkeys(spotify_ids)))
            except Exception as e:
                logger.warning(f"Spotify ingest skipped: {e}")
                stats_map = {}
            for account in spotify_accounts:
                stats = stats_map.get(account.platform_id)
                if not stats:
                    continue
                snapshot = Snapshot(
                    id=new_uuid(),
                    artist_id=account.artist_id,
                    platform="spotify",
                    captured_at=datetime.utcnow(),
                    followers=stats.get("followers") or 0,
                    views=stats.get("popularity") or 0,
                )
                snapshot.extra_metrics = {
                    "popularity": stats.get("popularity"),
                    "genres": stats.get("genres"),
                }
                db.add(snapshot)
            await db.flush()

        result = await db.execute(select(Artist.id))
        artist_ids = [r[0] for r in result.all()]
        logger.info(f"Ingesting {len(artist_ids)} artists")
        for aid in artist_ids:
            try:
                await ingest_artist(db, aid)
            except Exception as e:
                logger.error(f"Failed to ingest artist {aid}: {e}")
        await db.commit()
    logger.info("Ingestion complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
