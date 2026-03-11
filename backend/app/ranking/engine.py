import numpy as np
from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tables import (
    LabelCluster, Embedding, ArtistFeature, Recommendation,
    Artist, RosterMembership, PlatformAccount, LabelArtistState,
    ArtistCulturalProfile, LabelCandidate,
)
from app.models.base import new_uuid
from app.services.embeddings import cosine_similarity
from app.models.tables import Label
from app.services.emerging import EmergingDecision, EmergingSignals, evaluate_emerging_artist


@dataclass(frozen=True)
class RankingPolicy:
    name: str
    fit_weight: float
    momentum_weight: float
    scale_weight: float
    risk_weight: float
    cultural_weight: float
    min_growth_7d: float
    min_growth_30d: float
    min_momentum: float
    max_risk: float
    allow_without_features: bool
    allow_low_momentum: bool
    min_results: int


def _policy_for_roster_size(roster_size: int) -> RankingPolicy:
    # Smaller labels generally need emerging upside; larger labels need broader strategic fit.
    if roster_size <= 15:
        return RankingPolicy(
            name="focused_emerging",
            fit_weight=0.45,
            momentum_weight=0.45,
            scale_weight=0.10,
            risk_weight=0.35,
            cultural_weight=0.30,
            min_growth_7d=0.01,
            min_growth_30d=0.04,
            min_momentum=0.18,
            max_risk=0.70,
            allow_without_features=False,
            allow_low_momentum=False,
            min_results=20,
        )
    if roster_size <= 50:
        return RankingPolicy(
            name="balanced_growth",
            fit_weight=0.55,
            momentum_weight=0.30,
            scale_weight=0.15,
            risk_weight=0.30,
            cultural_weight=0.20,
            min_growth_7d=0.005,
            min_growth_30d=0.02,
            min_momentum=0.10,
            max_risk=0.75,
            allow_without_features=False,
            allow_low_momentum=True,
            min_results=35,
        )
    return RankingPolicy(
        name="strategic_scale",
        fit_weight=0.65,
        momentum_weight=0.15,
        scale_weight=0.20,
        risk_weight=0.25,
        cultural_weight=0.10,
        min_growth_7d=0.0,
        min_growth_30d=0.0,
        min_momentum=0.0,
        max_risk=0.80,
        allow_without_features=False,
        allow_low_momentum=True,
        min_results=60,
    )


def _passes_quality_gate(features: ArtistFeature | None, policy: RankingPolicy) -> bool:
    if not features:
        return policy.allow_without_features

    risk = features.risk_score or 0.0
    if risk > policy.max_risk:
        return False

    growth_7d = features.growth_7d or 0.0
    growth_30d = features.growth_30d or 0.0
    momentum = features.momentum_score or 0.0

    if growth_7d >= policy.min_growth_7d:
        return True
    if growth_30d >= policy.min_growth_30d:
        return True
    if momentum >= policy.min_momentum:
        return True
    return policy.allow_low_momentum and risk <= 0.15


def _scale_score(features: ArtistFeature | None) -> float:
    if not features or not features.extra:
        return 0.0
    followers = float(
        features.extra.get("latest_followers")
        or features.extra.get("max_followers")
        or 0
    )
    popularity = float(features.extra.get("spotify_popularity") or 0)
    follower_score = min(np.log10(max(followers, 1)) / 8.0, 1.0)
    popularity_score = min(max(popularity, 0.0) / 100.0, 1.0)
    return float(max(0.0, min(1.0, 0.7 * follower_score + 0.3 * popularity_score)))


def _to_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalized_cosine(sim: float) -> float:
    """Map cosine similarity [-1, 1] to [0, 1]."""
    return max(0.0, min(1.0, (float(sim) + 1.0) / 2.0))


def _passes_soft_backfill_gate(
    features: ArtistFeature | None,
    fit_score: float,
    risk: float,
    policy: RankingPolicy,
) -> bool:
    """Secondary gate when strict emerging evidence is sparse.

    Still requires thematic fit and manageable risk, but allows artists with
    weaker growth evidence as long as they are not mainstream.
    """
    if fit_score < 0.22:
        return False
    if risk > min(0.9, policy.max_risk + 0.15):
        return False
    if features:
        return True
    # If we have no features, only allow strong thematic matches.
    return fit_score >= 0.38


