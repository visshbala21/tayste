"""Secondary discovery: expand candidate pool via Spotify related-artists graph."""
import asyncio
import logging
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.tables import Label, Artist, PlatformAccount, RosterMembership
from app.models.base import new_uuid
from app.connectors.spotify import SpotifyConnector
from app.connectors.soundcharts import SoundchartsConnector
from app.jobs.discover import is_likely_slop

logger = logging.getLogger(__name__)


async def pull_graph_for_label(db, label_id: str):
    """Discover candidates via related-artists graph for a label's roster."""
    label = await db.get(Label, label_id)
    if not label:
        return

    spotify = SpotifyConnector()
    if not spotify.available:
        logger.info(f"Spotify unavailable, skipping graph expansion for {label.name}")
        return

    # Get roster artists with Spotify accounts
    result = await db.execute(
        select(PlatformAccount.platform_id, PlatformAccount.artist_id)
        .join(RosterMembership, RosterMembership.artist_id == PlatformAccount.artist_id)
        .where(
            RosterMembership.label_id == label_id,
            RosterMembership.is_active == True,
            PlatformAccount.platform == "spotify",
        )
    )
    roster_spotify = result.all()

    if not roster_spotify:
        logger.info(f"No roster artists with Spotify accounts for {label.name}")
        return

    sc = SoundchartsConnector()
    discovered = 0
    seen_spotify_ids: set[str] = set()

    for spotify_id, _roster_artist_id in roster_spotify:
        try:
            related = await spotify.get_related_artists(spotify_id)
        except Exception as e:
            logger.warning(f"Failed to get related artists for {spotify_id}: {e}")
            continue

        for artist_data in related:
            sp_id = artist_data.get("platform_id")
            name = artist_data.get("name", "")
            if not sp_id or not name:
                continue
            if sp_id in seen_spotify_ids:
                continue
            seen_spotify_ids.add(sp_id)

            if is_likely_slop(name):
                continue

            # Skip if already exists
            existing = await db.execute(
                select(PlatformAccount).where(
                    PlatformAccount.platform == "spotify",
                    PlatformAccount.platform_id == sp_id,
                )
            )
            if existing.scalar_one_or_none():
                continue

            # Also skip if artist name already exists (fuzzy dedup)
            existing_name = await db.execute(
                select(Artist).where(Artist.name == name)
            )
            if existing_name.scalar_one_or_none():
                continue

            # Create artist
            artist = Artist(
                id=new_uuid(),
                name=name,
                image_url=artist_data.get("image_url"),
                genre_tags=artist_data.get("genres") or [],
                is_candidate=True,
            )
            db.add(artist)
            await db.flush()

            # Create Spotify platform account
            sp_account = PlatformAccount(
                id=new_uuid(),
                artist_id=artist.id,
                platform="spotify",
                platform_id=sp_id,
                platform_url=artist_data.get("platform_url"),
            )
            db.add(sp_account)

            # Optionally cross-reference with Soundcharts
            if sc.available:
                try:
                    sc_artist = await sc.get_artist_by_platform_id("spotify", sp_id)
                    if sc_artist and sc_artist.get("sc_uuid"):
                        sc_account = PlatformAccount(
                            id=new_uuid(),
                            artist_id=artist.id,
                            platform="soundcharts",
                            platform_id=sc_artist["sc_uuid"],
                            platform_url=f"https://app.soundcharts.com/app/artist/{sc_artist.get('slug') or sc_artist['sc_uuid']}",
                        )
                        db.add(sc_account)
                except Exception as e:
                    logger.debug(f"SC cross-ref failed for spotify:{sp_id}: {e}")

            discovered += 1

    await db.flush()
    logger.info(f"Discovered {discovered} candidates via Spotify graph for label {label.name}")


async def run():
    logger.info("Starting Spotify graph discovery...")
    async with async_session_factory() as db:
        result = await db.execute(select(Label.id))
        label_ids = [r[0] for r in result.all()]
        for lid in label_ids:
            try:
                await pull_graph_for_label(db, lid)
            except Exception as e:
                logger.error(f"Spotify graph discovery failed for label {lid}: {e}")
        await db.commit()
    logger.info("Spotify graph discovery complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
