"""Ingestion job: pull latest metrics and build embeddings."""
import asyncio
import logging
from datetime import datetime
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.tables import Artist, PlatformAccount, Snapshot
from app.models.base import new_uuid
from app.connectors.youtube import YouTubeConnector
from app.connectors.spotify import SpotifyConnector
from app.connectors.soundcloud import SoundCloudConnector
from app.services.embeddings import build_metric_vector, store_embedding

logger = logging.getLogger(__name__)


async def ingest_artist(db, artist_id: str, skip_platforms: set[str] | None = None):
    """Ingest latest metrics for an artist."""
    result = await db.execute(
        select(PlatformAccount).where(PlatformAccount.artist_id == artist_id)
    )
    accounts = result.scalars().all()
    yt = YouTubeConnector()
    skip_platforms = skip_platforms or set()

    for account in accounts:
        if account.platform in skip_platforms:
            continue
        if account.platform == "youtube":
            stats = await yt.get_channel_stats(account.platform_id)
            if stats:
                snapshot = Snapshot(
                    id=new_uuid(),
                    artist_id=artist_id,
                    platform="youtube",
                    captured_at=stats["captured_at"],
                    followers=stats["followers"],
                    views=stats["views"],
                )
                # Compute basic engagement from recent videos
                videos = await yt.get_recent_videos(account.platform_id, max_results=5)
                if videos:
                    total_views = sum(v["views"] for v in videos)
                    total_engagement = sum(v["likes"] + v["comments"] for v in videos)
                    snapshot.likes = total_engagement
                    if total_views > 0:
                        snapshot.engagement_rate = total_engagement / total_views

                db.add(snapshot)
                logger.info(f"Ingested snapshot for {artist_id} on {account.platform}")

    await db.flush()

    # Build embedding from snapshots
    result = await db.execute(
        select(Snapshot).where(Snapshot.artist_id == artist_id)
        .order_by(Snapshot.captured_at.asc())
    )
    snapshots = result.scalars().all()
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

        # Batch ingest SoundCloud accounts to minimize API calls
        soundcloud = SoundCloudConnector()
        if soundcloud.available:
            result = await db.execute(
                select(PlatformAccount).where(PlatformAccount.platform == "soundcloud")
            )
            soundcloud_accounts = result.scalars().all()
            account_id_to_sc_id: dict[str, str] = {}
            sc_ids: list[str] = []
            for account in soundcloud_accounts:
                meta = account.platform_metadata or {}
                sc_id = meta.get("soundcloud_user_id")
                if not sc_id and account.platform_id and account.platform_id.isdigit():
                    sc_id = account.platform_id
                if not sc_id:
                    handle_or_url = account.platform_url or account.platform_id
                    if handle_or_url:
                        try:
                            resolved = await soundcloud.resolve_user(handle_or_url)
                        except Exception as e:
                            logger.warning(f"SoundCloud resolve failed: {e}")
                            resolved = None
                        if resolved and resolved.get("id"):
                            sc_id = str(resolved.get("id"))
                            meta["soundcloud_user_id"] = sc_id
                            if resolved.get("permalink"):
                                meta["soundcloud_handle"] = resolved.get("permalink")
                            account.platform_metadata = meta
                if sc_id:
                    account_id_to_sc_id[account.id] = sc_id
                    sc_ids.append(sc_id)

            try:
                stats_map = await soundcloud.get_user_stats_bulk(list(dict.fromkeys(sc_ids)))
            except Exception as e:
                logger.warning(f"SoundCloud ingest skipped: {e}")
                stats_map = {}

            for account in soundcloud_accounts:
                sc_id = account_id_to_sc_id.get(account.id)
                if not sc_id:
                    continue
                stats = stats_map.get(sc_id)
                if not stats:
                    continue
                snapshot = Snapshot(
                    id=new_uuid(),
                    artist_id=account.artist_id,
                    platform="soundcloud",
                    captured_at=datetime.utcnow(),
                    followers=stats.get("followers") or 0,
                    views=stats.get("playback_count") or 0,
                )
                snapshot.extra_metrics = {
                    "track_count": stats.get("track_count"),
                    "likes_count": stats.get("likes_count"),
                    "reposts_count": stats.get("reposts_count"),
                    "genre": stats.get("genre"),
                    "tag_list": stats.get("tag_list"),
                }
                db.add(snapshot)
            await db.flush()

        result = await db.execute(select(Artist.id))
        artist_ids = [r[0] for r in result.all()]
        logger.info(f"Ingesting {len(artist_ids)} artists")
        for aid in artist_ids:
            try:
                await ingest_artist(db, aid, skip_platforms={"spotify"})
            except Exception as e:
                logger.error(f"Failed to ingest artist {aid}: {e}")
        await db.commit()
    logger.info("Ingestion complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
