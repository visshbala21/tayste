import hashlib
import numpy as np
import re
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional
from app.models.tables import Embedding, LabelCluster, Snapshot, Artist, RosterMembership
from app.models.base import new_uuid
from app.config import get_settings

settings = get_settings()
EMBED_DIM = settings.embedding_dim


def build_metric_vector(snapshots: list[dict]) -> Optional[np.ndarray]:
    """Build a 128-dim embedding from artist metric snapshots.
    Uses latest snapshot values + computed growth features, padded to 128 dims."""
    if not snapshots:
        return None
    latest = snapshots[-1]
    features = [
        float(latest.get("followers", 0)),
        float(latest.get("views", 0)),
        float(latest.get("likes", 0)),
        float(latest.get("comments", 0)),
        float(latest.get("engagement_rate", 0)),
    ]
    # Growth features if we have history
    if len(snapshots) >= 2:
        prev = snapshots[0]
        for key in ["followers", "views", "likes"]:
            curr_val = float(latest.get(key, 0))
            prev_val = float(prev.get(key, 0))
            growth = (curr_val - prev_val) / max(prev_val, 1)
            features.append(growth)
    else:
        features.extend([0.0, 0.0, 0.0])
    # Pad to EMBED_DIM
    vec = np.zeros(EMBED_DIM, dtype=np.float32)
    vec[:len(features)] = features
    return vec


def build_text_vector(text: str) -> np.ndarray:
    vec = np.zeros(EMBED_DIM, dtype=np.float32)
    if not text:
        return vec
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    if not tokens:
        return vec
    for token in tokens:
        h = hashlib.md5(token.encode()).hexdigest()
        idx = int(h[:8], 16) % EMBED_DIM
        sign = 1.0 if int(h[8:10], 16) % 2 == 0 else -1.0
        vec[idx] += sign
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


def build_fallback_vector(name: str, genres: list | None) -> np.ndarray:
    parts = [name or ""]
    if genres:
        parts.extend([str(g) for g in genres])
    return build_text_vector(" ".join(parts))


async def store_embedding(db: AsyncSession, artist_id: str, vector: np.ndarray, provider: str = "metric"):
    """Store or update an artist embedding."""
    existing = await db.execute(
        select(Embedding).where(Embedding.artist_id == artist_id, Embedding.provider == provider)
    )
    existing = existing.scalar_one_or_none()
    if existing:
        existing.vector = vector.tolist()
        existing.updated_at = datetime.utcnow()
    else:
        emb = Embedding(
            id=new_uuid(), artist_id=artist_id, provider=provider,
            vector=vector.tolist(),
        )
        db.add(emb)
    await db.flush()


async def ensure_fallback_embeddings(db: AsyncSession, artist_ids: list[str]):
    if not artist_ids:
        return
    result = await db.execute(
        select(Embedding).where(
            Embedding.artist_id.in_(artist_ids),
            Embedding.provider.in_(["metric", "fallback"]),
        )
    )
    existing = result.scalars().all()
    existing_map: dict[str, set[str]] = {}
    for emb in existing:
        existing_map.setdefault(emb.artist_id, set()).add(emb.provider)

    missing = [aid for aid in artist_ids if "metric" not in existing_map.get(aid, set())
               and "fallback" not in existing_map.get(aid, set())]
    if not missing:
        return

    result = await db.execute(select(Artist).where(Artist.id.in_(missing)))
    artists = result.scalars().all()
    for artist in artists:
        vec = build_fallback_vector(artist.name, artist.genre_tags or [])
        await store_embedding(db, artist.id, vec, provider="fallback")


async def cluster_label_artists(db: AsyncSession, label_id: str, n_clusters: int = 3) -> list[dict]:
    """Cluster a label's roster artists and store centroids."""
    # Get roster artist IDs
    result = await db.execute(
        select(RosterMembership.artist_id).where(
            RosterMembership.label_id == label_id, RosterMembership.is_active == True
        )
    )
    artist_ids = [r[0] for r in result.all()]
    if len(artist_ids) < n_clusters:
        n_clusters = max(1, len(artist_ids))

    # Get embeddings
    result = await db.execute(
        select(Embedding).where(
            Embedding.artist_id.in_(artist_ids), Embedding.provider.in_(["metric", "fallback"])
        )
    )
    embeddings = result.scalars().all()
    if not embeddings:
        return []

    # Prefer metric embeddings; fall back if needed
    emb_map: dict[str, Embedding] = {}
    for emb in embeddings:
        if emb.artist_id not in emb_map or emb.provider == "metric":
            emb_map[emb.artist_id] = emb

    vectors = np.array([e.vector for e in emb_map.values()])
    aid_map = {i: e.artist_id for i, e in enumerate(emb_map.values())}

    # Scale and cluster
    scaler = StandardScaler()
    scaled = scaler.fit_transform(vectors)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(scaled)
    centroids = scaler.inverse_transform(kmeans.cluster_centers_)

    # Clear old clusters
    await db.execute(text("DELETE FROM label_clusters WHERE label_id = :lid"), {"lid": label_id})

    clusters = []
    for ci in range(n_clusters):
        cluster_artist_ids = [aid_map[i] for i in range(len(labels)) if labels[i] == ci]
        cluster = LabelCluster(
            id=new_uuid(), label_id=label_id, cluster_index=ci,
            centroid=centroids[ci].tolist(),
            artist_ids=cluster_artist_ids,
        )
        db.add(cluster)
        clusters.append({
            "cluster_index": ci,
            "centroid": centroids[ci].tolist(),
            "artist_ids": cluster_artist_ids,
        })
    await db.flush()
    return clusters


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
