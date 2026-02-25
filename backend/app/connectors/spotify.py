import base64
import time
from typing import Optional

import httpx
from app.config import get_settings

SPOTIFY_API_BASE = "https://api.spotify.com/v1"
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/api/token"


class SpotifyConnector:
    def __init__(self):
        self.settings = get_settings()
        self.client_id = self.settings.spotify_client_id
        self.client_secret = self.settings.spotify_client_secret
        self.market = self.settings.spotify_market or "US"
        self._token: Optional[str] = None
        self._token_expiry: float = 0
        self._disabled: bool = False

    @property
    def available(self) -> bool:
        return bool(self.client_id and self.client_secret)

    async def _get_token(self) -> Optional[str]:
        if not self.available or self._disabled:
            return None
        now = time.time()
        if self._token and now < self._token_expiry - 30:
            return self._token

        auth = f"{self.client_id}:{self.client_secret}"
        b64 = base64.b64encode(auth.encode()).decode()
        headers = {"Authorization": f"Basic {b64}"}
        data = {"grant_type": "client_credentials"}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(SPOTIFY_AUTH_URL, data=data, headers=headers)
            resp.raise_for_status()
            payload = resp.json()
        self._token = payload.get("access_token")
        expires_in = payload.get("expires_in", 3600)
        self._token_expiry = now + float(expires_in)
        return self._token

    async def _request(self, path: str, params: dict | None = None) -> Optional[dict]:
        token = await self._get_token()
        if not token:
            return None
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{SPOTIFY_API_BASE}{path}", headers=headers, params=params or {})
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                status = e.response.status_code if e.response else None
                if status in {401, 429}:
                    self._disabled = True
                    return None
                if status == 403:
                    # Don't globally disable — some endpoints may still work
                    return None
                raise
            return resp.json()

    async def search_artists(self, query: str, limit: int = 5) -> list[dict]:
        if not self.available:
            return []
        data = await self._request(
            "/search",
            params={"q": query, "type": "artist", "limit": limit, "market": self.market},
        )
        if not data:
            return []
        results = []
        for item in data.get("artists", {}).get("items", []):
            results.append({
                "platform_id": item.get("id"),
                "name": item.get("name"),
                "description": None,
                "image_url": (item.get("images") or [{}])[0].get("url"),
                "platform_url": (item.get("external_urls") or {}).get("spotify"),
                "genres": item.get("genres") or [],
                "followers": (item.get("followers") or {}).get("total"),
                "popularity": item.get("popularity"),
            })
        return results

    async def get_related_artists(self, artist_id: str) -> list[dict]:
        """Get up to 20 related artists for a Spotify artist."""
        if not self.available:
            return []
        data = await self._request(f"/artists/{artist_id}/related-artists")
        if not data:
            return []
        results = []
        for item in data.get("artists", []):
            results.append({
                "platform_id": item.get("id"),
                "name": item.get("name"),
                "image_url": (item.get("images") or [{}])[0].get("url"),
                "platform_url": (item.get("external_urls") or {}).get("spotify"),
                "genres": item.get("genres") or [],
                "followers": (item.get("followers") or {}).get("total"),
                "popularity": item.get("popularity"),
            })
        return results

    async def get_artist_stats_bulk(self, artist_ids: list[str]) -> dict[str, dict]:
        if not self.available or not artist_ids:
            return {}

        stats: dict[str, dict] = {}
        # Spotify supports up to 50 IDs per request
        for i in range(0, len(artist_ids), 50):
            chunk = artist_ids[i:i + 50]
            data = await self._request("/artists", params={"ids": ",".join(chunk)})
            if not data:
                continue
            for item in data.get("artists", []):
                if not item:
                    continue
                aid = item.get("id")
                if not aid:
                    continue
                stats[aid] = {
                    "followers": (item.get("followers") or {}).get("total"),
                    "popularity": item.get("popularity"),
                    "genres": item.get("genres") or [],
                    "image_url": (item.get("images") or [{}])[0].get("url"),
                    "platform_url": (item.get("external_urls") or {}).get("spotify"),
                }
        return stats
