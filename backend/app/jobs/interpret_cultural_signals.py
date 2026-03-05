"""LLM cultural interpretation job.

Runs post-scoring. For candidate artists with cultural signals, produces rich
interpretation: refined sentiment, themes, persona, evidence snippets.
Updates ArtistCulturalProfile.cultural_profile JSONB.
"""
import asyncio
import logging
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_factory
from app.models.tables import Artist, ArtistCulturalProfile, CulturalSignal, Recommendation
from app.llm.client import llm_client, hash_input
from app.models.base import new_uuid

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a music culture analyst. Given fan comments about an emerging artist,
produce a structured cultural profile. Be specific about cultural themes and fan sentiment.
Handle music slang and irony correctly (e.g. "this is illegal 😭🔥" = very positive, "bro snapped" = positive).
Respond with ONLY valid JSON."""


class CulturalTheme(BaseModel):
    label: str
    confidence: float
    evidence_count: int
    sample_evidence: str


class CulturalInterpretationOutput(BaseModel):
    sentiment_distribution: dict
    themes: List[CulturalTheme]
    persona_summary: str
    interaction_style: str
    fan_community_description: str
    evidence_snippets: List[dict]


async def interpret_artist_cultural_signals(
    db: AsyncSession, artist_id: str
) -> Optional[CulturalInterpretationOutput]:
    """Generate LLM cultural interpretation for an artist."""
    # Get the latest cultural profile
    result = await db.execute(
        select(ArtistCulturalProfile).where(
            ArtistCulturalProfile.artist_id == artist_id
        ).order_by(ArtistCulturalProfile.computed_at.desc()).limit(1)
    )
    profile = result.scalars().first()
    if not profile:
        return None

    # Skip if already interpreted
    if profile.cultural_profile and profile.cultural_profile.get("themes"):
        return None

    # Get artist info
    artist = await db.get(Artist, artist_id)
    if not artist:
        return None

    # Gather sampled comments from recent signals
    result = await db.execute(
        select(CulturalSignal).where(
            CulturalSignal.artist_id == artist_id
        ).order_by(CulturalSignal.captured_at.desc())
    )
    signals = result.scalars().all()

    all_comments = []
    platforms = set()
    for s in signals:
        if s.sampled_comments:
            for comment in s.sampled_comments:
                if isinstance(comment, str) and comment.strip():
                    all_comments.append({"text": comment, "platform": s.platform})
                    platforms.add(s.platform)

    if len(all_comments) < 5:
        return None

    # Truncate to ~3000 tokens worth (~50 comments)
    sampled = all_comments[:50]
    comments_text = "\n".join(
        f"[{c['platform']}] {c['text'][:200]}" for c in sampled
    )

    # Check cache
    cache_data = {"artist_id": artist_id, "comment_count": len(sampled), "platforms": sorted(platforms)}
    cache_hash = hash_input(cache_data)

    user_prompt = f"""Analyze these fan comments about the artist "{artist.name}" ({', '.join(artist.genre_tags or [])}):

{comments_text}

Produce a cultural profile as JSON:
{{
  "sentiment_distribution": {{"very_positive": 0.0, "positive": 0.0, "neutral": 0.0, "critical": 0.0, "negative": 0.0}},
  "themes": [
    {{"label": "theme name", "confidence": 0.0-1.0, "evidence_count": N, "sample_evidence": "a short quote supporting this theme"}}
  ],
  "persona_summary": "1-2 sentence summary of the artist's public persona and engagement style",
  "interaction_style": "How the artist engages with fans (if visible from comments)",
  "fan_community_description": "1-2 sentence summary of the fan community character",
  "evidence_snippets": [
    {{"text": "short fan comment", "platform": "youtube", "sentiment": "very_positive/positive/neutral/critical/negative"}}
  ]
}}

