import logging
from typing import Optional
from app.llm.client import llm_client
from app.api.schemas import QueryExpansionOutput, LabelDNAOutput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a music discovery specialist. Given a label's DNA profile,
generate search queries for discovering emerging artists across platforms.
Respond with ONLY valid JSON matching the requested schema."""


def expand_queries(label_dna: LabelDNAOutput, label_name: str) -> QueryExpansionOutput:
    """Generate platform-specific search queries from label DNA."""
    user_prompt = f"""Based on this label's taste profile, generate discovery search queries:

Label: {label_name}
Thesis: {chr(10).join(f'- {b}' for b in label_dna.label_thesis_bullets)}
Seed Queries: {label_dna.search_seed_queries}

Generate JSON:
{{
  "youtube_queries": ["10-15 YouTube search queries to find emerging artists matching this taste"],
  "tiktok_tags": ["5-10 TikTok hashtags for discovery"]
}}"""

    fallback = QueryExpansionOutput(
        youtube_queries=label_dna.search_seed_queries,
        tiktok_tags=[],
    )

    result = llm_client.generate_safe(SYSTEM_PROMPT, user_prompt, QueryExpansionOutput, fallback=fallback)
    return result or fallback
