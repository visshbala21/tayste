import numpy as np
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tables import (
    LabelCluster, Embedding, ArtistFeature, Recommendation,
    Artist, RosterMembership
)
from app.models.base import new_uuid
from app.services.embeddings import cosine_similarity


async def rank_candidates(db: AsyncSession, label_id: str) -> list[Recommendation]:
    """Score and rank candidate artists for a label."""
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

    # Get candidate artists
    result = await db.execute(
        select(Artist).where(Artist.is_candidate == True)
    )
    candidates = result.scalars().all()

    recommendations = []
    for artist in candidates:
        # Get embedding
        result = await db.execute(
            select(Embedding).where(
                Embedding.artist_id == artist.id, Embedding.provider.in_(["metric", "fallback"])
            )
        )
        emb = None
        for row in result.scalars().all():
            if emb is None or row.provider == "metric":
                emb = row
        if not emb:
            continue
        artist_vec = np.array(emb.vector)

        # Compute fit: max cosine similarity to any cluster centroid
        fit_score = 0.0
        nearest_cluster_id = None
        for cluster in clusters:
            centroid = np.array(cluster.centroid)
            sim = cosine_similarity(artist_vec, centroid)
            if sim > fit_score:
                fit_score = sim
                nearest_cluster_id = cluster.id
        fit_score = max(0.0, min(1.0, fit_score))

        # Get latest features
        result = await db.execute(
            select(ArtistFeature).where(ArtistFeature.artist_id == artist.id)
            .order_by(ArtistFeature.computed_at.desc()).limit(1)
        )
        features = result.scalar_one_or_none()
        fallback_metrics = False
        if features:
            momentum = features.momentum_score if features else 0.0
            risk = features.risk_score if features else 0.0
        else:
            momentum = 0.5
            risk = 0.0
            fallback_metrics = True

        # Find nearest roster artist
        nearest_roster_id = None
        best_roster_sim = -1
        for rid, rvec in roster_embeddings.items():
            sim = cosine_similarity(artist_vec, rvec)
            if sim > best_roster_sim:
                best_roster_sim = sim
                nearest_roster_id = rid

        # Final score
        final_score = fit_score * momentum - risk
        final_score = max(0.0, final_score)

        breakdown = {
            "fit": round(fit_score, 4),
            "momentum": round(momentum, 4),
            "risk": round(risk, 4),
            "formula": "fit * momentum - risk",
        }
        if fallback_metrics:
            breakdown["fallback"] = True
            breakdown["note"] = "No metrics available; using fit-only scoring"

        rec = Recommendation(
            id=new_uuid(), label_id=label_id, artist_id=artist.id,
            batch_id=batch_id,
            fit_score=round(fit_score, 4),
            momentum_score=round(momentum, 4),
            risk_score=round(risk, 4),
            final_score=round(final_score, 4),
            nearest_cluster_id=nearest_cluster_id,
            nearest_roster_artist_id=nearest_roster_id,
            score_breakdown=breakdown
        )
        db.add(rec)
        recommendations.append(rec)

    await db.flush()
    recommendations.sort(key=lambda r: r.final_score, reverse=True)
    return recommendations
