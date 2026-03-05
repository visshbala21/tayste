"""
Rule-based music-fan sentiment classifier.

Maps comment text to one of: very_positive, positive, neutral, critical, negative.
Handles music/internet slang, ironic emoji usage, and fan language.
No ML dependency — fully deterministic.
"""
import re
from typing import Literal

SentimentLabel = Literal["very_positive", "positive", "neutral", "critical", "negative"]

# ── Very positive: extreme enthusiasm ──
VERY_POSITIVE_PATTERNS = [
    # Slang
    r"\bgoated\b", r"\bmasterpiece\b", r"\bgoat\b", r"\blegendary\b",
    r"\bno\s*skip\b", r"\bon\s*repeat\b", r"\bgoes\s*crazy\b", r"\bgoes\s*hard\b",
    r"\bbro\s*snapped\b", r"\bshe\s*snapped\b", r"\bhe\s*snapped\b", r"\bthey\s*snapped\b",
    r"\bthis\s*is\s*illegal\b", r"\bthis\s*should\s*be\s*illegal\b",
    r"\bate\s*(and\s*left\s*no\s*crumbs|that)\b", r"\bate\b.*\bleft\s*no\s*crumbs\b",
    r"\binsane\b", r"\bcrazyyy+\b", r"\bcrazy\s*good\b",
    r"\bbest\s*(song|album|track|music)\b", r"\bsong\s*of\s*the\s*year\b",
    r"\balbum\s*of\s*the\s*year\b", r"\baoty\b",
    r"\bgeneration(al)?\s*talent\b", r"\bonce\s*in\s*a\s*lifetime\b",
]

# ── Positive: solid approval ──
POSITIVE_PATTERNS = [
    r"\bfire\b", r"\bheat\b", r"\bslaps?\b", r"\bbangs?\b", r"\bbussin\b",
    r"\bhard\b", r"\bclean\b", r"\bsmooth\b", r"\bvibe[sz]?\b",
    r"\bfresh\b", r"\bsick\b", r"\bnasty\b",  # "nasty" in music context = positive
    r"\b(big\s*)?w\b", r"\bdub\b", r"\bvalid\b", r"\bgoated\b",
    r"\blove\s*(this|it|the)\b", r"\bso\s*good\b", r"\breally\s*good\b",
    r"\bamazing\b", r"\bincredible\b", r"\bbeautiful\b", r"\bstunning\b",
    r"\bunderrated\b",  # "underrated" = positive (fan championing)
    r"\btalented\b", r"\bblessing\b", r"\bgifted\b",
    r"\bchills?\b", r"\bgoosebumps\b",
    r"\baddicted\b", r"\bobsessed\b",
    r"\bcan'?t\s*stop\s*(listening|playing|watching)\b",
    r"\bfavorite\b", r"\bfavourite\b",
    r"\bkeep\s*(it\s*)?up\b", r"\bmore\s*(of\s*)?this\b",
    r"\bproduction\s*is\b.*\b(insane|crazy|fire|clean|chef)\b",
    r"\bwho\s*produced\s*this\b",  # engagement signal = positive
]

# ── Critical: disappointment, nostalgia for past work ──
CRITICAL_PATTERNS = [
    r"\blost\s*(their|his|her)\s*sound\b", r"\bsold\s*out\b",
    r"\bmiss\s*the\s*old\b", r"\bnot\s*the\s*same\b",
    r"\bpeaked\b", r"\bdeclining\b", r"\bfell\s*off\b",
    r"\bnot\s*(as\s*good|feeling|it|vibing)\b",
    r"\bused\s*to\s*be\s*(better|good)\b",
    r"\bdisappointing\b", r"\blet\s*(me\s*)?down\b",
    r"\bexpected\s*(more|better)\b",
    r"\bmeh\b", r"\bokay\s*at\s*best\b",
    r"\b(kinda|kind\s*of)\s*(mid|boring|meh)\b",
]

