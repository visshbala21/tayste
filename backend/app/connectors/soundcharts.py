"""Soundcharts API connector with dual-header auth, rate limiting, and circuit breaker."""
import asyncio
import logging
import time
from typing import Optional

import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)


class SoundchartsConnector:
    def __init__(self):
        self.settings = get_settings()
        self.app_id = self.settings.soundcharts_app_id
        self.api_key = self.settings.soundcharts_api_key
        self.base_url = self.settings.soundcharts_api_base.rstrip("/")

        # Rate limiter (Soundcharts allows 10k req/min but we stay conservative)
        self._rate_lock = asyncio.Lock()
        self._last_request_time: float = 0
        self._rate_limit: float = 50.0  # req/s (conservative; actual limit is ~167/s)

        # Circuit breaker
        self._consecutive_failures: int = 0
        self._circuit_open_until: float = 0
        self._max_failures: int = 3
        self._cooldown_seconds: float = 300  # 5 min

        # Profile cache (in-memory TTL)
        self._profile_cache: dict[str, tuple[float, dict]] = {}
        self._profile_ttl: float = 3600  # 1 hour

        # ID mapping cache
        self._id_cache: dict[str, tuple[float, dict]] = {}
        self._id_cache_ttl: float = 86400 * 30  # 30 days

    @property
    def available(self) -> bool:
        return bool(self.app_id and self.api_key)

    def _is_circuit_open(self) -> bool:
        if self._consecutive_failures < self._max_failures:
            return False
        if time.time() >= self._circuit_open_until:
            self._consecutive_failures = 0
            return False
        return True

    def _auth_headers(self) -> dict:
        return {
            "x-app-id": self.app_id,
            "x-api-key": self.api_key,
        }

    async def _rate_wait(self):
        async with self._rate_lock:
            now = time.time()
            min_interval = 1.0 / self._rate_limit
            elapsed = now - self._last_request_time
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            self._last_request_time = time.time()

    async def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json_body: dict | None = None,
    ) -> Optional[dict]:
        if not self.available:
            return None
        if self._is_circuit_open():
            logger.warning("Soundcharts circuit breaker is open, skipping request")
            return None

        await self._rate_wait()

        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            if method == "POST":
                resp = await client.post(
                    url, headers=self._auth_headers(), params=params or {}, json=json_body or {},
                )
            else:
                resp = await client.get(
                    url, headers=self._auth_headers(), params=params or {},
                )
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                status = e.response.status_code if e.response else None
                if status and status >= 500:
                    self._consecutive_failures += 1
                    if self._consecutive_failures >= self._max_failures:
                        self._circuit_open_until = time.time() + self._cooldown_seconds
                        logger.error(
                            f"Soundcharts circuit breaker tripped after {self._max_failures} "
                            f"consecutive 5xx errors, cooldown {self._cooldown_seconds}s"
                        )
                    return None
                if status == 429:
                    logger.warning("Soundcharts rate limit hit (429)")
                    return None
                if status == 403:
                    logger.warning(f"Soundcharts access denied (403) for {path} — endpoint may require a paid plan")
                    return None
                if status == 404:
                    return None
                raise

        self._consecutive_failures = 0
        return resp.json()

    async def _get(self, path: str, params: dict | None = None) -> Optional[dict]:
        return await self._request("GET", path, params=params)

    async def _post(self, path: str, params: dict | None = None, json_body: dict | None = None) -> Optional[dict]:
        return await self._request("POST", path, params=params, json_body=json_body)

    # ── Discovery ──

    async def get_rising_artists(
        self,
        genre: str,
        limit: int = 50,
        platform: str = "spotify",
        metric_type: str = "followers",
        sort_by: str = "percent",
        period: str = "month",
        career_stage: str | None = None,
        growth_level: str | None = None,
    ) -> list[dict]:
        """Get rising/trending artists filtered by genre.

        Uses POST /api/v2/top/artists — a programmable discovery engine.
        """
        body: dict = {
            "platform": platform,
            "metricType": metric_type,
            "sortBy": sort_by,
            "period": period,
            "order": "desc",
            "limit": limit,
            "offset": 0,
            "filters": [
                {
                    "attribute": "artistGenres",
                    "operator": "in",
                    "value": [genre],
                },
            ],
        }
        if career_stage:
            body["filters"].append({
                "attribute": "careerStage",
                "operator": "in",
                "value": [career_stage],
            })
        if growth_level:
            body["filters"].append({
                "attribute": "growthLevel",
                "operator": "in",
                "value": [growth_level],
            })

        data = await self._post("/api/v2/top/artists", json_body=body)
        if not data:
            return []

        artists = []
        for item in data.get("items", []):
            obj = item.get("object", {})
            artists.append({
                "sc_uuid": obj.get("uuid", ""),
                "name": obj.get("name", ""),
                "slug": obj.get("slug"),
                "image_url": obj.get("imageUrl"),
                "genres": [g.get("name", "") for g in (obj.get("genres") or [])],
                "career_stage": obj.get("careerStage"),
                "growth_level": obj.get("growthLevel"),
                "country_code": obj.get("countryCode"),
            })
        return artists

    async def search_artists(self, query: str, limit: int = 20) -> list[dict]:
        """Search artists by name."""
        data = await self._get(
            f"/api/v2/artist/search/{query}",
            params={"limit": limit},
        )
        if not data:
            return []
        artists = []
        for item in data.get("items", []):
            artists.append({
                "sc_uuid": item.get("uuid", ""),
                "name": item.get("name", ""),
                "slug": item.get("slug"),
                "image_url": item.get("imageUrl"),
                "genres": [g.get("name", "") for g in (item.get("genres") or [])],
                "career_stage": item.get("careerStage"),
                "country_code": item.get("countryCode"),
            })
        return artists

    # ── Artist Profile & IDs ──

    async def get_artist_profile(self, sc_uuid: str) -> Optional[dict]:
        """Get artist profile. Cached 1 hour."""
        now = time.time()
        cached = self._profile_cache.get(sc_uuid)
        if cached and now < cached[0] + self._profile_ttl:
            return cached[1]

        data = await self._get(f"/api/v2/artist/{sc_uuid}")
        if not data:
            return None
        obj = data.get("object", data)
        profile = {
            "sc_uuid": obj.get("uuid", sc_uuid),
            "name": obj.get("name"),
            "slug": obj.get("slug"),
            "image_url": obj.get("imageUrl"),
            "genres": [g.get("name", "") for g in (obj.get("genres") or [])],
            "career_stage": obj.get("careerStage"),
            "growth_level": obj.get("growthLevel"),
            "country_code": obj.get("countryCode"),
            "description": obj.get("biography"),
        }
        self._profile_cache[sc_uuid] = (now, profile)
        return profile

    async def get_artist_by_platform_id(
        self, platform: str, identifier: str
    ) -> Optional[dict]:
        """Look up artist by platform ID (e.g., Spotify ID → Soundcharts UUID).

        If the artist isn't in Soundcharts yet, they're auto-ingested within 2 hours.
        """
        cache_key = f"{platform}:{identifier}"
        now = time.time()
        cached = self._id_cache.get(cache_key)
        if cached and now < cached[0] + self._id_cache_ttl:
            return cached[1]

        data = await self._get(f"/api/v2.9/artist/by-platform/{platform}/{identifier}")
        if not data:
            return None
        obj = data.get("object", data)
        result = {
            "sc_uuid": obj.get("uuid", ""),
            "name": obj.get("name"),
            "slug": obj.get("slug"),
            "image_url": obj.get("imageUrl"),
            "genres": [g.get("name", "") for g in (obj.get("genres") or [])],
        }
        self._id_cache[cache_key] = (now, result)
        return result

    async def get_artist_identifiers(self, sc_uuid: str) -> dict[str, str]:
        """Get all cross-platform IDs for an artist. Returns {platform: identifier}."""
        cache_key = f"ids:{sc_uuid}"
        now = time.time()
        cached = self._id_cache.get(cache_key)
        if cached and now < cached[0] + self._id_cache_ttl:
            return cached[1]

        data = await self._get(f"/api/v2/artist/{sc_uuid}/identifiers")
        if not data:
            return {}
        ids: dict[str, str] = {}
        for item in data.get("items", []):
            platform_code = item.get("platformCode", "")
            identifier = item.get("identifier", "")
            if platform_code and identifier:
                ids[platform_code] = identifier
        self._id_cache[cache_key] = (now, ids)
        return ids

    # ── Time-Series Stats ──

    async def get_audience_stats(
        self,
        sc_uuid: str,
        platform: str,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """Get daily audience (follower) time-series.

        platform: 'spotify', 'youtube', 'tiktok', 'instagram', etc.
        start_date/end_date: 'YYYY-MM-DD' strings.
        """
        all_items: list[dict] = []
        offset = 0
        while True:
            data = await self._get(
                f"/api/v2/artist/{sc_uuid}/audience/{platform}",
                params={
                    "startDate": start_date,
                    "endDate": end_date,
                    "offset": offset,
                    "limit": 100,
                },
            )
            if not data:
                break
            items = data.get("items", [])
            if not items:
                break
            all_items.extend(items)
            if len(items) < 100:
                break
            offset += 100
        return all_items

    async def get_streaming_stats(
        self,
        sc_uuid: str,
        platform: str,
        start_date: str,
        end_date: str,
    ) -> list[dict]:
        """Get daily streaming (listeners/views) time-series.

        platform: 'spotify' (monthly_listeners), 'youtube' (views), etc.
        """
        all_items: list[dict] = []
        offset = 0
        while True:
            data = await self._get(
                f"/api/v2/artist/{sc_uuid}/streaming/{platform}/listening",
                params={
                    "startDate": start_date,
                    "endDate": end_date,
                    "offset": offset,
                    "limit": 100,
                },
            )
            if not data:
                break
            items = data.get("items", [])
            if not items:
                break
            all_items.extend(items)
            if len(items) < 100:
                break
            offset += 100
        return all_items

    async def get_current_stats(self, sc_uuid: str) -> Optional[dict]:
        """Get current stats across all platforms in a single call."""
        return await self._get(f"/api/v2/artist/{sc_uuid}/current/stats")

    # ── Related Artists ──

    async def get_related_artists(self, sc_uuid: str, limit: int = 40) -> list[dict]:
        """Get related artists (based on Spotify 'Fans Also Like')."""
        data = await self._get(
            f"/api/v2/artist/{sc_uuid}/related",
            params={"limit": limit},
        )
        if not data:
            return []
        artists = []
        for item in data.get("items", []):
            artists.append({
                "sc_uuid": item.get("uuid", ""),
                "name": item.get("name", ""),
                "slug": item.get("slug"),
                "image_url": item.get("imageUrl"),
            })
        return artists

    # ── Playlist Monitoring ──

    async def get_playlist_placements(
        self, sc_uuid: str, platform: str = "spotify", placement_type: str = "all"
    ) -> list[dict]:
        """Get current playlist placements for an artist."""
        data = await self._get(
            f"/api/v2.20/artist/{sc_uuid}/playlist/current/{platform}",
            params={"type": placement_type, "currentOnly": 1, "sortBy": "subscriberCount"},
        )
        if not data:
            return []
        return data.get("items", [])
