import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.llm.client import llm_client, hash_input
from app.api.schemas import LabelDNAOutput
from app.models.tables import Label, Artist, RosterMembership, LabelCluster

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an A&R intelligence analyst. Given a record label's roster and cluster data,
produce a structured analysis of the label's musical DNA and taste profile.
Respond with ONLY valid JSON matching the requested schema."""


async def generate_label_dna(db: AsyncSession, label_id: str) -> Optional[LabelDNAOutput]:
    """Generate Label DNA analysis using Claude."""
    # Gather label data
    label = await db.get(Label, label_id)
    if not label:
        return None

    # Get roster artists
    result = await db.execute(
        select(Artist).join(RosterMembership).where(
            RosterMembership.label_id == label_id,
            RosterMembership.is_active == True,
        )
    )
    roster_artists = result.scalars().all()

    # Get clusters
    result = await db.execute(
        select(LabelCluster).where(LabelCluster.label_id == label_id)
    )
    clusters = result.scalars().all()

    input_data = {
        "label_name": label.name,
        "label_description": label.description,
        "roster": [{"name": a.name, "genres": a.genre_tags} for a in roster_artists],
        "num_clusters": len(clusters),
        "cluster_sizes": [len(c.artist_ids or []) for c in clusters],
    }

    input_hash = hash_input(input_data)

    # Check if cached in label
    if label.label_dna and label.label_dna.get("_input_hash") == input_hash:
        try:
            return LabelDNAOutput.model_validate({k: v for k, v in label.label_dna.items() if not k.startswith("_")})
        except Exception:
            pass

    user_prompt = f"""Analyze this record label's taste profile:

Label: {label.name}
Description: {label.description or 'N/A'}
Genre tags: {label.genre_tags}

Roster Artists:
{chr(10).join(f"- {a['name']} (genres: {a['genres']})" for a in input_data['roster'])}

Number of taste clusters: {len(clusters)}
Cluster sizes: {input_data['cluster_sizes']}

Respond with JSON:
{{
  "cluster_names": ["name for each cluster based on the artists"],
  "label_thesis_bullets": ["3-5 bullet points describing the label's taste"],
  "search_seed_queries": ["5-10 YouTube search queries to find similar artists"]
}}"""

    fallback = LabelDNAOutput(
        cluster_names=[f"Cluster {i+1}" for i in range(len(clusters))],
        label_thesis_bullets=["Diverse roster spanning multiple genres"],
        search_seed_queries=[f"{label.name} similar artists"],
    )

    result = llm_client.generate_safe(SYSTEM_PROMPT, user_prompt, LabelDNAOutput, fallback=fallback)

    if result:
        dna_dict = result.model_dump()
        dna_dict["_input_hash"] = input_hash
        label.label_dna = dna_dict
        await db.flush()

        # Update cluster names
        if result.cluster_names:
            for i, cluster in enumerate(clusters):
                if i < len(result.cluster_names):
                    cluster.cluster_name = result.cluster_names[i]
            await db.flush()

    return result
