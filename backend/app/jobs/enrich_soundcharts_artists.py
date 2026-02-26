"""Enrichment job: pull Soundcharts time-series stats for tracked artists.

Creates Snapshot records from Soundcharts daily audience and streaming stats
across spotify, youtube, tiktok, and instagram. Tiered refresh: "hot" artists
daily, "stable" weekly.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func
from app.db.session import async_session_factory
from app.models.tables import Artist, PlatformAccount, Snapshot, ArtistFeature
from app.models.base import new_uuid
from app.connectors.soundcharts import SoundchartsConnector
from app.services.embeddings import build_metric_vector, store_embedding

logger = logging.getLogger(__name__)

SC_PLATFORMS = ["spotify", "youtube"]


def _is_hot(artist_id: str, features_map: dict, days_since_discovery: int) -> bool:
    """Determine if artist should be refreshed daily (hot) or weekly (stable)."""
    if days_since_discovery < 14:
        return True
    feat = features_map.get(artist_id)
    if feat and feat.momentum_score and feat.momentum_score > 0.5:
        return True
    return False


async def enrich_artist(
    db, sc: SoundchartsConnector, artist_id: str, sc_uuid: str, is_hot: bool
):
    """Pull Soundcharts stats and create Snapshots for one artist."""
    now = datetime.utcnow()

    # Determine time range based on existing snapshots
    result = await db.execute(
        select(func.max(Snapshot.captured_at)).where(
            Snapshot.artist_id == artist_id,
            Snapshot.platform.like("soundcharts_%"),
        )
    )
    last_snapshot_time = result.scalar()

    if last_snapshot_time:
        since = last_snapshot_time.date() + timedelta(days=1)
        # For stable artists, only pull weekly
        if not is_hot:
            days_since = (now.date() - last_snapshot_time.date()).days
            if days_since < 7:
                return
    else:
        since = (now - timedelta(days=30)).date()

    until = now.date()
    if since >= until:
        return

    since_str = since.isoformat()
    until_str = until.isoformat()

    for platform in SC_PLATFORMS:
        snapshot_platform = f"soundcharts_{platform}"

        # Pull audience (followers) time-series
        try:
            audience = await sc.get_audience_stats(sc_uuid, platform, since_str, until_str)
        except Exception as e:
            logger.warning(f"SC audience stats failed for {sc_uuid}/{platform}: {e}")
            audience = []

        # Pull streaming (listeners/views) time-series
        try:
            streaming = await sc.get_streaming_stats(sc_uuid, platform, since_str, until_str)
        except Exception as e:
            logger.debug(f"SC streaming stats failed for {sc_uuid}/{platform}: {e}")
            streaming = []

        # Index streaming data by date for merging
        streaming_by_date: dict[str, dict] = {}
        for item in streaming:
            date_str = item.get("date", "")
            if date_str:
                streaming_by_date[date_str[:10]] = item

        # Create snapshots from audience data (primary), merge streaming if available
        for day_data in audience:
            date_str = day_data.get("date", "")
            if not date_str:
                continue

            try:
                captured = datetime.fromisoformat(date_str[:10])
            except (ValueError, TypeError):
                continue

            # Dedup: check (artist_id, platform, date)
            existing = await db.execute(
                select(Snapshot.id).where(
                    Snapshot.artist_id == artist_id,
                    Snapshot.platform == snapshot_platform,
                    func.date(Snapshot.captured_at) == captured.date(),
                )
            )
            if existing.scalar_one_or_none():
                continue

            followers = day_data.get("followerCount") or day_data.get("value")
            views = None
            extra = {}

            # Merge streaming data if available for this date
            stream_data = streaming_by_date.get(date_str[:10])
            if stream_data:
                views = stream_data.get("value")
                if platform == "spotify":
                    extra["monthly_listeners"] = stream_data.get("value")
                elif platform == "youtube":
                    extra["daily_views"] = stream_data.get("value")

            # Collect other audience fields
            like_count = day_data.get("likeCount")
            if like_count is not None:
                extra["like_count"] = like_count
            post_count = day_data.get("postCount")
            if post_count is not None:
                extra["post_count"] = post_count
            view_count = day_data.get("viewCount")
            if view_count is not None:
                extra["view_count"] = view_count

            snapshot = Snapshot(
                id=new_uuid(),
                artist_id=artist_id,
                platform=snapshot_platform,
                captured_at=captured,
                followers=int(followers) if followers is not None else None,
                views=int(views) if views is not None else None,
                extra_metrics=extra if extra else None,
            )
            db.add(snapshot)

    await db.flush()

    # Rebuild metric embedding from all snapshots
    result = await db.execute(
        select(Snapshot).where(Snapshot.artist_id == artist_id)
        .order_by(Snapshot.captured_at.asc())
    )
    snapshots = result.scalars().all()
    snap_dicts = [
        {
            "followers": s.followers,
            "views": s.views,
            "likes": s.likes,
            "comments": s.comments,
            "engagement_rate": s.engagement_rate,
        }
        for s in snapshots
    ]
    vec = build_metric_vector(snap_dicts)
    if vec is not None:
        await store_embedding(db, artist_id, vec)


async def run():
    logger.info("Starting Soundcharts enrichment...")
    sc = SoundchartsConnector()
    if not sc.available:
        logger.info("Soundcharts unavailable, skipping enrichment.")
        return

    async with async_session_factory() as db:
        # Get all artists with Soundcharts accounts
        result = await db.execute(
            select(PlatformAccount.artist_id, PlatformAccount.platform_id).where(
                PlatformAccount.platform == "soundcharts"
            )
        )
        sc_artists = result.all()
        if not sc_artists:
            logger.info("No artists with Soundcharts accounts.")
            return

        # Load latest features for tiered refresh
        artist_ids = [a[0] for a in sc_artists]
        result = await db.execute(
            select(ArtistFeature).where(ArtistFeature.artist_id.in_(artist_ids))
            .order_by(ArtistFeature.computed_at.desc())
        )
        features = result.scalars().all()
        features_map: dict[str, ArtistFeature] = {}
        for f in features:
            if f.artist_id not in features_map:
                features_map[f.artist_id] = f

        # Load artist creation dates for "days since discovery"
        result = await db.execute(
            select(Artist.id, Artist.created_at).where(Artist.id.in_(artist_ids))
        )
        creation_map = {r[0]: r[1] for r in result.all()}
        now = datetime.utcnow()

        logger.info(f"Enriching {len(sc_artists)} artists from Soundcharts")

        for artist_id, sc_uuid in sc_artists:
            created = creation_map.get(artist_id)
            days_since = (now - created).days if created else 0
            is_hot = _is_hot(artist_id, features_map, days_since)

            try:
                await enrich_artist(db, sc, artist_id, sc_uuid, is_hot)
            except Exception as e:
                logger.error(f"SC enrichment failed for artist {artist_id}: {e}")

        await db.commit()
    logger.info("Soundcharts enrichment complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
