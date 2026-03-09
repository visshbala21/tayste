"""TikTok Research API connector.

Uses client credentials (server-to-server) OAuth to access the Research API v2.
Endpoints: user info lookup, video query (for discovery), video comments.
"""
import httpx
import logging
import time
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)

TIKTOK_AUTH_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_API_BASE = "https://open.tiktokapis.com/v2/research"


class TikTokConnector:
    def __init__(self):
        self.settings = get_settings()
        self.client_key = self.settings.tiktok_client_key
        self.client_secret = self.settings.tiktok_client_secret
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    @property
    def available(self) -> bool:
        return bool(self.client_key and self.client_secret)

    async def _ensure_token(self):
        """Get or refresh the client access token."""
        if self._access_token and time.time() < self._token_expires_at - 60:
            return

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                TIKTOK_AUTH_URL,
                data={
                    "client_key": self.client_key,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            data = resp.json()
            self._access_token = data["access_token"]
            self._token_expires_at = time.time() + data.get("expires_in", 7200)
            logger.info("TikTok access token refreshed, expires in %ds", data.get("expires_in", 7200))

    async def _request(self, method: str, url: str, **kwargs) -> dict:
        """Make an authenticated request to the TikTok API."""
        await self._ensure_token()
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                url,
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Content-Type": "application/json",
                },
                **kwargs,
            )
            if resp.status_code == 401:
                # Token expired, refresh and retry once
                self._access_token = None
                await self._ensure_token()
                resp = await client.request(
                    method,
                    url,
                    headers={
                        "Authorization": f"Bearer {self._access_token}",
                        "Content-Type": "application/json",
                    },
                    **kwargs,
                )
            if resp.status_code == 429:
                raise httpx.HTTPStatusError(
                    "TikTok rate limit exceeded",
                    request=resp.request,
                    response=resp,
                )
            resp.raise_for_status()
            return resp.json()

    async def get_user_info(self, username: str) -> Optional[dict]:
        """Look up a TikTok user by username.

        Returns dict with: display_name, bio, avatar_url, follower_count,
        following_count, likes_count, video_count, is_verified.
        """
        if not self.available:
            return None

        handle = username.lstrip("@")
        try:
            data = await self._request(
                "POST",
                f"{TIKTOK_API_BASE}/user/info/",
                json={
                    "username": handle,
                    "fields": [
                        "display_name",
                        "bio_description",
                        "avatar_url",
                        "follower_count",
                        "following_count",
                        "likes_count",
                        "video_count",
                        "is_verified",
                    ],
                },
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (400, 404):
                return None
            raise

        user = data.get("data", {}).get("user_info", {})
        if not user:
            return None

        return {
            "display_name": user.get("display_name", ""),
            "bio": user.get("bio_description", ""),
            "avatar_url": user.get("avatar_url"),
            "follower_count": user.get("follower_count", 0),
            "following_count": user.get("following_count", 0),
            "likes_count": user.get("likes_count", 0),
            "video_count": user.get("video_count", 0),
            "is_verified": user.get("is_verified", False),
        }

    async def query_videos(
        self,
        keyword: str,
        max_count: int = 20,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        region_code: Optional[str] = None,
    ) -> list[dict]:
        """Search public TikTok videos by keyword.

        start_date/end_date: 'YYYYMMDD' format strings.
        Returns list of video dicts with: id, desc, like_count, comment_count,
        share_count, view_count, create_time, author username.
        """
        if not self.available:
            return []

        query: dict = {
            "and": [{"operation": "IN", "field_name": "keyword", "field_values": [keyword]}]
        }
        if region_code:
            query["and"].append(
                {"operation": "EQ", "field_name": "region_code", "field_values": [region_code]}
            )

        body: dict = {
            "query": query,
            "max_count": min(max_count, 100),
            "fields": [
                "id",
                "video_description",
                "like_count",
                "comment_count",
                "share_count",
                "view_count",
                "create_time",
                "username",
                "music_id",
                "hashtag_names",
            ],
        }
        if start_date:
            body["start_date"] = start_date
        if end_date:
            body["end_date"] = end_date

        try:
            data = await self._request(
                "POST",
                f"{TIKTOK_API_BASE}/video/query/",
                json=body,
            )
        except httpx.HTTPStatusError:
            return []

        videos = data.get("data", {}).get("videos", [])
        return [
            {
                "video_id": v.get("id"),
                "description": v.get("video_description", ""),
                "like_count": v.get("like_count", 0),
                "comment_count": v.get("comment_count", 0),
                "share_count": v.get("share_count", 0),
                "view_count": v.get("view_count", 0),
                "create_time": v.get("create_time"),
                "username": v.get("username", ""),
                "hashtags": v.get("hashtag_names", []),
            }
            for v in videos
        ]

    async def get_video_comments(
        self,
        video_id: str,
        max_count: int = 50,
        cursor: int = 0,
    ) -> dict:
        """Get comments on a TikTok video.

        Returns {comments: [{text, like_count, create_time}], cursor, has_more}.
        """
        if not self.available:
            return {"comments": [], "cursor": 0, "has_more": False}

        body: dict = {
            "video_id": video_id,
            "max_count": min(max_count, 100),
            "fields": ["text", "like_count", "create_time", "id"],
        }
        if cursor:
            body["cursor"] = cursor

        try:
            data = await self._request(
                "POST",
                f"{TIKTOK_API_BASE}/video/comment/list/",
                json=body,
            )
        except httpx.HTTPStatusError:
            return {"comments": [], "cursor": 0, "has_more": False}

        comments_data = data.get("data", {})
        comments = [
            {
                "comment_id": c.get("id", ""),
                "text": c.get("text", ""),
                "like_count": c.get("like_count", 0),
                "create_time": c.get("create_time"),
            }
            for c in comments_data.get("comments", [])
        ]

        return {
            "comments": comments,
            "cursor": comments_data.get("cursor", 0),
            "has_more": comments_data.get("has_more", False),
        }
