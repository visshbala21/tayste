"""Shared emerging-artist eligibility rules used across discovery and ranking."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from app.config import get_settings

EMERGING_STAGE_KEYWORDS = {
    "emerging",
    "developing",
    "breakthrough",
    "breaking",
    "newcomer",
}

MAINSTREAM_STAGE_KEYWORDS = {
    "mainstream",
    "established",
    "superstar",
    "legend",
    "legacy",
    "icon",
    "major",
    "global",
}

MAINSTREAM_BIO_PATTERNS = [
    re.compile(r"\bgrammy\b", re.IGNORECASE),
    re.compile(r"\bbillboard\s+hot\s*100\b", re.IGNORECASE),
    re.compile(r"\bmulti[-\s]?platinum\b", re.IGNORECASE),
    re.compile(r"\bplatinum\b", re.IGNORECASE),
    re.compile(r"\bchart[-\s]?topping\b", re.IGNORECASE),
    re.compile(r"\baward[-\s]?winning\b", re.IGNORECASE),
    re.compile(r"\bsigned to (sony|universal|warner)\b", re.IGNORECASE),
]


def _clean(value: str | None) -> str:
    return (value or "").strip().lower()


def _int_or_none(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _float_or_none(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_non_null(values: Iterable[int | float | None]):
    for value in values:
        if value is not None:
            return value
    return None


@dataclass(frozen=True)
class EmergingSignals:
    name: str | None = None
    bio: str | None = None
    career_stage: str | None = None
    spotify_followers: int | None = None
    spotify_popularity: int | None = None
    total_followers: int | None = None
    growth_7d: float | None = None
    growth_30d: float | None = None
    momentum_score: float | None = None


@dataclass(frozen=True)
class EmergingDecision:
    is_emerging: bool
    reasons: tuple[str, ...]


def evaluate_emerging_artist(signals: EmergingSignals, strict: bool = True) -> EmergingDecision:
    """Classify whether an artist should remain in the emerging-only funnel.

    strict=False is used in discovery (allow unknowns unless hard mainstream signals exist).
    strict=True is used in ranking (require at least one positive emerging signal).
    """
    settings = get_settings()
    hard_fail: list[str] = []
    positive: list[str] = []

    stage = _clean(signals.career_stage)
    if stage:
        if any(token in stage for token in MAINSTREAM_STAGE_KEYWORDS):
            hard_fail.append(f"career_stage:{stage}")
        if any(token in stage for token in EMERGING_STAGE_KEYWORDS):
            positive.append(f"career_stage:{stage}")

    bio = signals.bio or ""
    if bio:
        for pattern in MAINSTREAM_BIO_PATTERNS:
            if pattern.search(bio):
                hard_fail.append(f"bio_pattern:{pattern.pattern}")
                break

    spotify_followers = _int_or_none(signals.spotify_followers)
    spotify_popularity = _int_or_none(signals.spotify_popularity)
    total_followers = _int_or_none(
        _first_non_null([signals.total_followers, spotify_followers])
    )
    growth_7d = _float_or_none(signals.growth_7d)
    growth_30d = _float_or_none(signals.growth_30d)
    momentum = _float_or_none(signals.momentum_score)

    if spotify_followers is not None:
        if spotify_followers > settings.emerging_max_spotify_followers:
            hard_fail.append(f"spotify_followers:{spotify_followers}")
        elif spotify_followers <= int(settings.emerging_max_spotify_followers * 0.6):
            positive.append("spotify_followers_below_cap")
    if spotify_popularity is not None:
        if spotify_popularity > settings.emerging_max_spotify_popularity:
            hard_fail.append(f"spotify_popularity:{spotify_popularity}")
        elif spotify_popularity <= int(settings.emerging_max_spotify_popularity * 0.8):
            positive.append("spotify_popularity_below_cap")
    if total_followers is not None and total_followers > settings.emerging_max_followers:
        hard_fail.append(f"total_followers:{total_followers}")

    if growth_7d is not None and growth_7d >= settings.emerging_min_growth_7d:
        positive.append("growth_7d")
    if growth_30d is not None and growth_30d >= settings.emerging_min_growth_30d:
        positive.append("growth_30d")
    if momentum is not None and momentum >= settings.emerging_min_momentum:
        positive.append("momentum")

    if hard_fail:
        return EmergingDecision(is_emerging=False, reasons=tuple(hard_fail))
    if not strict:
        return EmergingDecision(is_emerging=True, reasons=tuple(positive or ["no_hard_mainstream_signal"]))
    if positive:
        return EmergingDecision(is_emerging=True, reasons=tuple(positive))
    return EmergingDecision(is_emerging=False, reasons=("insufficient_emerging_signal",))


def evaluate_open_mode(signals: EmergingSignals) -> EmergingDecision:
    """Open-mode evaluation: allow all artists unless they fail the slop name filter.

    Skips career stage gates, follower/popularity caps, and bio pattern matching.
    Only rejects names that look like playlists, compilations, or genre pages.
    """
    from app.jobs.discover import is_likely_slop

    if is_likely_slop(signals.name):
        return EmergingDecision(is_emerging=False, reasons=("slop_name_filter",))
    return EmergingDecision(is_emerging=True, reasons=("open_mode",))
