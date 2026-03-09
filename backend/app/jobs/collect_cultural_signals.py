"""Collect cultural signals: YouTube comments and Genius annotations/comments for candidate artists.

Creates CulturalSignal rows with raw comment data, commenter counts, and rule-based
sentiment classification. Tiered refresh: hot artists daily, stable weekly.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select, func
from app.db.session import async_session_factory
from app.models.tables import Artist, PlatformAccount, ArtistFeature, CulturalSignal
from app.models.base import new_uuid
from app.connectors.youtube import YouTubeConnector
from app.connectors.genius import GeniusConnector
from app.services.sentiment import classify_batch
from app.config import get_settings

logger = logging.getLogger(__name__)

COLLECT_CONCURRENCY = 5


def _is_hot(artist_id: str, features_map: dict, days_since_discovery: int) -> bool:
    if days_since_discovery < 14:
        return True
    feat = features_map.get(artist_id)
    if feat and feat.momentum_score and feat.momentum_score > 0.5:
        return True
    return False


async def _collect_youtube_signals(
    db, yt: YouTubeConnector, artist_id: str, channel_id: str, settings,
) -> int:
    """Collect YouTube comment signals for an artist. Returns count of new signals."""
    videos = await yt.get_recent_videos(channel_id, max_results=settings.cultural_max_videos_per_artist)
    count = 0

    for video in videos:
        video_id = video["video_id"]

        # Check if we already have this signal
        existing = await db.execute(
            select(CulturalSignal.id).where(
                CulturalSignal.artist_id == artist_id,
                CulturalSignal.platform == "youtube",
                CulturalSignal.source_id == video_id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        # Fetch comments (up to 2 pages)
        all_comments = []
        page_token = None
        pages_fetched = 0
        max_pages = settings.cultural_max_comments_per_video // 100

        while pages_fetched < max_pages:
            result = await yt.get_video_comments(video_id, max_results=100, page_token=page_token)
            all_comments.extend(result["comments"])
            page_token = result["next_page_token"]
            pages_fetched += 1
            if not page_token:
                break

        if not all_comments:
            continue

        # Count unique/repeat commenters
        author_counts: dict[str, int] = {}
        for c in all_comments:
            h = c["author_hash"]
            if h:
                author_counts[h] = author_counts.get(h, 0) + 1

        unique = len(author_counts)
        repeat = sum(1 for v in author_counts.values() if v > 1)

        # Sample comments for LLM (up to 50)
        comment_texts = [c["text"] for c in all_comments if c["text"]]
        sampled = comment_texts[:50]

        # Rule-based sentiment
        sentiment = classify_batch(comment_texts)

        total_replies = sum(c["reply_count"] for c in all_comments)
        total_likes = sum(c["like_count"] for c in all_comments)

        signal = CulturalSignal(
            id=new_uuid(),
            artist_id=artist_id,
            platform="youtube",
            source_type="video_comment",
            source_id=video_id,
            captured_at=datetime.utcnow(),
            comment_count=len(all_comments),
            view_count=video.get("views", 0),
            like_count=total_likes,
            reply_count=total_replies,
            unique_commenters=unique,
            repeat_commenters=repeat,
            sampled_comments=sampled,
            rule_sentiment=sentiment,
        )
        db.add(signal)
        count += 1

    return count


async def _collect_genius_signals(
    db, genius: GeniusConnector, artist_id: str, artist_name: str, settings,
) -> int:
    """Collect Genius annotation + comment signals for an artist. Returns count of new signals."""
    songs = await genius.search_artist_songs(artist_name, max_songs=settings.cultural_max_genius_songs)
    count = 0

    for song in songs:
        song_id = song["song_id"]
        source_id = f"genius:{song_id}"

        # Skip already collected
        existing = await db.execute(
            select(CulturalSignal.id).where(
                CulturalSignal.artist_id == artist_id,
                CulturalSignal.platform == "genius",
                CulturalSignal.source_id == source_id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        # Fetch comments
        comments = await genius.get_song_comments(
            song_id, per_page=settings.cultural_max_comments_per_song,
        )

        # Fetch annotations (referents)
        referents = await genius.get_song_referents(song_id, per_page=20)

        # Combine comment texts + annotation texts for sentiment analysis
        all_texts: list[str] = []
        all_texts.extend(c["text"] for c in comments if c["text"])
        all_texts.extend(r["text"] for r in referents if r["text"])

        if not all_texts:
            continue

        # Count unique commenters (from comments only)
        author_counts: dict[str, int] = {}
        for c in comments:
            h = c["author_hash"]
            if h:
                author_counts[h] = author_counts.get(h, 0) + 1

        unique = len(author_counts)
        repeat = sum(1 for v in author_counts.values() if v > 1)

        sampled = all_texts[:50]
        sentiment = classify_batch(all_texts)

        total_votes = sum(c["votes_total"] for c in comments) + sum(r["votes_total"] for r in referents)
        total_replies = sum(c["reply_count"] for c in comments)
        verified_annotations = sum(1 for r in referents if r.get("verified"))

        song_stats = song.get("stats", {})

        signal = CulturalSignal(
            id=new_uuid(),
            artist_id=artist_id,
            platform="genius",
            source_type="song_annotations",
            source_id=source_id,
            captured_at=datetime.utcnow(),
            comment_count=len(comments),
            view_count=song_stats.get("pageviews", 0),
            like_count=total_votes,
            reply_count=total_replies,
            unique_commenters=unique,
            repeat_commenters=repeat,
            sampled_comments=sampled,
            rule_sentiment=sentiment,
            extra={
                "song_title": song["title"],
                "song_url": song["url"],
                "annotation_count": song.get("annotation_count", 0),
                "referents_sampled": len(referents),
                "verified_annotations": verified_annotations,
            },
        )
        db.add(signal)
        count += 1

    return count


async def collect_artist_signals(
    db, yt: YouTubeConnector, genius: GeniusConnector,
    artist_id: str, artist_name: str,
    youtube_channel_id: str | None, is_hot: bool,
):
    """Collect all cultural signals for a single artist."""
    settings = get_settings()
    total = 0

    # Check last collection time
    result = await db.execute(
        select(func.max(CulturalSignal.captured_at)).where(
            CulturalSignal.artist_id == artist_id,
        )
    )
    last_collected = result.scalar()

    if last_collected:
        days_since = (datetime.utcnow() - last_collected).days
        refresh_days = settings.cultural_signal_refresh_days_hot if is_hot else settings.cultural_signal_refresh_days_stable
        if days_since < refresh_days:
            return 0

    # YouTube comments
    if youtube_channel_id and yt.available:
        try:
            yt_count = await _collect_youtube_signals(db, yt, artist_id, youtube_channel_id, settings)
            total += yt_count
        except Exception as e:
            logger.warning(f"YouTube cultural signals failed for {artist_id}: {e}")

    # Genius annotations + comments
    if genius.available:
        try:
            genius_count = await _collect_genius_signals(
                db, genius, artist_id, artist_name, settings,
            )
            total += genius_count
        except Exception as e:
            logger.warning(f"Genius cultural signals failed for {artist_id}: {e}")

    return total


async def run():
    """Main entry point: collect cultural signals for all candidate artists."""
    logger.info("Starting cultural signal collection...")
    settings = get_settings()
    yt = YouTubeConnector()
    genius = GeniusConnector()

    if genius.available:
        logger.info("Genius connector available — will collect annotations + comments")
    else:
        logger.info("Genius access token not configured — skipping Genius signals")

    async with async_session_factory() as db:
        # Get all candidate artists with platform accounts
        result = await db.execute(
            select(Artist, PlatformAccount).join(
                PlatformAccount, Artist.id == PlatformAccount.artist_id
            ).where(
                Artist.is_candidate == True,
            )
        )
        artist_channels: dict[str, str] = {}
        artist_names: dict[str, str] = {}
        for artist, pa in result.all():
            artist_names[artist.id] = artist.name
            if pa.platform == "youtube":
                artist_channels[artist.id] = pa.platform_id

        # Load latest features for hot/stable classification
        features_map = {}
        for artist_id in artist_names:
            result = await db.execute(
                select(ArtistFeature).where(
                    ArtistFeature.artist_id == artist_id
                ).order_by(ArtistFeature.computed_at.desc()).limit(1)
            )
            feat = result.scalars().first()
            if feat:
                features_map[artist_id] = feat

        logger.info(f"Collecting cultural signals for {len(artist_names)} candidate artists")

        sem = asyncio.Semaphore(COLLECT_CONCURRENCY)
        total_signals = 0

        async def _process(aid: str):
            nonlocal total_signals
            async with sem:
                days = 30  # default
                is_hot_flag = _is_hot(aid, features_map, days)
                n = await collect_artist_signals(
                    db, yt, genius, aid, artist_names[aid],
                    artist_channels.get(aid), is_hot_flag,
                )
                total_signals += n

        await asyncio.gather(*[_process(aid) for aid in artist_names])

        await db.commit()
        logger.info(f"Cultural signal collection complete: {total_signals} new signals")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
