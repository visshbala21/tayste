"""Resolve artist names to platform profiles (Spotify, YouTube, Soundcharts)."""
import asyncio
import logging
from typing import Optional

from app.api.schemas import ResolvedArtistProfile, PlatformEntry
from app.connectors.spotify import SpotifyConnector
from app.connectors.youtube import YouTubeConnector
from app.connectors.soundcharts import SoundchartsConnector

logger = logging.getLogger(__name__)

RESOLVE_CONCURRENCY = 5


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
                # Pick best match (first result from Spotify is usually best)
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
                profile.name = best.get("name") or name  # Use Spotify's canonical name
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
