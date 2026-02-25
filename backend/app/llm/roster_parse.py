import json
import logging
import re
from typing import List
from urllib.parse import urlparse

from app.api.schemas import RosterParseOutput, RosterParsedArtist
from app.llm.client import llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a data normalization assistant for music rosters.
Extract artist roster entries from raw text. Output ONLY valid JSON that matches the schema.
Rules:
- Return every artist entry you can identify.
- Include platform if explicitly mentioned (youtube, spotify, soundcloud, lastfm, tiktok).
- If a URL is present, include it as platform_url.
- If a YouTube channel ID is present (starts with UC...), include as platform_id.
- If only a handle is present (e.g. @artist), keep it in platform_url if possible, otherwise omit.
- genre_tags should be a list of strings if clearly provided; otherwise omit.
"""

URL_RE = re.compile(r"(https?://[^\s\)\]]+)")
YOUTUBE_CHANNEL_RE = re.compile(r"youtube\.com/channel/(UC[a-zA-Z0-9_-]{20,})", re.IGNORECASE)
NULL_LIKE = {"none", "null", "n/a", "na", "", "unknown"}


def _detect_platform(url: str, default_platform: str) -> str:
    lower = url.lower()
    if "youtube.com" in lower or "youtu.be" in lower:
        return "youtube"
    if "soundcloud.com" in lower:
        return "soundcloud"
    if "tiktok.com" in lower:
        return "tiktok"
    if "spotify.com" in lower:
        return "spotify"
    if "last.fm" in lower or "lastfm" in lower:
        return "lastfm"
    return default_platform


def _extract_youtube_channel_id(url: str) -> str | None:
    match = YOUTUBE_CHANNEL_RE.search(url)
    if match:
        return match.group(1)
    return None


def _name_from_url(url: str) -> str | None:
    try:
        parsed = urlparse(url)
    except Exception:
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if not parts:
        return None
    last = parts[-1].lstrip("@").strip()
    return last or None


def _extract_genres(text: str) -> list | None:
    match = re.search(r"[\(\[]([^\)\]]+)[\)\]]", text)
    if not match:
        return None
    raw = match.group(1)
    genres = [g.strip() for g in re.split(r"[,\|/]", raw) if g.strip()]
    return genres or None


def _normalize_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.lower() in NULL_LIKE:
            return None
        return stripped
    return value


def _parse_json_roster(raw_text: str) -> RosterParseOutput | None:
    try:
        obj = json.loads(raw_text)
    except Exception:
        return None

    artists: List[RosterParsedArtist] = []

    def handle_entry(entry: dict):
        name = _normalize_value(entry.get("name") or entry.get("artist") or entry.get("artist_name"))
        if not name:
            return
        platform = _normalize_value(entry.get("platform") or entry.get("service"))
        platform_id = _normalize_value(entry.get("platform_id") or entry.get("channel_id"))
        platform_url = _normalize_value(entry.get("platform_url") or entry.get("url") or entry.get("link"))
        genres = entry.get("genre_tags") or entry.get("genres")
        if isinstance(genres, str):
            genres = [g.strip() for g in genres.split(",") if g.strip()]
        elif isinstance(genres, list):
            genres = [str(g).strip() for g in genres if str(g).strip()]
        else:
            genres = None

        artists.append(RosterParsedArtist(
            name=str(name),
            platform=str(platform).lower() if platform else None,
            platform_id=str(platform_id) if platform_id else None,
            platform_url=str(platform_url) if platform_url else None,
            genre_tags=genres,
        ))

    if isinstance(obj, dict):
        if isinstance(obj.get("artists"), list):
            for entry in obj["artists"]:
                if isinstance(entry, dict):
                    handle_entry(entry)
    elif isinstance(obj, list):
        for entry in obj:
            if isinstance(entry, dict):
                handle_entry(entry)

    if not artists:
        return None
    return RosterParseOutput(artists=artists)


def _heuristic_parse(raw_text: str, default_platform: str) -> RosterParseOutput:
    artists: List[RosterParsedArtist] = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        url_match = URL_RE.search(line)
        url = url_match.group(1) if url_match else None
        platform = default_platform
        platform_id = None
        platform_url = None

        if url:
            platform_url = url
            platform = _detect_platform(url, default_platform)
            if platform == "youtube":
                platform_id = _extract_youtube_channel_id(url)

        genres = _extract_genres(line)

        name = line
        if url:
            name = line.replace(url, "").strip(" -|•\t")
        if not name:
            name = _name_from_url(url) if url else None
        if not name:
            continue

        artists.append(RosterParsedArtist(
            name=name,
            platform=platform,
            platform_id=platform_id,
            platform_url=platform_url,
            genre_tags=genres,
        ))

    return RosterParseOutput(artists=artists)


def parse_roster_text(raw_text: str, default_platform: str = "youtube") -> RosterParseOutput:
    """Parse roster from raw text using LLM with a heuristic fallback."""
    raw_text = (raw_text or "").strip()
    if not raw_text:
        return RosterParseOutput(artists=[])

    json_parsed = _parse_json_roster(raw_text)
    if json_parsed:
        return json_parsed

    user_prompt = f"""Raw roster text:
{raw_text}

Return JSON:
{{
  "artists": [
    {{
      "name": "Artist Name",
      "platform": "youtube",
      "platform_id": "UCxxxxxxxxxxxxxxxxxxxx",
      "platform_url": "https://youtube.com/channel/UCxxxx",
      "genre_tags": ["indie-rock", "dream-pop"]
    }}
  ]
}}
"""

    # Always compute a heuristic fallback so we never return an empty result
    # just because the LLM was conservative or confused by the input format.
    fallback = _heuristic_parse(raw_text, default_platform)
    result = llm_client.generate_safe(
        SYSTEM_PROMPT,
        user_prompt,
        RosterParseOutput,
        fallback=fallback,
        temperature=0.1,
    )

    # Prefer the LLM output if it actually found artists; otherwise fall back
    # to the heuristic parser so that structured text (like JSON) or slightly
    # odd formats still yield entries instead of silently returning zero.
    if result and getattr(result, "artists", None):
        return result
    return fallback
