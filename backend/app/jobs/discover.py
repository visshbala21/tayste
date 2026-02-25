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
from app.connectors.soundcloud import SoundCloudConnector
from app.llm.label_dna import generate_label_dna
from app.llm.query_expansion import expand_queries
from app.llm.candidate_suggestions import generate_candidate_suggestions
from app.api.schemas import LabelDNAOutput

logger = logging.getLogger(__name__)

BAD_NAME_PATTERNS = [
    r"\b(music for|music to|music with)\b",
    r"\b(study|focus|deep focus|concentration)\b",
    r"\b(background music|ambient music|sleep music|meditation music)\b",
    r"\b(relax|relaxing|calm|chill)\b",
    r"\b(white noise|rain sounds|ocean sounds)\b",
    r"\b(work music|office music|productivity)\b",
    r"\b(instrumental music|lofi)\b",
]


def is_likely_slop(name: str) -> bool:
    if not name:
        return True
    lower = name.lower()
    if len(lower) > 60:
        return True
    if lower.count(",") >= 3:
        return True
    for pat in BAD_NAME_PATTERNS:
        if re.search(pat, lower):
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
    soundcloud = SoundCloudConnector()
    discovered = 0
    yt_disabled = False
    yt_budget = 5
    yt_used = 0
    spotify_budget = 25
    spotify_used = 0
    soundcloud_budget = 20
    soundcloud_used = 0
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
                popularity = ch.get("popularity")
                followers = ch.get("followers")
                if popularity is not None and followers is not None:
                    if popularity < 10 and followers < 1000:
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

        if soundcloud.available and soundcloud_used < soundcloud_budget and discovered < max_candidates:
            try:
                sc_results = await soundcloud.search_users(query, limit=5)
            except Exception:
                sc_results = []
            soundcloud_used += 1
            for ch in sc_results:
                if discovered >= max_candidates:
                    break
                if not ch.get("platform_id"):
                    continue
                name = ch.get("name") or ""
                if is_likely_slop(name):
                    continue
                followers = ch.get("followers")
                track_count = ch.get("track_count")
                if followers is not None and track_count is not None:
                    if followers < 100 and track_count < 3:
                        continue
                # Skip if already exists by name
                existing_by_name = await db.execute(
                    select(Artist).where(Artist.name == name)
                )
                if existing_by_name.scalar_one_or_none():
                    continue
                # Check if already exists
                result = await db.execute(
                    select(PlatformAccount).where(
                        PlatformAccount.platform == "soundcloud",
                        PlatformAccount.platform_id == ch.get("platform_id"),
                    )
                )
                if result.scalar_one_or_none():
                    continue

                genre_tags = []
                if ch.get("genre"):
                    genre_tags.append(ch["genre"])
                tag_list = ch.get("tag_list")
                if tag_list:
                    if isinstance(tag_list, str):
                        genre_tags.extend([t for t in tag_list.split() if t])
                    elif isinstance(tag_list, list):
                        genre_tags.extend(tag_list)

                artist = Artist(
                    id=new_uuid(),
                    name=name,
                    bio=ch.get("description"),
                    image_url=ch.get("image_url"),
                    genre_tags=genre_tags,
                    is_candidate=True,
                )
                db.add(artist)
                await db.flush()

                account = PlatformAccount(
                    id=new_uuid(),
                    artist_id=artist.id,
                    platform="soundcloud",
                    platform_id=ch.get("platform_id") or "",
                    platform_url=ch.get("platform_url"),
                    platform_metadata={
                        "soundcloud_handle": ch.get("handle"),
                    },
                )
                db.add(account)
                discovered += 1

    await db.flush()
    logger.info(f"Discovered {discovered} new candidates for label {label.name}")

    # Fallback: if nothing discovered, generate candidates via LLM
    if discovered == 0:
        roster_result = await db.execute(
            select(Artist.name).join(RosterMembership).where(
                RosterMembership.label_id == label_id,
                RosterMembership.is_active == True,
            )
        )
        roster_names = [r[0] for r in roster_result.all()]
        suggestions = generate_candidate_suggestions(
            label.name,
            label.description,
            label.genre_tags or {},
            roster_names,
            limit=10,
        )
        if suggestions and suggestions.candidates:
            for s in suggestions.candidates:
                # Skip if already exists by name
                existing = await db.execute(
                    select(Artist).where(Artist.name == s.name)
                )
                if existing.scalar_one_or_none():
                    continue
                artist = Artist(
                    id=new_uuid(),
                    name=s.name,
                    genre_tags=s.genres,
                    bio="Generated candidate (no platform data)",
                    is_candidate=True,
                )
                db.add(artist)
                discovered += 1
            await db.flush()
            logger.info(f"Generated {discovered} fallback candidates for label {label.name}")


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
