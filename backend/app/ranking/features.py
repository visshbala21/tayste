import numpy as np
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tables import Snapshot, ArtistFeature, Artist
from app.models.base import new_uuid


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

    # Momentum: weighted combination
    momentum_score = (
        0.3 * min(growth_7d, 2.0) / 2.0 +
        0.3 * min(growth_30d, 5.0) / 5.0 +
        0.2 * min(max(acceleration, 0), 1.0) +
        0.2 * min(engagement_rate * 100, 1.0)
    )
    momentum_score = max(0.0, min(1.0, momentum_score))

    feature = ArtistFeature(
        id=new_uuid(), artist_id=artist_id, computed_at=now,
        growth_7d=growth_7d, growth_30d=growth_30d,
        acceleration=acceleration, engagement_rate=engagement_rate,
        momentum_score=momentum_score, risk_score=risk_score,
        risk_flags=risk_flags,
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
