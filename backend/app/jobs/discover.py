"""Discovery job: find new candidate artists."""
import asyncio
import logging
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.tables import Label, Artist, PlatformAccount, RosterMembership
from app.models.base import new_uuid
import re
from app.connectors.youtube import YouTubeConnector
from app.connectors.spotify import SpotifyConnector
from app.llm.label_dna import generate_label_dna
from app.llm.query_expansion import expand_queries
from app.api.schemas import LabelDNAOutput

logger = logging.getLogger(__name__)

BAD_NAME_PATTERNS = [
    r"\b(music for|music to|music with)\b",
    r"\b(study|focus|deep focus|concentration)\b",
    r"\b(background music|ambient music|sleep music|meditation music)\b",
    r"\b(relax|relaxing|calm|chill vibes|chill beats)\b",
    r"\b(white noise|rain sounds|ocean sounds)\b",
    r"\b(work music|office music|productivity)\b",
    r"\b(instrumental music|lofi)\b",
    r"\b(podcast|episode|interview|review|reaction)\b",
    r"\b(best of|top \d|greatest hits|compilation)\b",
    r"\b(lyrics|lyric video|official video|music video)\b",
    r"\b(playlist|mix|mixtape|radio)\b",
]

# Genre names and descriptors that are NOT artist names
GENRE_PATTERNS = [
    # Broad genres
    r"^(hip hop|hip-hop|rap|r&b|rnb|rock|pop|jazz|blues|soul|funk|country|metal|punk|reggae|ska|gospel|classical|electronic|edm|techno|house|trance|dubstep|dnb|drum and bass|ambient|folk|indie|alternative|grunge|emo)$",
    # Sub-genres and compound genres
    r"^(g[- ]?funk|trap|drill|boom bap|lo-?fi|synth-?pop|post-?punk|dream pop|shoegaze|new wave|dark-?wave|vapor-?wave|math rock|prog rock|death metal|black metal|nu metal|hard rock|soft rock|acid jazz|smooth jazz|neo[- ]?soul|trip[- ]?hop|uk garage|grime|afrobeats|dancehall|bossa nova|latin pop|k-?pop|j-?pop)$",
    # Era/descriptor + genre combos
    r"^\d{2}s\s+(hip hop|rap|rock|pop|r&b|soul|funk|jazz|metal|punk)",
    r"^(new|old|classic|modern|underground|mainstream|alternative|experimental|progressive|traditional)\s+(hip hop|rap|rock|pop|r&b|soul|funk|jazz|metal|punk|music)",
    # Genre with qualifiers
    r"(hip hop|rap|rock|pop|r&b|rnb|soul|funk|jazz|blues|metal|punk|reggae).*(lyrics|songs|tracks|beats|instrumentals|remixes|samples|vibes|music|radio|mix)",
    r"^(west coast|east coast|south|midwest|dirty south|southern)\s+(rap|hip hop|hip-hop)$",
    # Slash/semicolon separated genres
    r"^[a-zA-Z&\s]+[/;][a-zA-Z&\s]+$",
]


def is_likely_slop(name: str) -> bool:
    """Check if a name is likely not a real artist (genre, playlist, podcast, etc.)."""
    if not name:
        return True
    lower = name.strip().lower()
    if len(lower) > 60:
        return True
    if lower.count(",") >= 3:
        return True
    # Single word names under 3 chars are suspicious
    if len(lower) < 3 and " " not in lower:
        return True
    for pat in BAD_NAME_PATTERNS:
        if re.search(pat, lower):
            return True
    for pat in GENRE_PATTERNS:
        if re.search(pat, lower, re.IGNORECASE):
            return True
    return False


