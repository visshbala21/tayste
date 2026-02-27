import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tables import Snapshot, ArtistFeature, Artist
from app.models.base import new_uuid


def _compute_daily_growth_rates(
    snapshots: list[Snapshot],
    field: str,
    window_days: int = 30,
) -> list[float]:
    if not snapshots:
        return []
    cutoff = datetime.utcnow() - timedelta(days=window_days)
    series = [
        (s.captured_at, getattr(s, field))
        for s in snapshots
        if s.captured_at and s.captured_at >= cutoff and getattr(s, field) is not None
    ]
    if len(series) < 2:
        return []
    rates: list[float] = []
    prev_time, prev_val = series[0]
    for current_time, current_val in series[1:]:
        if prev_val is None or prev_val <= 0 or current_val is None:
            prev_time, prev_val = current_time, current_val
            continue
        days = (current_time - prev_time).total_seconds() / 86400
        if days <= 0:
            prev_time, prev_val = current_time, current_val
            continue
        rate = (current_val - prev_val) / prev_val / days
        rates.append(rate)
        prev_time, prev_val = current_time, current_val
    return rates


async def compute_artist_features(db: AsyncSession, artist_id: str) -> Optional[ArtistFeature]:
    """Compute features for an artist from their snapshots."""
    # Get snapshots ordered by time
    result = await db.execute(
        select(Snapshot).where(Snapshot.artist_id == artist_id)
        .order_by(Snapshot.captured_at.asc())
    )
    snapshots = result.scalars().all()
    if not snapshots:
        return None

    now = datetime.utcnow()
    latest = snapshots[-1]

    # Growth calculations
    def calc_growth(metric: str, days: int) -> float:
        cutoff = now - timedelta(days=days)
        older = [s for s in snapshots if s.captured_at <= cutoff]
        if not older:
            return 0.0
        old_val = getattr(older[-1], metric) or 0
        new_val = getattr(latest, metric) or 0
        if old_val == 0:
            return 0.0
        return (new_val - old_val) / old_val

    growth_7d = calc_growth("followers", 7)
    growth_30d = calc_growth("followers", 30)

    # Acceleration: change in growth rate
    growth_7d_views = calc_growth("views", 7)
    growth_30d_views = calc_growth("views", 30)
    weekly_rate_30d = growth_30d_views / 4.0 if growth_30d_views else 0
    acceleration = growth_7d_views - weekly_rate_30d

    # Engagement rate
    engagement_rate = latest.engagement_rate or 0.0
    if engagement_rate == 0 and latest.views and latest.views > 0:
        total_engagement = (latest.likes or 0) + (latest.comments or 0)
        engagement_rate = total_engagement / latest.views

    # Risk detection
    risk_flags = []
    risk_score = 0.0
    if growth_7d > 5.0:  # 500% growth in 7 days is suspicious
        risk_flags.append("extreme_growth_7d")
        risk_score += 0.4
    if engagement_rate < 0.001 and (latest.followers or 0) > 10000:
        risk_flags.append("low_engagement_high_followers")
        risk_score += 0.3
    if growth_7d > 0 and growth_30d < 0:
        risk_flags.append("inconsistent_growth")
        risk_score += 0.2
    risk_score = min(risk_score, 1.0)

    # Volatility + sustained vs spike (30d)
    rates = _compute_daily_growth_rates(snapshots, "followers", window_days=30)
    if len(rates) < 3:
        rates = _compute_daily_growth_rates(snapshots, "views", window_days=30)

    volatility_30d = float(np.std(rates)) if rates else None
    sustained_ratio_30d = None
    spike_ratio_30d = None
    if rates:
        sustained_ratio_30d = float(sum(1 for r in rates if r > 0) / len(rates))
        median_rate = float(np.median(rates))
        spike_ratio_30d = float(max(rates) / (abs(median_rate) + 1e-6))
        spike_ratio_30d = min(spike_ratio_30d, 50.0)

    if volatility_30d is not None and volatility_30d > 0.15:
        risk_flags.append("high_volatility_30d")
    if spike_ratio_30d is not None and spike_ratio_30d > 4.0:
        risk_flags.append("spiky_growth_30d")

    # Momentum: weighted combination with realistic normalization ranges
    # growth_7d: 20% weekly = top score (viral territory)
    # growth_30d: 50% monthly = top score
    # acceleration: 20% = top score
    # engagement: 5% = top score (excellent organic engagement)
    momentum_score = (
        0.35 * min(max(growth_7d, 0) / 0.20, 1.0) +
        0.25 * min(max(growth_30d, 0) / 0.50, 1.0) +
        0.20 * min(max(acceleration, 0) / 0.20, 1.0) +
        0.20 * min(engagement_rate / 0.05, 1.0)
    )
    momentum_score = max(0.0, min(1.0, momentum_score))

    extra_metrics = {}
    follower_values = [s.followers for s in snapshots if s.followers is not None]
    if follower_values:
        extra_metrics["max_followers"] = int(max(follower_values))
        extra_metrics["latest_followers"] = int(latest.followers) if latest.followers is not None else None
    popularity_values = [
        (s.extra_metrics or {}).get("popularity")
        for s in snapshots
        if (s.extra_metrics or {}).get("popularity") is not None
    ]
    if popularity_values:
        extra_metrics["spotify_popularity"] = float(max(popularity_values))
    if volatility_30d is not None:
        extra_metrics["volatility_30d"] = round(volatility_30d, 4)
    if sustained_ratio_30d is not None:
        extra_metrics["sustained_ratio_30d"] = round(sustained_ratio_30d, 4)
    if spike_ratio_30d is not None:
        extra_metrics["spike_ratio_30d"] = round(spike_ratio_30d, 4)

    feature = ArtistFeature(
        id=new_uuid(), artist_id=artist_id, computed_at=now,
        growth_7d=growth_7d, growth_30d=growth_30d,
        acceleration=acceleration, engagement_rate=engagement_rate,
        momentum_score=momentum_score, risk_score=risk_score,
        risk_flags=risk_flags,
        extra=extra_metrics or None,
    )
    db.add(feature)
    await db.flush()
    return feature


async def compute_all_candidate_features(db: AsyncSession) -> list[ArtistFeature]:
    """Compute features for all candidate artists."""
    result = await db.execute(
        select(Artist.id).where(Artist.is_candidate == True)
    )
    artist_ids = [r[0] for r in result.all()]
    features = []
    for aid in artist_ids:
        feat = await compute_artist_features(db, aid)
        if feat:
            features.append(feat)
    return features
