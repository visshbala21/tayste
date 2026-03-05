"""Deterministic cultural feature computation.

Aggregates CulturalSignal data into an ArtistCulturalProfile with:
- sentiment_strength, engagement_density, superfan_density
- cross_platform_presence, thematic_clarity, polarization_index
- composite cultural_energy score
- breakout_candidate flag

All scores are 0.0-1.0. No LLM dependency — fully deterministic from raw signals.
"""
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import CulturalSignal, ArtistCulturalProfile
from app.models.base import new_uuid

logger = logging.getLogger(__name__)

# Normalization ceilings (divide by these, clamp to 1.0)
ENGAGEMENT_DENSITY_CEILING = 0.05  # 5% comment-to-view ratio is very high
SUPERFAN_DENSITY_CEILING = 0.30  # 30% repeat rate is very high
CROSS_PLATFORM_MAX = 4.0  # 4 platforms max


def _clamp(val: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, val))


def _compute_sentiment_strength(distribution: dict[str, float]) -> float:
    """Compute sentiment strength from normalized distribution.

    Maps weighted sentiment to [0, 1] where 0.5 = neutral.
    Formula: (very_positive*1.0 + positive*0.6 - critical*0.4 - negative*1.0) / total
    """
    total = sum(distribution.values())
    if total == 0:
        return 0.0

    raw = (
        distribution.get("very_positive", 0) * 1.0
        + distribution.get("positive", 0) * 0.6
        - distribution.get("critical", 0) * 0.4
        - distribution.get("negative", 0) * 1.0
    ) / total

    # Map from [-1, 1] to [0, 1]
    return _clamp((raw + 1.0) / 2.0)


def _compute_polarization(distribution: dict[str, float]) -> float:
    """Compute polarization as variance of sentiment proportions."""
    total = sum(distribution.values())
    if total == 0:
        return 0.0

    proportions = [v / total for v in distribution.values()]
    mean = sum(proportions) / len(proportions)
    variance = sum((p - mean) ** 2 for p in proportions) / len(proportions)

    # Normalize: max theoretical variance for 5 buckets is ~0.16
    return _clamp(variance / 0.16)


async def compute_cultural_features(
    db: AsyncSession, artist_id: str, scale_score: float = 0.5
) -> Optional[ArtistCulturalProfile]:
    """Compute cultural features for an artist from the last 30 days of signals.

    Args:
        db: Database session
        artist_id: Artist UUID
        scale_score: Current scale score (used for breakout detection)

    Returns:
        ArtistCulturalProfile if signals exist, None otherwise
    """
    cutoff = datetime.utcnow() - timedelta(days=30)

    result = await db.execute(
        select(CulturalSignal).where(
            CulturalSignal.artist_id == artist_id,
            CulturalSignal.captured_at >= cutoff,
        )
    )
    signals = result.scalars().all()

    if not signals:
        return None

    # ── Aggregate metrics ──

    total_comments = sum(s.comment_count or 0 for s in signals)
    total_views = sum(s.view_count or 0 for s in signals)
    total_unique = sum(s.unique_commenters or 0 for s in signals)
    total_repeat = sum(s.repeat_commenters or 0 for s in signals)
    total_replies = sum(s.reply_count or 0 for s in signals)
    platforms = set(s.platform for s in signals)

    # Aggregate sentiment counts
    agg_sentiment = {"very_positive": 0, "positive": 0, "neutral": 0, "critical": 0, "negative": 0}
    for s in signals:
        if s.rule_sentiment:
            for k, v in s.rule_sentiment.items():
                if k in agg_sentiment:
                    agg_sentiment[k] += v

    total_sent = sum(agg_sentiment.values())
    sentiment_dist = {k: v / total_sent if total_sent else 0.0 for k, v in agg_sentiment.items()}

    # ── Sub-scores ──

    engagement_density_raw = total_comments / total_views if total_views > 0 else 0.0
    engagement_density = _clamp(engagement_density_raw / ENGAGEMENT_DENSITY_CEILING)

    superfan_density_raw = total_repeat / total_unique if total_unique > 0 else 0.0
    superfan_density = _clamp(superfan_density_raw / SUPERFAN_DENSITY_CEILING)

    cross_platform = _clamp(len(platforms) / CROSS_PLATFORM_MAX)

    sentiment_strength = _compute_sentiment_strength(agg_sentiment)

    polarization = _compute_polarization(agg_sentiment)

    # thematic_clarity starts at 0, updated after LLM interpretation
    thematic_clarity = 0.0

    # ── Composite ──

    cultural_energy = (
        0.25 * sentiment_strength
        + 0.20 * engagement_density
        + 0.20 * superfan_density
        + 0.15 * cross_platform
        + 0.10 * thematic_clarity
        + 0.10 * polarization
    )

    # ── Breakout detection ──

    breakout = (
        engagement_density > 0.6
        and superfan_density > 0.5
        and sentiment_strength > 0.5
        and len(platforms) >= 2
        and scale_score < 0.3
    )

    # ── Input hash for caching ──

    hash_input = json.dumps({
        "artist_id": artist_id,
        "total_comments": total_comments,
        "total_views": total_views,
        "signal_count": len(signals),
        "platforms": sorted(platforms),
    }, sort_keys=True)
    input_hash = hashlib.sha256(hash_input.encode()).hexdigest()

    # ── Store profile ──

    profile = ArtistCulturalProfile(
        id=new_uuid(),
        artist_id=artist_id,
        computed_at=datetime.utcnow(),
        input_hash=input_hash,
        sentiment_strength=sentiment_strength,
        engagement_density=engagement_density,
        superfan_density=superfan_density,
        cross_platform_presence=cross_platform,
        thematic_clarity=thematic_clarity,
        polarization_index=polarization,
        cultural_energy=cultural_energy,
        breakout_candidate=breakout,
        sentiment_distribution=sentiment_dist,
    )
    db.add(profile)

    return profile