Important:
- Extract 2-5 cultural themes (e.g. "underground rage", "anime aesthetic", "diaspora pride")
- Select 3-6 evidence snippets that best represent the cultural conversation
- Handle slang correctly: "goes crazy", "bro snapped", "this is illegal" = positive/very_positive
- "mid", "fell off" = negative/critical"""

    fallback = CulturalInterpretationOutput(
        sentiment_distribution=profile.sentiment_distribution or {},
        themes=[],
        persona_summary=f"{artist.name} is an emerging artist generating fan discussion.",
        interaction_style="Unknown from available data.",
        fan_community_description="Active fan base across social platforms.",
        evidence_snippets=[sampled[0]] if sampled else [],
    )

    interpretation = llm_client.generate_safe(
        SYSTEM_PROMPT, user_prompt, CulturalInterpretationOutput, fallback=fallback
    )

    if interpretation:
        # Build full cultural_profile JSONB
        profile_data = {
            "version": "1.0",
            "computed_at": profile.computed_at.isoformat() if profile.computed_at else None,
            "sentiment": {
                "distribution": interpretation.sentiment_distribution,
                "dominant": max(interpretation.sentiment_distribution, key=interpretation.sentiment_distribution.get) if interpretation.sentiment_distribution else "neutral",
                "strength": profile.sentiment_strength,
            },
            "engagement": {
                "density_normalized": profile.engagement_density,
                "platforms_sampled": sorted(platforms),
            },
            "superfans": {
                "density_normalized": profile.superfan_density,
            },
            "cross_platform": {
                "platforms_with_mentions": sorted(platforms),
                "platform_count": len(platforms),
                "normalized": profile.cross_platform_presence,
            },
            "cultural_identity": {
                "themes": [t.model_dump() for t in interpretation.themes],
                "thematic_clarity": profile.thematic_clarity,
            },
            "persona": {
                "interaction_style": interpretation.interaction_style,
                "summary": interpretation.persona_summary,
            },
            "polarization": {
                "index": profile.polarization_index,
                "description": "",
            },
            "evidence_snippets": interpretation.evidence_snippets[:6],
            "breakout_signals": {
                "is_breakout_candidate": profile.breakout_candidate,
                "reasons": [],
            },
            "fan_community": interpretation.fan_community_description,
            "scores": {
                "cultural_energy": profile.cultural_energy,
                "sub_scores": {
                    "sentiment_strength": profile.sentiment_strength,
                    "engagement_density": profile.engagement_density,
                    "superfan_density": profile.superfan_density,
                    "cross_platform_presence": profile.cross_platform_presence,
                    "thematic_clarity": profile.thematic_clarity,
                    "polarization_index": profile.polarization_index,
                },
            },
        }

        # Add breakout reasons if applicable
        if profile.breakout_candidate:
            reasons = []
            if profile.engagement_density and profile.engagement_density > 0.6:
                reasons.append(f"High engagement density ({profile.engagement_density:.2f})")
            if profile.superfan_density and profile.superfan_density > 0.5:
                reasons.append(f"Strong superfan density ({profile.superfan_density:.2f})")
            if profile.sentiment_strength and profile.sentiment_strength > 0.5:
                reasons.append(f"Dominant positive sentiment ({profile.sentiment_strength:.2f})")
            if len(platforms) >= 2:
                reasons.append(f"Cross-platform discussion ({len(platforms)} platforms)")
            profile_data["breakout_signals"]["reasons"] = reasons

        # Update thematic clarity from LLM themes
        if interpretation.themes:
            high_confidence_themes = [t for t in interpretation.themes if t.confidence > 0.3]
            thematic_clarity = min(len(high_confidence_themes) / 5.0, 1.0)
            profile.thematic_clarity = thematic_clarity
            profile_data["cultural_identity"]["thematic_clarity"] = thematic_clarity

            # Recompute cultural energy with updated thematic clarity
            profile.cultural_energy = (
                0.25 * (profile.sentiment_strength or 0.0)
                + 0.20 * (profile.engagement_density or 0.0)
                + 0.20 * (profile.superfan_density or 0.0)
                + 0.15 * (profile.cross_platform_presence or 0.0)
                + 0.10 * thematic_clarity
                + 0.10 * (profile.polarization_index or 0.0)
            )
            profile_data["scores"]["cultural_energy"] = profile.cultural_energy
            profile_data["scores"]["sub_scores"]["thematic_clarity"] = thematic_clarity

        profile.cultural_profile = profile_data
        await db.flush()

    return interpretation


async def run():
    """Main entry point: interpret cultural signals for top candidates."""
    logger.info("Starting cultural signal interpretation...")

    async with async_session_factory() as db:
        # Get artists with cultural profiles but no LLM interpretation yet
        result = await db.execute(
            select(ArtistCulturalProfile.artist_id).where(
                ArtistCulturalProfile.cultural_profile == None  # noqa: E711
            ).distinct()
        )
        artist_ids = [r[0] for r in result.all()]

        if not artist_ids:
            # Also try profiles where themes are missing
            result = await db.execute(
                select(ArtistCulturalProfile.artist_id).distinct()
            )
            all_ids = [r[0] for r in result.all()]
            artist_ids = []
            for aid in all_ids:
                res = await db.execute(
                    select(ArtistCulturalProfile).where(
                        ArtistCulturalProfile.artist_id == aid
                    ).order_by(ArtistCulturalProfile.computed_at.desc()).limit(1)
                )
                cp = res.scalars().first()
                if cp and (not cp.cultural_profile or not cp.cultural_profile.get("themes")):
                    artist_ids.append(aid)

        logger.info(f"Interpreting cultural signals for {len(artist_ids)} artists")

        interpreted = 0
        for aid in artist_ids:
            try:
                result = await interpret_artist_cultural_signals(db, aid)
                if result:
                    interpreted += 1
            except Exception as e:
                logger.error(f"Cultural interpretation failed for {aid}: {e}")

        await db.commit()
        logger.info(f"Cultural interpretation complete: {interpreted} artists interpreted")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