def _max_normalized_similarity(
    artist_vec: np.ndarray,
    reference_vectors: list[np.ndarray],
) -> float:
    if not reference_vectors:
        return 0.0
    best_sim = -1.0
    for reference in reference_vectors:
        sim = cosine_similarity(artist_vec, reference)
        if sim > best_sim:
            best_sim = sim
    return _normalized_cosine(best_sim)


async def rank_candidates(db: AsyncSession, label_id: str, batch_id: str | None = None) -> list[Recommendation]:
    """Score and rank candidate artists for a label."""
    if batch_id is None:
        batch_id = new_uuid()

    # Load label clusters
    result = await db.execute(
        select(LabelCluster).where(LabelCluster.label_id == label_id)
    )
    clusters = result.scalars().all()
    if not clusters:
        return []

    # Load roster artist IDs for nearest match
    result = await db.execute(
        select(RosterMembership.artist_id).where(
            RosterMembership.label_id == label_id
        )
    )
    roster_ids = set(r[0] for r in result.all())
    result = await db.execute(select(RosterMembership.artist_id).distinct())
    globally_rostered_ids = {r[0] for r in result.all()}

    # Determine discovery mode from label
    label = await db.get(Label, label_id)
    discovery_mode = getattr(label, "discovery_mode", "emerging") or "emerging" if label else "emerging"
    open_mode = discovery_mode == "open"

    if open_mode:
        policy = RankingPolicy(
            name="open_discovery",
            fit_weight=0.55,
            momentum_weight=0.25,
            scale_weight=0.20,
            risk_weight=0.25,
            cultural_weight=0.20,
            min_growth_7d=0.0,
            min_growth_30d=0.0,
            min_momentum=0.0,
            max_risk=0.85,
            allow_without_features=True,
            allow_low_momentum=True,
            min_results=40,
        )
    else:
        policy = _policy_for_roster_size(len(roster_ids))

    # Load roster embeddings for nearest match
    roster_embeddings = {}
    if roster_ids:
        result = await db.execute(
            select(Embedding).where(
                Embedding.artist_id.in_(roster_ids), Embedding.provider.in_(["metric", "fallback"])
            )
        )
        for emb in result.scalars().all():
            if emb.artist_id not in roster_embeddings or emb.provider == "metric":
                roster_embeddings[emb.artist_id] = np.array(emb.vector)

    # Get candidate artists linked to this label; fall back to all candidates
    # if no label_candidates rows exist yet (backward compat).
    lc_result = await db.execute(
        select(LabelCandidate.artist_id).where(LabelCandidate.label_id == label_id)
    )
    label_candidate_ids = {r[0] for r in lc_result.all()}
    if label_candidate_ids:
        result = await db.execute(
            select(Artist).where(Artist.id.in_(label_candidate_ids))
        )
    else:
        result = await db.execute(
            select(Artist).where(Artist.is_candidate == True)
        )
    candidates = result.scalars().all()
    candidate_ids = [artist.id for artist in candidates]
    if not candidate_ids:
        return []

    # Label feedback/stage state used to learn from A&R actions.
    result = await db.execute(
        select(LabelArtistState.artist_id, LabelArtistState.stage).where(
            LabelArtistState.label_id == label_id
        )
    )
    stage_by_artist: dict[str, str] = {artist_id: stage for artist_id, stage in result.all()}
    positive_feedback_ids = [
        artist_id
        for artist_id, stage in stage_by_artist.items()
        if stage in {"shortlist", "sign"}
    ]
    negative_feedback_ids = [
        artist_id
        for artist_id, stage in stage_by_artist.items()
        if stage in {"pass", "archive"}
    ]

    # Candidate platform metadata (career stage + latest discovery scale hints).
    result = await db.execute(
        select(
            PlatformAccount.artist_id,
            PlatformAccount.platform,
            PlatformAccount.platform_metadata,
        ).where(
            PlatformAccount.artist_id.in_(candidate_ids),
            PlatformAccount.platform.in_(["spotify", "soundcharts"]),
        )
    )
    platform_metadata: dict[str, dict[str, dict]] = {}
    for artist_id, platform, metadata in result.all():
        platform_metadata.setdefault(artist_id, {})[platform] = metadata or {}

    # Preload candidate embeddings, preferring metric vectors.
    result = await db.execute(
        select(Embedding).where(
            Embedding.artist_id.in_(candidate_ids),
            Embedding.provider.in_(["metric", "fallback"]),
        )
    )
    candidate_embeddings: dict[str, Embedding] = {}
    for emb in result.scalars().all():
        if emb.artist_id not in candidate_embeddings or emb.provider == "metric":
            candidate_embeddings[emb.artist_id] = emb

    # Build feedback reference vectors (learn taste from explicit A&R decisions).
    feedback_reference_ids = list(set(positive_feedback_ids + negative_feedback_ids))
    positive_feedback_vectors: list[np.ndarray] = []
    negative_feedback_vectors: list[np.ndarray] = []
    if feedback_reference_ids:
        result = await db.execute(
            select(Embedding).where(
                Embedding.artist_id.in_(feedback_reference_ids),
                Embedding.provider.in_(["metric", "fallback"]),
            )
        )
        feedback_embeddings: dict[str, Embedding] = {}
        for emb in result.scalars().all():
            if emb.artist_id not in feedback_embeddings or emb.provider == "metric":
                feedback_embeddings[emb.artist_id] = emb
        positive_feedback_vectors = [
            np.array(feedback_embeddings[artist_id].vector)
            for artist_id in positive_feedback_ids
            if artist_id in feedback_embeddings
        ]
        negative_feedback_vectors = [
            np.array(feedback_embeddings[artist_id].vector)
            for artist_id in negative_feedback_ids
            if artist_id in feedback_embeddings
        ]

    # Preload latest features for candidates.
    result = await db.execute(
        select(ArtistFeature).where(ArtistFeature.artist_id.in_(candidate_ids))
        .order_by(ArtistFeature.computed_at.desc())
    )
    latest_features: dict[str, ArtistFeature] = {}
    for feat in result.scalars().all():
        if feat.artist_id not in latest_features:
            latest_features[feat.artist_id] = feat

    # Preload latest cultural profiles for candidates.
    result = await db.execute(
        select(ArtistCulturalProfile).where(
            ArtistCulturalProfile.artist_id.in_(candidate_ids)
        ).order_by(ArtistCulturalProfile.computed_at.desc())
    )
    cultural_profiles: dict[str, ArtistCulturalProfile] = {}
    for cp in result.scalars().all():
        if cp.artist_id not in cultural_profiles:
            cultural_profiles[cp.artist_id] = cp

    cluster_centroids = [(cluster.id, np.array(cluster.centroid)) for cluster in clusters]
    qualified_payloads: list[dict] = []
    fallback_payloads: list[dict] = []
    soft_backfill_payloads: list[dict] = []

    for artist in candidates:
        if artist.id in globally_rostered_ids:
            continue
        stage = stage_by_artist.get(artist.id)
        # Already decided artists shouldn't keep resurfacing in ranked output.
        if stage in {"pass", "archive", "sign"}:
            continue

        emb = candidate_embeddings.get(artist.id)
        if not emb:
            continue
        artist_vec = np.array(emb.vector)

        # Compute fit from both centroid and nearest roster signals.
        best_cluster_sim = -1.0
        nearest_cluster_id = None
        for cluster_id, centroid in cluster_centroids:
            sim = cosine_similarity(artist_vec, centroid)
            if sim > best_cluster_sim:
                best_cluster_sim = sim
                nearest_cluster_id = cluster_id

        nearest_roster_id = None
        best_roster_sim = -1.0
        roster_similarities: dict[str, float] = {}
        for rid, rvec in roster_embeddings.items():
            sim = cosine_similarity(artist_vec, rvec)
            roster_similarities[rid] = round(_normalized_cosine(sim), 4)
            if sim > best_roster_sim:
                best_roster_sim = sim
                nearest_roster_id = rid

        fit_score = max(
            _normalized_cosine(best_cluster_sim),
            _normalized_cosine(best_roster_sim),
        )
        # Hard floor: avoid low/zero-theme matches in feed.
        if fit_score < 0.12:
            continue

        features = latest_features.get(artist.id)
        artist_platform_meta = platform_metadata.get(artist.id, {})
        spotify_meta = artist_platform_meta.get("spotify", {})
        soundcharts_meta = artist_platform_meta.get("soundcharts", {})
        feature_extra = features.extra if features and features.extra else {}
        spotify_followers = (
            _to_int(spotify_meta.get("followers"))
            or _to_int(feature_extra.get("latest_followers"))
            or _to_int(feature_extra.get("max_followers"))
        )
        spotify_popularity = (
            _to_int(spotify_meta.get("popularity"))
            or _to_int(feature_extra.get("spotify_popularity"))
        )
        total_followers = spotify_followers or _to_int(feature_extra.get("max_followers"))
        if open_mode:
            emerging = EmergingDecision(is_emerging=True, reasons=("open_mode",))
            emerging_gate = "open"
        else:
            strict_emerging = evaluate_emerging_artist(
                EmergingSignals(
                    name=artist.name,
                    bio=artist.bio,
                    career_stage=soundcharts_meta.get("career_stage"),
                    spotify_followers=spotify_followers,
                    spotify_popularity=spotify_popularity,
                    total_followers=total_followers,
                    growth_7d=features.growth_7d if features else None,
                    growth_30d=features.growth_30d if features else None,
                    momentum_score=features.momentum_score if features else None,
                ),
                strict=True,
            )
            soft_emerging = strict_emerging
            emerging_gate = "strict"
            if not strict_emerging.is_emerging:
                soft_emerging = evaluate_emerging_artist(
                    EmergingSignals(
                        name=artist.name,
                        bio=artist.bio,
                        career_stage=soundcharts_meta.get("career_stage"),
                        spotify_followers=spotify_followers,
                        spotify_popularity=spotify_popularity,
                        total_followers=total_followers,
                        growth_7d=features.growth_7d if features else None,
                        growth_30d=features.growth_30d if features else None,
                        momentum_score=features.momentum_score if features else None,
                    ),
                    strict=False,
                )
                if not soft_emerging.is_emerging:
                    continue
                emerging_gate = "soft"

            emerging = strict_emerging if emerging_gate == "strict" else soft_emerging
            if not emerging.is_emerging:
                continue

        fallback_metrics = False
        if features:
            momentum = features.momentum_score if features else 0.0
            risk = features.risk_score if features else 0.0
        else:
            momentum = 0.12
            risk = 0.18
            fallback_metrics = True
        momentum = max(0.0, min(1.0, float(momentum or 0.0)))
        risk = max(0.0, min(1.0, float(risk or 0.0)))
        scale = _scale_score(features)

        # Cultural energy integration
        cp = cultural_profiles.get(artist.id)
        cultural_energy = float(cp.cultural_energy or 0.0) if cp else 0.0
        breakout_boost = 0.10 if (cp and cp.breakout_candidate) else 0.0

        weighted_sum = (
            fit_score * policy.fit_weight
            + momentum * policy.momentum_weight
            + scale * policy.scale_weight
        )
        denom = policy.fit_weight + policy.momentum_weight + policy.scale_weight

        # Only include cultural weight in formula if data exists
        if cultural_energy > 0.0:
            weighted_sum += cultural_energy * policy.cultural_weight
            denom += policy.cultural_weight

        denom = max(denom, 1e-6)
        feedback_positive_similarity = _max_normalized_similarity(artist_vec, positive_feedback_vectors)
        feedback_negative_similarity = _max_normalized_similarity(artist_vec, negative_feedback_vectors)
        feedback_delta = (0.15 * feedback_positive_similarity) - (0.12 * feedback_negative_similarity)
        if stage == "shortlist":
            feedback_delta = max(feedback_delta, 0.18)
        elif stage == "review":
            feedback_delta = max(feedback_delta, 0.08)

        final_score = (weighted_sum / denom) - (risk * policy.risk_weight) + feedback_delta + breakout_boost
        final_score = max(0.0, min(1.0, final_score))

        payload = {
            "artist_id": artist.id,
            "fit_score": round(fit_score, 4),
            "momentum_score": round(momentum, 4),
            "risk_score": round(risk, 4),
            "final_score": round(final_score, 4),
            "nearest_cluster_id": nearest_cluster_id,
            "nearest_roster_artist_id": nearest_roster_id,
            "roster_similarities": roster_similarities,
            "score_breakdown": {
                "fit": round(fit_score, 4),
                "momentum": round(momentum, 4),
                "scale": round(scale, 4),
                "risk": round(risk, 4),
                "policy": policy.name,
                "weights": {
                    "fit": policy.fit_weight,
                    "momentum": policy.momentum_weight,
                    "scale": policy.scale_weight,
                    "risk": policy.risk_weight,
                },
                "cultural_energy": round(cultural_energy, 4),
                "cultural_weight": policy.cultural_weight if cultural_energy > 0 else 0.0,
                "breakout_boost": round(breakout_boost, 4),
                "formula": "((fit*w_fit + momentum*w_mom + scale*w_scale + cultural*w_cultural)/sum_w) - risk*w_risk + breakout",
                "emerging_gate": emerging_gate,
                "emerging_reasons": list(emerging.reasons),
                "label_feedback": {
                    "stage": stage,
                    "positive_similarity": round(feedback_positive_similarity, 4),
                    "negative_similarity": round(feedback_negative_similarity, 4),
                    "delta": round(feedback_delta, 4),
                },
            },
        }
        if fallback_metrics:
            payload["score_breakdown"]["fallback"] = True
            payload["score_breakdown"]["note"] = "No recent features; using strict conservative defaults"

        if stage == "shortlist":
            payload["score_breakdown"]["note"] = "Forced include: previously shortlisted by label"
            qualified_payloads.append(payload)
        elif emerging_gate == "open":
            qualified_payloads.append(payload)
        elif emerging_gate == "strict" and _passes_quality_gate(features, policy):
            qualified_payloads.append(payload)
        elif emerging_gate == "strict":
            fallback_payloads.append(payload)
        elif _passes_soft_backfill_gate(features, fit_score, risk, policy):
            payload["score_breakdown"]["note"] = (
                "Soft emerging backfill: no hard mainstream signal and strong thematic fit"
            )
            soft_backfill_payloads.append(payload)

    qualified_payloads.sort(key=lambda p: p["final_score"], reverse=True)
    fallback_payloads.sort(key=lambda p: p["final_score"], reverse=True)
    soft_backfill_payloads.sort(key=lambda p: p["final_score"], reverse=True)

    selected_payloads = list(qualified_payloads)
    if len(selected_payloads) < policy.min_results:
        selected_ids = {p["artist_id"] for p in selected_payloads}
        for payload in fallback_payloads:
            if payload["artist_id"] in selected_ids:
                continue
            selected_payloads.append(payload)
            selected_ids.add(payload["artist_id"])
            if len(selected_payloads) >= policy.min_results:
                break
        if len(selected_payloads) < policy.min_results:
            for payload in soft_backfill_payloads:
                if payload["artist_id"] in selected_ids:
                    continue
                selected_payloads.append(payload)
                selected_ids.add(payload["artist_id"])
                if len(selected_payloads) >= policy.min_results:
                    break

    recommendations = []
    for payload in selected_payloads:
        rec = Recommendation(
            id=new_uuid(),
            label_id=label_id,
            artist_id=payload["artist_id"],
            batch_id=batch_id,
            fit_score=payload["fit_score"],
            momentum_score=payload["momentum_score"],
            risk_score=payload["risk_score"],
            final_score=payload["final_score"],
            nearest_cluster_id=payload["nearest_cluster_id"],
            nearest_roster_artist_id=payload["nearest_roster_artist_id"],
            score_breakdown=payload["score_breakdown"],
            roster_similarities=payload.get("roster_similarities") or {},
        )
        db.add(rec)
        recommendations.append(rec)

    await db.flush()
    recommendations.sort(key=lambda r: r.final_score, reverse=True)
    return recommendations
