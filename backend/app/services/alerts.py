import logging
from datetime import datetime, timedelta
from typing import Iterable

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tables import Alert, AlertRule, ArtistFeature, Recommendation
from app.models.base import new_uuid

logger = logging.getLogger(__name__)

DEFAULT_RULES = [
    {
        "name": "Momentum Surge",
        "severity": "high",
        "criteria": {"momentum_min": 0.7, "growth_7d_min": 0.2},
    },
    {
        "name": "Sustained Growth",
        "severity": "medium",
        "criteria": {"sustained_ratio_min": 0.7, "growth_30d_min": 0.3},
    },
    {
        "name": "Risk Spike",
        "severity": "high",
        "criteria": {"type": "risk_spike", "risk_min": 0.6},
    },
]


async def ensure_default_rules(db: AsyncSession, label_id: str) -> list[AlertRule]:
    result = await db.execute(
        select(AlertRule).where(AlertRule.label_id == label_id)
    )
    existing = result.scalars().all()
    if existing:
        return existing

    created: list[AlertRule] = []
    for rule in DEFAULT_RULES:
        alert_rule = AlertRule(
            id=new_uuid(),
            label_id=label_id,
            name=rule["name"],
            severity=rule["severity"],
            is_active=True,
            criteria=rule["criteria"],
        )
        db.add(alert_rule)
        created.append(alert_rule)
    await db.flush()
    return created


def _match_rule(rule: AlertRule, rec: Recommendation, features: ArtistFeature | None) -> bool:
    criteria = rule.criteria or {}
    if criteria.get("type") == "risk_spike":
        if rec.risk_score >= float(criteria.get("risk_min", 0.6)):
            return True
        if features and features.risk_flags:
            if "high_volatility_30d" in features.risk_flags or "spiky_growth_30d" in features.risk_flags:
                return True
        return False

    momentum_min = criteria.get("momentum_min")
    growth_7d_min = criteria.get("growth_7d_min")
    growth_30d_min = criteria.get("growth_30d_min")
    sustained_ratio_min = criteria.get("sustained_ratio_min")

    if momentum_min is not None and rec.momentum_score < float(momentum_min):
        return False
    if growth_7d_min is not None and (not features or (features.growth_7d or 0) < float(growth_7d_min)):
        return False
    if growth_30d_min is not None and (not features or (features.growth_30d or 0) < float(growth_30d_min)):
        return False
    if sustained_ratio_min is not None:
        sustained = None
        if features and features.extra:
            sustained = features.extra.get("sustained_ratio_30d")
        if sustained is None or sustained < float(sustained_ratio_min):
            return False

    return True


def _build_alert_text(rule: AlertRule, rec: Recommendation, features: ArtistFeature | None) -> tuple[str, str]:
    title = rule.name
    parts = []
    if features:
        if features.growth_7d is not None:
            parts.append(f"7d growth {features.growth_7d:+.0%}")
        if features.growth_30d is not None:
            parts.append(f"30d growth {features.growth_30d:+.0%}")
        if features.momentum_score is not None:
            parts.append(f"momentum {(features.momentum_score or 0):.2f}")
        if features.extra:
            sustained = features.extra.get("sustained_ratio_30d")
            if sustained is not None:
                parts.append(f"sustained {(sustained or 0):.0%}")
    parts.append(f"fit {(rec.fit_score or 0):.2f}")
    desc = ", ".join(parts) if parts else "Triggered by scoring rule."
    return title, desc


async def generate_alerts_for_label(
    db: AsyncSession,
    label_id: str,
    recs: Iterable[Recommendation],
    lookback_days: int = 7,
    limit: int = 50,
) -> int:
    rules = await ensure_default_rules(db, label_id)
    rules = [r for r in rules if r.is_active]
    if not rules:
        return 0

    recs = list(recs)[:limit]
    if not recs:
        return 0

    artist_ids = [r.artist_id for r in recs]
    feat_result = await db.execute(
        select(ArtistFeature).where(ArtistFeature.artist_id.in_(artist_ids))
        .order_by(ArtistFeature.computed_at.desc())
    )
    features_map: dict[str, ArtistFeature] = {}
    for feat in feat_result.scalars().all():
        if feat.artist_id not in features_map:
            features_map[feat.artist_id] = feat

    now = datetime.utcnow()
    created = 0
    cutoff = now - timedelta(days=lookback_days)

    for rec in recs:
        feat = features_map.get(rec.artist_id)
        for rule in rules:
            if not _match_rule(rule, rec, feat):
                continue
            existing = await db.execute(
                select(Alert.id).where(
                    and_(
                        Alert.label_id == label_id,
                        Alert.artist_id == rec.artist_id,
                        Alert.rule_id == rule.id,
                        Alert.created_at >= cutoff,
                    )
                )
            )
            if existing.scalar_one_or_none():
                continue
            title, description = _build_alert_text(rule, rec, feat)
            alert = Alert(
                id=new_uuid(),
                label_id=label_id,
                artist_id=rec.artist_id,
                rule_id=rule.id,
                severity=rule.severity or "medium",
                status="new",
                title=title,
                description=description,
                context={
                    "fit": rec.fit_score,
                    "momentum": rec.momentum_score,
                    "risk": rec.risk_score,
                    "features": feat.extra if feat else None,
                },
            )
            db.add(alert)
            created += 1

    return created