# ── Negative: strong disapproval ──
NEGATIVE_PATTERNS = [
    r"\bmid\b", r"\btrash\b", r"\bgarbage\b", r"\bterrible\b",
    r"\bawful\b", r"\bhorrible\b", r"\bworst\b",
    r"\b(big\s*)?l\b", r"\bflop\b", r"\bskip\b",
    r"\boverrated\b", r"\boverhyped\b",
    r"\bboring\b", r"\bgeneric\b", r"\bbasic\b",
    r"\bno\s*talent\b", r"\btalentless\b",
    r"\bwack\b", r"\bcorny\b", r"\bcheesy\b",
    r"\bcan'?t\s*stand\b", r"\bunlistenable\b",
]

# ── Emoji patterns ──
VERY_POSITIVE_EMOJI = {"🔥🔥", "🔥🔥🔥", "💯💯", "🐐", "👑"}
POSITIVE_EMOJI = {"🔥", "💯", "❤️", "😍", "🥰", "💜", "💙", "🖤", "✨", "⭐", "🙌", "👏", "💪", "🤩", "😭🔥", "💀🔥"}
NEGATIVE_EMOJI = {"👎", "🗑️", "💩", "🤮", "😴"}

# Ironic-positive combos: crying/skull + fire/positive context
IRONIC_POSITIVE_EMOJI_PAIRS = [
    ({"😭", "💀", "☠️"}, {"🔥", "💯", "❤️", "🙌", "👏", "✨"}),
]


def _extract_emojis(text: str) -> set[str]:
    """Extract emoji characters from text."""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U0001F900-\U0001F9FF"  # supplemental
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002600-\U000026FF"
        "\U0000FE00-\U0000FE0F"
        "]+",
        flags=re.UNICODE,
    )
    return set(emoji_pattern.findall(text))


def _check_emoji_patterns(text: str) -> SentimentLabel | None:
    emojis = _extract_emojis(text)
    if not emojis:
        return None

    emoji_str = "".join(sorted(emojis))

    # Check ironic positive: crying/skull + fire/positive
    for neg_set, pos_set in IRONIC_POSITIVE_EMOJI_PAIRS:
        if emojis & neg_set and emojis & pos_set:
            return "very_positive"

    # Check multi-emoji combos
    for pattern in VERY_POSITIVE_EMOJI:
        if pattern in text:
            return "very_positive"

    # Check single positive emoji
    if emojis & POSITIVE_EMOJI:
        return "positive"

    if emojis & NEGATIVE_EMOJI:
        return "negative"

    return None


def classify_comment(text: str) -> SentimentLabel:
    """Classify a single comment into a sentiment bucket."""
    if not text or not text.strip():
        return "neutral"

    lower = text.lower().strip()

    # Check very positive patterns first
    for pattern in VERY_POSITIVE_PATTERNS:
        if re.search(pattern, lower):
            return "very_positive"

    # Check negative before positive (avoid "not good" → "good" match)
    for pattern in NEGATIVE_PATTERNS:
        if re.search(pattern, lower):
            return "negative"

    # Check critical
    for pattern in CRITICAL_PATTERNS:
        if re.search(pattern, lower):
            return "critical"

    # Check positive
    for pattern in POSITIVE_PATTERNS:
        if re.search(pattern, lower):
            return "positive"

    # Emoji-based fallback
    emoji_result = _check_emoji_patterns(text)
    if emoji_result:
        return emoji_result

    # ALL CAPS with >5 chars often = enthusiasm in music comments
    if len(lower) > 5 and text == text.upper() and any(c.isalpha() for c in text):
        return "positive"

    return "neutral"


def classify_batch(comments: list[str]) -> dict[str, int]:
    """Classify a batch of comments and return sentiment counts."""
    counts = {
        "very_positive": 0,
        "positive": 0,
        "neutral": 0,
        "critical": 0,
        "negative": 0,
    }
    for comment in comments:
        label = classify_comment(comment)
        counts[label] += 1
    return counts
