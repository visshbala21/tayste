"""Broad genre-based discovery via Spotify search.

Complements the related-artist graph walk by searching Spotify for artists
matching the label's genre tags.  Pre-filters by follower count and popularity
so only emerging-scale artists enter the candidate pool.
"""
import asyncio
import logging
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.tables import Label, Artist, PlatformAccount, RosterMembership
from app.models.base import new_uuid
from app.connectors.spotify import SpotifyConnector
from app.jobs.discover import is_likely_slop
from app.services.emerging import EmergingSignals, evaluate_emerging_artist

logger = logging.getLogger(__name__)

MAX_CANDIDATES_PER_LABEL = 60
MAX_FOLLOWERS = 150_000
MAX_POPULARITY = 45


async def _genre_search_for_label(db, spotify: SpotifyConnector, label_id: str):
    label = await db.get(Label, label_id)
    if not label:
        return

    genre_tags = label.genre_tags or {}
    primary = genre_tags.get("primary") or []
    secondary = genre_tags.get("secondary") or []
    genres = list(dict.fromkeys(primary + secondary))  # dedupe, preserve order

    if not genres:
        logger.info(f"No genre tags for label {label.name}, skipping genre search")
        return

    discovered = 0
    seen_spotify_ids: set[str] = set()

    for genre in genres:
        if discovered >= MAX_CANDIDATES_PER_LABEL:
            break

        query = f'genre:"{genre}"'
        try:
            results = await spotify.search_artists(query, limit=50)
        except Exception as e:
            logger.warning(f"Spotify genre search failed for '{genre}': {e}")
            continue

        for artist_data in results:
            if discovered >= MAX_CANDIDATES_PER_LABEL:
                break

            sp_id = artist_data.get("platform_id")
            name = artist_data.get("name", "")
            if not sp_id or not name:
                continue
            if sp_id in seen_spotify_ids:
                continue
            seen_spotify_ids.add(sp_id)

            followers = artist_data.get("followers") or 0
            popularity = artist_data.get("popularity") or 0
            if followers > MAX_FOLLOWERS:
                continue
            if popularity > MAX_POPULARITY:
                continue

            if is_likely_slop(name):
                continue

            emerging = evaluate_emerging_artist(
                EmergingSignals(
                    name=name,
                    spotify_followers=followers,
                    spotify_popularity=popularity,
                    total_followers=followers,
                ),
                strict=False,
            )
            if not emerging.is_emerging:
                continue

            # Dedup: skip if Spotify account already exists
            existing = await db.execute(
                select(PlatformAccount).where(
                    PlatformAccount.platform == "spotify",
                    PlatformAccount.platform_id == sp_id,
                )
            )
            if existing.scalar_one_or_none():
                continue

            # Dedup: skip if artist name already exists
            existing_name = await db.execute(
                select(Artist).where(Artist.name == name)
            )
            if existing_name.scalar_one_or_none():
                continue

            artist = Artist(
                id=new_uuid(),
                name=name,
                bio=artist_data.get("description"),
                image_url=artist_data.get("image_url"),
                genre_tags=artist_data.get("genres") or [],
                is_candidate=True,
            )
            db.add(artist)
            await db.flush()

            db.add(PlatformAccount(
                id=new_uuid(),
                artist_id=artist.id,
                platform="spotify",
                platform_id=sp_id,
                platform_url=artist_data.get("platform_url"),
                platform_metadata={
                    "followers": followers,
                    "popularity": popularity,
                    "genres": artist_data.get("genres") or [],
                    "emerging_reasons": list(emerging.reasons),
                    "discovery_source": "genre_search",
                },
            ))

            discovered += 1

    await db.flush()
    logger.info(f"Genre search discovered {discovered} candidates for label {label.name}")


async def run():
    logger.info("Starting Spotify genre-based discovery...")
    spotify = SpotifyConnector()
    if not spotify.available:
        logger.warning("Spotify connector not available, skipping genre search")
        return

    async with async_session_factory() as db:
        result = await db.execute(select(Label.id))
        label_ids = [r[0] for r in result.all()]
        for lid in label_ids:
            try:
                await _genre_search_for_label(db, spotify, lid)
            except Exception as e:
                logger.error(f"Genre search failed for label {lid}: {e}")
        await db.commit()
    logger.info("Spotify genre-based discovery complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
