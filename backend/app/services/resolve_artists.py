"""Resolve artist names to platform profiles (Spotify, YouTube, Soundcharts)."""
import asyncio
import logging
import re
from typing import Optional, List

from pydantic import BaseModel

from app.api.schemas import ResolvedArtistProfile, PlatformEntry
from app.connectors.spotify import SpotifyConnector
from app.connectors.youtube import YouTubeConnector
from app.connectors.soundcharts import SoundchartsConnector

logger = logging.getLogger(__name__)

RESOLVE_CONCURRENCY = 5


# --- Name extraction from freeform text ---

class ExtractedNames(BaseModel):
    artist_names: List[str]


EXTRACT_SYSTEM_PROMPT = """You are a music industry assistant. Extract artist/band names from the user's text.
Rules:
- Return ONLY artist/band names, one per entry.
- Handle any format: comma-separated, numbered lists, bullet points, prose, parenthetical notes.
- If an entry has aliases or member names in parentheses like "Tha Dogg Pound (Kurupt & Daz Dillinger)", keep the main act name AND extract the members as separate artists.
- Strip numbering, bullets, dashes, and other formatting artifacts.
- Do not include labels, descriptions, genres, or other non-artist text.
- Return JSON: {"artist_names": ["Artist 1", "Artist 2", ...]}
"""

# Patterns to strip from heuristic parse
_STRIP_PATTERNS = [
    re.compile(r"^\d+[\.\)\-\:]?\s*"),        # "1. " "2) " "3- "
    re.compile(r"^[\-\*\•\▸\→\›]\s*"),        # "- " "* " "• "
    re.compile(r"\s*[\(\[].*?[\)\]]"),          # "(member info)" "[genre]"
]


def _heuristic_extract(text: str) -> list[str]:
    """Fallback: split on newlines, commas, 'and', then clean up."""
    # First split on newlines
    lines = text.splitlines()

    # If there's only one line (or very few), also split on commas
    if len([l for l in lines if l.strip()]) <= 2:
        parts = []
        for line in lines:
            parts.extend(re.split(r",\s*", line))
        lines = parts

    names = []
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue

        # Split on " and " / " & " at boundaries (but not inside names like "Simon & Garfunkel")
        # Only split if the segment before/after looks like separate names
        sub_parts = re.split(r",\s*(?:and|&)\s+|\s+and\s+", raw, flags=re.IGNORECASE)

        for part in sub_parts:
            part = part.strip()
            if not part:
                continue

            # Strip numbering, bullets
            for pat in _STRIP_PATTERNS:
                part = pat.sub("", part).strip()

            if not part:
                continue

            # Skip if it looks like a genre/description (all lowercase, no capital)
            if len(part) > 3 and part == part.lower() and not any(c.isdigit() for c in part):
                continue

            # Skip very short fragments
            if len(part) < 2:
                continue

            names.append(part)

    return names


def extract_artist_names(text: str) -> tuple[list[str], list[str]]:
    """Extract artist names from any freeform text. Uses LLM with heuristic fallback.

    Returns (names, warnings).
    """
    text = (text or "").strip()
    if not text:
        return [], ["No text provided"]

    warnings: list[str] = []

    # Try LLM extraction first
    try:
        from app.llm.client import llm_client

        if llm_client.available:
            result = llm_client.generate_safe(
                EXTRACT_SYSTEM_PROMPT,
                f"Extract artist names from:\n{text}",
                ExtractedNames,
                fallback=None,
                temperature=0.0,
            )
            if result and result.artist_names:
                # Deduplicate while preserving order
                seen: set[str] = set()
                deduped = []
                for name in result.artist_names:
                    name = name.strip()
                    if name and name.lower() not in seen:
                        seen.add(name.lower())
                        deduped.append(name)
                if deduped:
                    return deduped, warnings
                warnings.append("LLM returned no names, falling back to heuristic")
    except Exception as e:
        logger.warning(f"LLM name extraction failed: {e}")
        warnings.append("LLM extraction failed, using heuristic parser")

    # Heuristic fallback
    names = _heuristic_extract(text)
    if not names:
        warnings.append("Could not extract any artist names")
    return names, warnings


# --- Platform resolution ---

async def _resolve_single(
    name: str,
    spotify: SpotifyConnector,
    youtube: YouTubeConnector,
    soundcharts: SoundchartsConnector,
) -> ResolvedArtistProfile:
    """Resolve a single artist name across all platforms."""
    profile = ResolvedArtistProfile(name=name, query_name=name)

    # Spotify (primary — best name matching, genres, images)
    try:
        if spotify.available:
            results = await spotify.search_artists(name, limit=3)
            if results:
                best = results[0]
                profile.spotify = PlatformEntry(
                    platform="spotify",
                    platform_id=best.get("platform_id"),
                    platform_url=best.get("platform_url"),
                )
                profile.image_url = best.get("image_url")
                profile.genres = best.get("genres") or []
                profile.spotify_followers = best.get("followers")
                profile.spotify_popularity = best.get("popularity")
                profile.name = best.get("name") or name
                profile.resolved = True
    except Exception as e:
        logger.warning(f"Spotify resolve failed for '{name}': {e}")

    # YouTube
    try:
        if youtube.available:
            results = await youtube.search_channels(name, max_results=1)
            if results:
                best = results[0]
                profile.youtube = PlatformEntry(
                    platform="youtube",
                    platform_id=best.get("platform_id"),
                    platform_url=best.get("platform_url"),
                )
                if not profile.image_url:
                    profile.image_url = best.get("image_url")
    except Exception as e:
        logger.warning(f"YouTube resolve failed for '{name}': {e}")

    # Soundcharts
    try:
        if soundcharts.available:
            results = await soundcharts.search_artists(name, limit=1)
            if results:
                best = results[0]
                profile.soundcharts = PlatformEntry(
                    platform="soundcharts",
                    platform_id=best.get("sc_uuid"),
                    platform_url=None,
                )
                if not profile.image_url:
                    profile.image_url = best.get("image_url")
                if not profile.genres:
                    profile.genres = best.get("genres") or []
    except Exception as e:
        logger.warning(f"Soundcharts resolve failed for '{name}': {e}")

    return profile


async def resolve_artist_names(
    names: list[str],
) -> tuple[list[ResolvedArtistProfile], list[str]]:
    """Resolve a list of artist names to platform profiles.

    Returns (resolved_profiles, warnings).
    """
    # Deduplicate and clean names
    seen: set[str] = set()
    clean_names: list[str] = []
    warnings: list[str] = []

    for raw in names:
        name = raw.strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            warnings.append(f"Duplicate name skipped: '{name}'")
            continue
        seen.add(key)
        clean_names.append(name)

    if not clean_names:
        return [], ["No valid artist names provided"]

    # Initialize connectors
    spotify = SpotifyConnector()
    youtube = YouTubeConnector()
    soundcharts = SoundchartsConnector()

    sem = asyncio.Semaphore(RESOLVE_CONCURRENCY)
    results: list[Optional[ResolvedArtistProfile]] = [None] * len(clean_names)

    async def _resolve_with_sem(idx: int, name: str):
        async with sem:
            results[idx] = await _resolve_single(name, spotify, youtube, soundcharts)

    await asyncio.gather(*[_resolve_with_sem(i, n) for i, n in enumerate(clean_names)])

    profiles = [r for r in results if r is not None]

    # Warn about unresolved artists
    for p in profiles:
        if not p.resolved:
            warnings.append(f"Could not resolve '{p.query_name}' on any platform — will import name only")

    return profiles, warnings
