"""Reddit API connector with OAuth2 client credentials, rate limiting, and graceful degradation."""
import asyncio
import hashlib
import logging
import time
from typing import Optional

import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)

REDDIT_AUTH_URL = "https://www.reddit.com/api/v1/access_token"
REDDIT_API_BASE = "https://oauth.reddit.com"

# Genre tag → subreddit mapping
GENRE_SUBREDDIT_MAP: dict[str, list[str]] = {
    "hip-hop": ["hiphopheads", "rap"],
    "hip hop": ["hiphopheads", "rap"],
    "rap": ["hiphopheads", "rap"],
    "indie": ["indieheads"],
    "dream-pop": ["indieheads"],
    "dream pop": ["indieheads"],
    "shoegaze": ["indieheads"],
    "post-punk": ["indieheads"],
    "post punk": ["indieheads"],
    "pop": ["popheads"],
    "electronic": ["electronicmusic"],
    "edm": ["electronicmusic"],
    "metal": ["Metal"],
    "r&b": ["rnb", "hiphopheads"],
    "rnb": ["rnb", "hiphopheads"],
}

FALLBACK_SUBREDDITS = ["Music", "listentothis"]


class RedditConnector:
    def __init__(self):
        self.settings = get_settings()
        self.client_id = self.settings.reddit_client_id
        self.client_secret = self.settings.reddit_client_secret
        self.user_agent = self.settings.reddit_user_agent
        self._token: Optional[str] = None
        self._token_expiry: float = 0
        self._rate_lock = asyncio.Lock()
        self._last_request_time: float = 0
        self._min_interval: float = 0.6  # ~100 req/min

    @property
    def available(self) -> bool:
        return bool(self.client_id and self.client_secret)

    async def _get_token(self) -> Optional[str]:
        """OAuth2 client credentials flow (mirrors SpotifyConnector._get_token)."""
        if not self.available:
            return None
        now = time.time()
        if self._token and now < self._token_expiry - 30:
            return self._token

        auth = httpx.BasicAuth(self.client_id, self.client_secret)
        headers = {"User-Agent": self.user_agent}
        data = {"grant_type": "client_credentials"}

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(REDDIT_AUTH_URL, auth=auth, data=data, headers=headers)
            resp.raise_for_status()
            payload = resp.json()

        self._token = payload.get("access_token")
        expires_in = payload.get("expires_in", 3600)
        self._token_expiry = now + float(expires_in)
        return self._token

    async def _request(self, path: str, params: dict | None = None) -> Optional[dict]:
        """Authenticated GET with rate limiting and graceful error handling."""
        token = await self._get_token()
        if not token:
            return None

        # Rate limiting
        async with self._rate_lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            self._last_request_time = time.time()

        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": self.user_agent,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{REDDIT_API_BASE}{path}",
                headers=headers,
                params=params or {},
            )
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                status = e.response.status_code if e.response else None
                if status in {401, 403}:
                    logger.warning(f"Reddit auth/access error ({status}) for {path}")
                    self._token = None  # Force re-auth on next request
                    return None
                if status == 429:
                    logger.warning("Reddit rate limit hit (429)")
                    return None
                if status == 404:
                    return None
                raise
            return resp.json()

    def get_subreddits_for_genres(self, genre_tags: list[str]) -> list[str]:
        """Map genre tags to a deduplicated list of subreddits."""
        subs: list[str] = []
        seen: set[str] = set()
        for tag in genre_tags:
            key = tag.lower().strip()
            for sub in GENRE_SUBREDDIT_MAP.get(key, []):
                if sub.lower() not in seen:
                    seen.add(sub.lower())
                    subs.append(sub)
        # Always include fallbacks
        for sub in FALLBACK_SUBREDDITS:
            if sub.lower() not in seen:
                seen.add(sub.lower())
                subs.append(sub)
        return subs

    async def search_artist_posts(
        self,
        artist_name: str,
        subreddit: str,
        limit: int = 10,
        time_filter: str = "month",
    ) -> list[dict]:
        """Search for posts about an artist in a subreddit."""
        data = await self._request(
            f"/r/{subreddit}/search",
            params={
                "q": f'"{artist_name}"',
                "restrict_sr": "true",
                "sort": "relevance",
                "t": time_filter,
                "limit": limit,
                "type": "link",
            },
        )
        if not data:
            return []

        posts = []
        for child in data.get("data", {}).get("children", []):
            post = child.get("data", {})
            posts.append({
                "post_id": post.get("id", ""),
                "title": post.get("title", ""),
                "score": post.get("score", 0),
                "num_comments": post.get("num_comments", 0),
                "url": f"https://reddit.com{post.get('permalink', '')}",
                "selftext": (post.get("selftext") or "")[:500],
                "subreddit": subreddit,
            })
        return posts

    async def get_post_comments(
        self,
        subreddit: str,
        post_id: str,
        limit: int = 50,
    ) -> list[dict]:
        """Get top-level comments for a post."""
        data = await self._request(
            f"/r/{subreddit}/comments/{post_id}",
            params={"depth": 1, "limit": limit, "sort": "top"},
        )
        if not data:
            return []

        # Reddit returns [post_listing, comments_listing]
        comments_listing = data[1] if isinstance(data, list) and len(data) > 1 else None
        if not comments_listing:
            return []

        comments = []
        for child in comments_listing.get("data", {}).get("children", []):
            if child.get("kind") != "t1":
                continue
            c = child.get("data", {})
            author = c.get("author", "")
            text = (c.get("body") or "")[:500]
            if not text:
                continue
            comments.append({
                "comment_id": c.get("id", ""),
                "text": text,
                "author_hash": hashlib.sha256(author.encode()).hexdigest()[:16] if author else "",
                "score": c.get("score", 0),
                "reply_count": len(c.get("replies", {}).get("data", {}).get("children", []))
                    if isinstance(c.get("replies"), dict) else 0,
            })
        return comments
