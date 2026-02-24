import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.llm.client import llm_client, hash_input
from app.api.schemas import ArtistBriefOutput
from app.models.tables import Artist, ArtistLLMBrief, ArtistFeature, Snapshot, Recommendation
from app.models.base import new_uuid

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an A&R scouting analyst. Given an emerging artist's data,
produce a structured scouting brief for A&R decision makers.
Be specific, concise, and actionable. Respond with ONLY valid JSON."""


async def generate_artist_brief(
    db: AsyncSession, artist_id: str, label_id: Optional[str] = None
) -> Optional[ArtistBriefOutput]:
    """Generate an LLM scouting brief for an artist."""
    artist = await db.get(Artist, artist_id)
    if not artist:
        return None

    # Get latest features
    result = await db.execute(
        select(ArtistFeature).where(ArtistFeature.artist_id == artist_id)
        .order_by(ArtistFeature.computed_at.desc()).limit(1)
    )
    features = result.scalar_one_or_none()

    # Get recent snapshots
    result = await db.execute(
        select(Snapshot).where(Snapshot.artist_id == artist_id)
        .order_by(Snapshot.captured_at.desc()).limit(10)
    )
    snapshots = result.scalars().all()

    # Get recommendation if label context
    rec = None
    if label_id:
        result = await db.execute(
            select(Recommendation).where(
                Recommendation.artist_id == artist_id,
                Recommendation.label_id == label_id,
            ).order_by(Recommendation.created_at.desc()).limit(1)
        )
        rec = result.scalar_one_or_none()

    input_data = {
        "artist_name": artist.name,
        "genres": artist.genre_tags,
        "followers": snapshots[0].followers if snapshots else None,
        "views": snapshots[0].views if snapshots else None,
        "growth_7d": features.growth_7d if features else None,
        "growth_30d": features.growth_30d if features else None,
        "engagement_rate": features.engagement_rate if features else None,
        "risk_flags": features.risk_flags if features else [],
        "fit_score": rec.fit_score if rec else None,
        "momentum_score": features.momentum_score if features else None,
    }

    input_hash = hash_input(input_data)

    # Check cache
    result = await db.execute(
        select(ArtistLLMBrief).where(
            ArtistLLMBrief.artist_id == artist_id,
            ArtistLLMBrief.input_hash == input_hash,
        )
    )
    cached = result.scalar_one_or_none()
    if cached:
        try:
            return ArtistBriefOutput.model_validate(cached.brief)
        except Exception:
            pass

    user_prompt = f"""Produce a scouting brief for this emerging artist:

Artist: {artist.name}
Genres: {artist.genre_tags}
Current Followers: {input_data['followers']}
Total Views: {input_data['views']}
7-day Growth: {input_data['growth_7d']}
30-day Growth: {input_data['growth_30d']}
Engagement Rate: {input_data['engagement_rate']}
Risk Flags: {input_data['risk_flags']}
Fit Score: {input_data['fit_score']}
Momentum Score: {input_data['momentum_score']}

Respond with JSON:
{{
  "what_is_happening": "1-2 sentence summary of the artist's current trajectory",
  "why_fit": "Why this artist fits the label's taste profile",
  "risks_unknowns": "Key risks and unknowns for signing consideration",
  "next_actions": ["2-4 specific next steps for the A&R team"]
}}"""

    fallback = ArtistBriefOutput(
        what_is_happening=f"{artist.name} is an emerging artist with growing metrics.",
        why_fit="Metrics align with label taste profile.",
        risks_unknowns="Limited data history. Further monitoring recommended.",
        next_actions=["Monitor growth for 2 more weeks", "Review content quality manually"],
    )

    result = llm_client.generate_safe(SYSTEM_PROMPT, user_prompt, ArtistBriefOutput, fallback=fallback)

    if result:
        brief = ArtistLLMBrief(
            id=new_uuid(), artist_id=artist_id, label_id=label_id,
            input_hash=input_hash, brief=result.model_dump(),
        )
        db.add(brief)
        await db.flush()

    return result
