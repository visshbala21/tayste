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

    async def get_channel_stats(self, channel_id: str) -> Optional[dict]:
        """Get channel statistics."""
        if not self.available:
            return self._mock_channel_stats(channel_id)
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{YOUTUBE_API_BASE}/channels", params={
                "key": self.api_key, "id": channel_id,
                "part": "statistics,snippet",
            })
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
        """Get recent video stats for a channel."""
        if not self.available:
            return self._mock_recent_videos(channel_id)
        async with httpx.AsyncClient() as client:
            # First get video IDs
            search_resp = await client.get(f"{YOUTUBE_API_BASE}/search", params={
                "key": self.api_key, "channelId": channel_id,
                "type": "video", "part": "id", "maxResults": max_results,
                "order": "date",
            })
            search_resp.raise_for_status()
            video_ids = [item["id"]["videoId"] for item in search_resp.json().get("items", [])]
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