async def discover_for_label(db, label_id: str):
    """Discover candidate artists for a label."""
    label = await db.get(Label, label_id)
    if not label:
        return

    # Get or generate label DNA
    label_dna = None
    if label.label_dna:
        try:
            dna_data = {k: v for k, v in label.label_dna.items() if not k.startswith("_")}
            label_dna = LabelDNAOutput.model_validate(dna_data)
        except Exception:
            pass

    if not label_dna:
        label_dna = await generate_label_dna(db, label_id)

    if not label_dna:
        logger.warning(f"No label DNA for {label_id}, using default queries")
        queries = [f"{label.name} emerging artists", f"{label.name} new music"]
    else:
        expanded = expand_queries(label_dna, label.name)
        queries = expanded.youtube_queries[:5]

    yt = YouTubeConnector()
    spotify = SpotifyConnector()
    discovered = 0
    yt_disabled = False
    yt_budget = 5
    yt_used = 0
    spotify_budget = 25
    spotify_used = 0
    max_candidates = 60

    for query in queries:
        if discovered >= max_candidates:
            break
        if yt.available and not yt_disabled and yt_used < yt_budget:
            try:
                channels = await yt.search_channels(query, max_results=3)
            except Exception as e:
                msg = str(e)
                if "400" in msg or "403" in msg or "Forbidden" in msg or "429" in msg:
                    yt_disabled = True
                    channels = []
                else:
                    channels = []
            for ch in channels:
                if is_likely_slop(ch.get("name") or ""):
                    continue
                # Check if already exists
                result = await db.execute(
                    select(PlatformAccount).where(
                        PlatformAccount.platform == "youtube",
                        PlatformAccount.platform_id == ch["platform_id"],
                    )
                )
                if result.scalar_one_or_none():
                    continue

                artist = Artist(
                    id=new_uuid(), name=ch["name"], bio=ch.get("description"),
                    image_url=ch.get("image_url"), is_candidate=True,
                )
                db.add(artist)
                await db.flush()

                account = PlatformAccount(
                    id=new_uuid(), artist_id=artist.id, platform="youtube",
                    platform_id=ch["platform_id"],
                    platform_url=ch.get("platform_url"),
                )
                db.add(account)
                discovered += 1
            yt_used += 1

        if spotify.available and spotify_used < spotify_budget and discovered < max_candidates:
            try:
                results = await spotify.search_artists(query, limit=5)
            except Exception:
                results = []
            spotify_used += 1
            for ch in results:
                if discovered >= max_candidates:
                    break
                if not ch.get("platform_id"):
                    continue
                if is_likely_slop(ch.get("name") or ""):
                    continue
                popularity = ch.get("popularity") or 0
                followers = ch.get("followers") or 0
                # Require meaningful Spotify presence — real artists have
                # followers and popularity; genre pages and compilations don't
                if followers < 500 or popularity < 5:
                    continue
                # No genres on Spotify usually means it's not a real artist
                if not ch.get("genres"):
                    continue
                # Skip if already exists by name
                existing_by_name = await db.execute(
                    select(Artist).where(Artist.name == ch["name"])
                )
                if existing_by_name.scalar_one_or_none():
                    continue
                # Check if already exists
                result = await db.execute(
                    select(PlatformAccount).where(
                        PlatformAccount.platform == "spotify",
                        PlatformAccount.platform_id == ch["platform_id"],
                    )
                )
                if result.scalar_one_or_none():
                    continue

                artist = Artist(
                    id=new_uuid(),
                    name=ch["name"],
                    bio=ch.get("description"),
                    image_url=ch.get("image_url"),
                    genre_tags=ch.get("genres") or [],
                    is_candidate=True,
                )
                db.add(artist)
                await db.flush()

                account = PlatformAccount(
                    id=new_uuid(),
                    artist_id=artist.id,
                    platform="spotify",
                    platform_id=ch["platform_id"],
                    platform_url=ch.get("platform_url"),
                )
                db.add(account)
                discovered += 1

    await db.flush()
    logger.info(f"Discovered {discovered} new candidates for label {label.name}")

    if discovered == 0:
        logger.warning(f"No candidates discovered for label {label.name} — all connectors returned empty")


async def run():
    logger.info("Starting discovery job...")
    async with async_session_factory() as db:
        result = await db.execute(select(Label.id))
        label_ids = [r[0] for r in result.all()]
        for lid in label_ids:
            try:
                await discover_for_label(db, lid)
            except Exception as e:
                logger.error(f"Discovery failed for label {lid}: {e}")
        await db.commit()
    logger.info("Discovery complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
