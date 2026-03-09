"""Genius API connector for song annotations and comments as cultural signals."""
import asyncio
import logging
from typing import Optional

import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)

GENIUS_API_BASE = "https://api.genius.com"


class GeniusConnector:
    def __init__(self):
        self.settings = get_settings()
        self.access_token = self.settings.genius_access_token
        self._rate_lock = asyncio.Lock()
        self._last_request_time: float = 0
        self._min_interval: float = 0.2  # conservative ~5 req/s

    @property
    def available(self) -> bool:
        return bool(self.access_token)

    async def _request(self, path: str, params: dict | None = None) -> Optional[dict]:
        """Authenticated GET with rate limiting."""
        if not self.available:
            return None

        import time
        async with self._rate_lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            self._last_request_time = time.time()

        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{GENIUS_API_BASE}{path}",
                headers=headers,
                params=params or {},
            )
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                status = e.response.status_code if e.response else None
                if status in {401, 403}:
                    logger.warning(f"Genius auth error ({status}) for {path}")
                    return None
                if status == 429:
                    logger.warning("Genius rate limit hit (429)")
                    return None
                if status == 404:
                    return None
                raise
            return resp.json()

    async def search_artist_songs(self, artist_name: str, max_songs: int = 5) -> list[dict]:
        """Search for an artist's songs on Genius. Returns top results by relevance."""
        data = await self._request("/search", params={"q": artist_name, "per_page": max_songs})
        if not data:
            return []

        songs = []
        artist_lower = artist_name.lower()
        for hit in data.get("response", {}).get("hits", []):
            if hit.get("type") != "song":
                continue
            song = hit.get("result", {})
            primary_artist = song.get("primary_artist", {})
            # Filter to songs by this artist (not just mentioned in)
            if artist_lower not in (primary_artist.get("name", "")).lower():
                continue
            songs.append({
                "song_id": song.get("id"),
                "title": song.get("title", ""),
                "full_title": song.get("full_title", ""),
                "url": song.get("url", ""),
                "annotation_count": song.get("annotation_count", 0),
                "artist_id": primary_artist.get("id"),
                "artist_name": primary_artist.get("name", ""),
                "stats": song.get("stats", {}),
            })
        return songs

    async def get_song_comments(
        self, song_id: int, per_page: int = 50, page: int = 1
    ) -> list[dict]:
        """Get comments on a song."""
        import hashlib

        data = await self._request(
            f"/songs/{song_id}/comments",
            params={"per_page": per_page, "page": page, "text_format": "plain"},
        )
        if not data:
            return []

        comments = []
        for item in data.get("response", {}).get("comments", []):
            body = item.get("body", {})
            text = body.get("plain", "") if isinstance(body, dict) else str(body)
            text = text[:500]  # truncate like YouTube pattern
            if not text:
                continue
            author = item.get("author", {})
            author_id = str(author.get("id", "")) if author else ""
            comments.append({
                "comment_id": str(item.get("id", "")),
                "text": text,
                "author_hash": hashlib.sha256(author_id.encode()).hexdigest()[:16] if author_id else "",
                "votes_total": item.get("votes_total", 0),
                "reply_count": len(item.get("replies", [])) if item.get("replies") else 0,
            })
        return comments

    async def get_song_referents(
        self, song_id: int, per_page: int = 20, page: int = 1
    ) -> list[dict]:
        """Get referents (annotations) for a song. High engagement signal."""
        data = await self._request(
            "/referents",
            params={
                "song_id": song_id,
                "per_page": per_page,
                "page": page,
                "text_format": "plain",
            },
        )
        if not data:
            return []

        referents = []
        for ref in data.get("response", {}).get("referents", []):
            annotations = ref.get("annotations", [])
            if not annotations:
                continue
            ann = annotations[0]  # primary annotation
            body = ann.get("body", {})
            text = body.get("plain", "") if isinstance(body, dict) else str(body)
            text = text[:500]
            if not text:
                continue
            referents.append({
                "referent_id": str(ref.get("id", "")),
                "annotation_id": str(ann.get("id", "")),
                "text": text,
                "votes_total": ann.get("votes_total", 0),
                "verified": ann.get("verified", False),
                "fragment": ref.get("fragment", ""),
            })
        return referents
