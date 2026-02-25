import httpx
from typing import Optional
from datetime import datetime
from app.config import get_settings

LASTFM_API_BASE = "https://ws.audioscrobbler.com/2.0"


class LastFMConnector:
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.lastfm_api_key
        self._disabled: bool = False

    @property
    def available(self) -> bool:
        return bool(self.api_key) and not self._disabled

    async def _request(self, method: str, params: dict | None = None) -> Optional[dict]:
        """Make a request to Last.fm API."""
        if not self.available:
            return None
        
        request_params = {
            "method": method,
            "api_key": self.api_key,
            "format": "json",
            **(params or {}),
        }
        
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                resp = await client.get(LASTFM_API_BASE, params=request_params)
                resp.raise_for_status()
                data = resp.json()
                # Last.fm returns errors in the response body
                if "error" in data:
                    error_code = data.get("error")
                    if error_code in {4, 10}:  # Invalid API key or service offline
                        self._disabled = True
                    return None
                return data
            except httpx.HTTPStatusError as e:
                status = e.response.status_code if e.response else None
                if status in {401, 403, 429}:
                    self._disabled = True
                return None

    async def search_artists(self, query: str, limit: int = 5) -> list[dict]:
        """Search for artists on Last.fm."""
        if not self.available:
            return []
        
        data = await self._request("artist.search", {"artist": query, "limit": limit})
        if not data:
            return []
        
        results = []
        artists = data.get("results", {}).get("artistmatches", {}).get("artist", [])
        # Last.fm returns a single dict if only one result, list if multiple
        if isinstance(artists, dict):
            artists = [artists]
        
        for item in artists[:limit]:
            artist_name = item.get("name", "")
            if not artist_name:
                continue

            mbid = item.get("mbid") or ""
            # Skip entries without a MusicBrainz ID — these are usually
            # genre tags or non-artist pages, not real musicians
            if not mbid:
                continue

            # Fetch detailed info for listener/play counts
            detail_data = await self._request("artist.getInfo", {"artist": artist_name})
            stats = {}
            genres = []
            image_url = None
            if detail_data and "artist" in detail_data:
                artist_info = detail_data["artist"]
                stats = {
                    "listeners": int(artist_info.get("stats", {}).get("listeners", 0)),
                    "playcount": int(artist_info.get("stats", {}).get("playcount", 0)),
                }
                tags = artist_info.get("tags", {}).get("tag", [])
                if isinstance(tags, dict):
                    tags = [tags]
                genres = [t.get("name", "") for t in tags if t.get("name")]
                image_url = self._extract_image_url(artist_info.get("image", []))

            results.append({
                "platform_id": mbid,
                "name": artist_name,
                "description": None,
                "image_url": image_url,
                "platform_url": item.get("url"),
                "genres": genres,
                "listeners": stats.get("listeners", 0),
                "playcount": stats.get("playcount", 0),
            })
        
        return results

    async def get_artist_stats(self, artist_name: str) -> Optional[dict]:
        """Get detailed stats for an artist."""
        if not self.available:
            return None
        
        data = await self._request("artist.getInfo", {"artist": artist_name})
        if not data or "artist" not in data:
            return None
        
        artist = data["artist"]
        stats = artist.get("stats", {})
        tags = artist.get("tags", {}).get("tag", [])
        if isinstance(tags, dict):
            tags = [tags]
        
        return {
            "listeners": int(stats.get("listeners", 0)),
            "playcount": int(stats.get("playcount", 0)),
            "genres": [tag.get("name", "") for tag in tags if tag.get("name")],
            "image_url": self._extract_image_url(artist.get("image", [])),
            "platform_url": artist.get("url"),
            "bio": artist.get("bio", {}).get("content", ""),
        }

    async def get_artist_similar(self, artist_name: str, limit: int = 10) -> list[dict]:
        """Get similar artists (great for discovery)."""
        if not self.available:
            return []
        
        data = await self._request("artist.getSimilar", {"artist": artist_name, "limit": limit})
        if not data or "similarartists" not in data:
            return []
        
        similar = data["similarartists"].get("artist", [])
        if isinstance(similar, dict):
            similar = [similar]
        
        results = []
        for item in similar[:limit]:
            results.append({
                "name": item.get("name", ""),
                "platform_url": item.get("url"),
                "match": float(item.get("match", 0)),
            })
        
        return results

    def _extract_image_url(self, images: list) -> Optional[str]:
        """Extract the largest image URL from Last.fm image array."""
        if not images:
            return None
        # Last.fm returns images in order: small, medium, large, extralarge, mega
        # Prefer large or extralarge
        for size in ["extralarge", "large", "medium"]:
            for img in images:
                if img.get("size") == size:
                    return img.get("#text")
        return None

    async def get_artist_stats_bulk(self, artist_names: list[str]) -> dict[str, dict]:
        """Get stats for multiple artists (Last.fm doesn't support bulk, so we batch)."""
        if not self.available or not artist_names:
            return {}
        
        stats: dict[str, dict] = {}
        # Last.fm doesn't have bulk endpoint, so we fetch individually
        # But we can do it concurrently
        import asyncio
        
        async def fetch_one(name: str):
            result = await self.get_artist_stats(name)
            if result:
                stats[name.lower()] = result
        
        # Batch requests to respect rate limits (5 req/sec)
        batch_size = 5
        for i in range(0, len(artist_names), batch_size):
            batch = artist_names[i:i + batch_size]
            await asyncio.gather(*[fetch_one(name) for name in batch])
            # Small delay between batches to respect rate limits
            if i + batch_size < len(artist_names):
                await asyncio.sleep(0.2)
        
        return stats
