import logging
from typing import Optional, List
from pydantic import BaseModel
from app.llm.client import llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a music discovery assistant.
Given a label's roster and taste profile, suggest emerging artists that could fit.
Return ONLY valid JSON that matches the schema.
The suggestions can be hypothetical if real artists are unknown.
"""


class CandidateSuggestion(BaseModel):
    name: str
    genres: List[str] = []


class CandidateSuggestionOutput(BaseModel):
    candidates: List[CandidateSuggestion]


def generate_candidate_suggestions(
    label_name: str,
    label_description: str | None,
    genre_tags: dict | None,
    roster_names: list[str],
    limit: int = 10,
) -> Optional[CandidateSuggestionOutput]:
    roster_str = "\n".join(f"- {n}" for n in roster_names[:20])
    user_prompt = f"""Label: {label_name}
Description: {label_description or 'N/A'}
Genre tags: {genre_tags or {}}

Roster:
{roster_str}

Return JSON:
{{
  "candidates": [
    {{"name": "Artist Name", "genres": ["genre-1", "genre-2"]}}
  ]
}}
"""
    fallback = CandidateSuggestionOutput(candidates=[])
    result = llm_client.generate_safe(
        SYSTEM_PROMPT,
        user_prompt,
        CandidateSuggestionOutput,
        fallback=fallback,
        temperature=0.4,
    )
    if not result:
        return fallback
    result.candidates = result.candidates[:limit]
    return result
