import httpx
from typing import Optional

from app.config import get_settings

SOUNDCLOUD_API_BASE = "https://api-v2.soundcloud.com"


class SoundCloudConnector:
    def __init__(self):
        self.settings = get_settings()
        self.client_id = self.settings.soundcloud_client_id
        self._disabled: bool = False

    @property
    def available(self) -> bool:
        return bool(self.client_id)

    async def _request(self, path: str, params: dict | None = None) -> Optional[dict]:
        if not self.available or self._disabled:
            return None
        payload = dict(params or {})
        payload["client_id"] = self.client_id
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{SOUNDCLOUD_API_BASE}{path}", params=payload)
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                status = e.response.status_code if e.response else None
                if status in {401, 403, 429}:
                    self._disabled = True
                    return None
                raise
            return resp.json()

    async def search_users(self, query: str, limit: int = 5) -> list[dict]:
        if not self.available:
            return []
        data = await self._request("/search/users", params={"q": query, "limit": limit})
        if not data:
            return []
        if isinstance(data, dict):
            collection = data.get("collection") or []
        else:
            collection = data or []

        results: list[dict] = []
        for item in collection:
            if not item:
                continue
            results.append({
                "platform_id": str(item.get("id") or ""),
                "name": item.get("username"),
                "description": item.get("description"),
                "image_url": item.get("avatar_url"),
                "platform_url": item.get("permalink_url"),
                "handle": item.get("permalink"),
                "followers": item.get("followers_count"),
                "track_count": item.get("track_count"),
                "likes_count": item.get("likes_count"),
                "reposts_count": item.get("reposts_count"),
                "genre": item.get("genre"),
                "tag_list": item.get("tag_list"),
                "playback_count": item.get("track_playback_count") or item.get("playback_count"),
            })
        return results

    async def resolve_user(self, handle_or_url: str) -> Optional[dict]:
        if not self.available or not handle_or_url:
            return None
        url = handle_or_url
        if not url.startswith("http"):
            url = f"https://soundcloud.com/{handle_or_url}"
        data = await self._request("/resolve", params={"url": url})
        if not data:
            return None
        kind = data.get("kind")
        if kind and kind != "user":
            return None
        return data

    async def get_user_stats_bulk(self, user_ids: list[str]) -> dict[str, dict]:
        if not self.available or not user_ids:
            return {}
        stats: dict[str, dict] = {}
        for i in range(0, len(user_ids), 50):
            chunk = user_ids[i:i + 50]
            data = await self._request("/users", params={"ids": ",".join(chunk)})
            if not data:
                continue
            if isinstance(data, dict):
                users = data.get("collection") or []
            else:
                users = data or []
            for user in users:
                if not user:
                    continue
                uid = user.get("id")
                if not uid:
                    continue
                stats[str(uid)] = {
                    "followers": user.get("followers_count"),
                    "track_count": user.get("track_count"),
                    "likes_count": user.get("likes_count"),
                    "reposts_count": user.get("reposts_count"),
                    "playback_count": user.get("track_playback_count") or user.get("playback_count"),
                    "image_url": user.get("avatar_url"),
                    "platform_url": user.get("permalink_url"),
                    "handle": user.get("permalink"),
                    "genre": user.get("genre"),
                    "tag_list": user.get("tag_list"),
                }
        return stats

