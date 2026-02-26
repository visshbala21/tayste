import re

YOUTUBE_CHANNEL_RE = re.compile(r"youtube\.com/channel/(UC[a-zA-Z0-9_-]{20,})", re.IGNORECASE)
YOUTUBE_HANDLE_RE = re.compile(r"youtube\.com/@([a-zA-Z0-9._-]+)", re.IGNORECASE)
SPOTIFY_ARTIST_RE = re.compile(r"open\.spotify\.com/artist/([a-zA-Z0-9]+)", re.IGNORECASE)
SPOTIFY_URI_RE = re.compile(r"spotify:artist:([a-zA-Z0-9]+)", re.IGNORECASE)
TIKTOK_HANDLE_RE = re.compile(r"tiktok\.com/@([a-zA-Z0-9._-]+)", re.IGNORECASE)
SOUNDCHARTS_ARTIST_RE = re.compile(r"soundcharts\.com/(?:en/)?artist/([a-f0-9-]{36}|[a-z0-9-]+)", re.IGNORECASE)


def detect_platform_from_url(url: str) -> str | None:
    if not url:
        return None
    u = url.lower()
    if "soundcharts.com" in u:
        return "soundcharts"
    if "youtube.com" in u or "youtu.be" in u:
        return "youtube"
    if "spotify.com" in u or u.startswith("spotify:"):
        return "spotify"
    if "tiktok.com" in u:
        return "tiktok"
    return None


def extract_platform_id(platform: str, url: str) -> str | None:
    if not platform or not url:
        return None

    if platform == "soundcharts":
        match = SOUNDCHARTS_ARTIST_RE.search(url)
        if match:
            return match.group(1)
        return None

    if platform == "youtube":
        match = YOUTUBE_CHANNEL_RE.search(url)
        if match:
            return match.group(1)
        handle_match = YOUTUBE_HANDLE_RE.search(url)
        if handle_match:
            return f"@{handle_match.group(1)}"
        return None

    if platform == "spotify":
        match = SPOTIFY_ARTIST_RE.search(url)
        if match:
            return match.group(1)
        match = SPOTIFY_URI_RE.search(url)
        if match:
            return match.group(1)
        return None

    if platform == "tiktok":
        match = TIKTOK_HANDLE_RE.search(url)
        if match:
            return f"@{match.group(1)}"
        return None

    return None
