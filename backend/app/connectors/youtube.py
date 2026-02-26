import httpx
from typing import Optional
from datetime import datetime
from app.config import get_settings

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


class YouTubeConnector:
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.youtube_api_key

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    async def search_channels(self, query: str, max_results: int = 10) -> list[dict]:
        """Search YouTube for channels matching query."""
        if not self.available:
            return self._mock_search(query, max_results)
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{YOUTUBE_API_BASE}/search", params={
                "key": self.api_key, "q": query, "type": "channel",
                "part": "snippet", "maxResults": max_results,
                "order": "viewCount",
            })
            if resp.status_code in (400, 403, 429):
                raise httpx.HTTPStatusError(
                    f"YouTube quota/auth error: {resp.status_code}",
                    request=resp.request, response=resp,
                )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("items", []):
                results.append({
                    "platform_id": item["snippet"]["channelId"],
                    "name": item["snippet"]["title"],
                    "description": item["snippet"].get("description", ""),
                    "image_url": item["snippet"]["thumbnails"].get("high", {}).get("url"),
                    "platform_url": f"https://youtube.com/channel/{item['snippet']['channelId']}",
                })
            return results

    async def _resolve_channel_id(self, identifier: str) -> Optional[str]:
        if not identifier:
            return None
        raw = identifier.strip()
        if raw.startswith("UC") and len(raw) >= 20:
            return raw

        handle = raw
        if handle.startswith("@"):
            handle = handle[1:]

        async with httpx.AsyncClient() as client:
            # Try handle lookup (YouTube handles)
            resp = await client.get(f"{YOUTUBE_API_BASE}/channels", params={
                "key": self.api_key,
                "part": "id",
                "forHandle": handle,
            })
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    return items[0].get("id")

            # Try legacy username lookup
            resp = await client.get(f"{YOUTUBE_API_BASE}/channels", params={
                "key": self.api_key,
                "part": "id",
                "forUsername": handle,
            })
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    return items[0].get("id")

        # Fallback to search
        try:
            results = await self.search_channels(raw, max_results=1)
        except Exception:
            return None
        if results:
            return results[0].get("platform_id")
        return None

    async def get_channel_stats(self, channel_id: str) -> Optional[dict]:
        """Get channel statistics."""
        if not self.available:
            return self._mock_channel_stats(channel_id)
        resolved = channel_id
        if not channel_id.startswith("UC"):
            resolved = await self._resolve_channel_id(channel_id) or channel_id
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{YOUTUBE_API_BASE}/channels", params={
                "key": self.api_key, "id": resolved,
                "part": "statistics,snippet",
            })
            if resp.status_code in (400, 404):
                return None
            if resp.status_code in (403, 429):
                raise httpx.HTTPStatusError(
                    f"YouTube quota/auth error: {resp.status_code}",
                    request=resp.request, response=resp,
                )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            if not items:
                return None
            stats = items[0]["statistics"]
            return {
                "followers": int(stats.get("subscriberCount", 0)),
                "views": int(stats.get("viewCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "captured_at": datetime.utcnow(),
            }

    async def get_recent_videos(self, channel_id: str, max_results: int = 5) -> list[dict]:
        """Get recent video stats for a channel.
        Uses playlistItems.list (1 quota unit) instead of search.list (100 units).
        The uploads playlist ID is derived from the channel ID: UC... -> UU...
        """
        if not self.available:
            return self._mock_recent_videos(channel_id)
        resolved = channel_id
        if not channel_id.startswith("UC"):
            resolved = await self._resolve_channel_id(channel_id) or channel_id
        async with httpx.AsyncClient() as client:
            # Derive uploads playlist ID from channel ID (UC -> UU)
            uploads_playlist_id = "UU" + resolved[2:] if resolved.startswith("UC") else None
            if not uploads_playlist_id:
                return []
            # Use playlistItems.list (1 unit) instead of search.list (100 units)
            search_resp = await client.get(f"{YOUTUBE_API_BASE}/playlistItems", params={
                "key": self.api_key, "playlistId": uploads_playlist_id,
                "part": "contentDetails", "maxResults": max_results,
            })
            search_resp.raise_for_status()
            video_ids = [
                item["contentDetails"]["videoId"]
                for item in search_resp.json().get("items", [])
                if "contentDetails" in item and "videoId" in item["contentDetails"]
            ]
            if not video_ids:
                return []
            # Then get stats
            stats_resp = await client.get(f"{YOUTUBE_API_BASE}/videos", params={
                "key": self.api_key, "id": ",".join(video_ids),
                "part": "statistics,snippet",
            })
            stats_resp.raise_for_status()
            results = []
            for item in stats_resp.json().get("items", []):
                s = item["statistics"]
                results.append({
                    "video_id": item["id"],
                    "title": item["snippet"]["title"],
                    "views": int(s.get("viewCount", 0)),
                    "likes": int(s.get("likeCount", 0)),
                    "comments": int(s.get("commentCount", 0)),
                    "published_at": item["snippet"]["publishedAt"],
                })
            return results

    def _mock_search(self, query: str, max_results: int) -> list[dict]:
        """Return mock data when API key not available."""
        return []

    def _mock_channel_stats(self, channel_id: str) -> dict:
        import random
        return {
            "followers": random.randint(1000, 500000),
            "views": random.randint(50000, 10000000),
            "video_count": random.randint(10, 200),
            "captured_at": datetime.utcnow(),
        }

    def _mock_recent_videos(self, channel_id: str) -> list[dict]:
        return []
