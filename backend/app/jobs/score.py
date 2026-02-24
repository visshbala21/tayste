"""Scoring job: compute features, cluster, and rank."""
import asyncio
import logging
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.tables import Label, RosterMembership
from app.ranking.features import compute_all_candidate_features, compute_artist_features
from app.ranking.engine import rank_candidates
from app.services.embeddings import cluster_label_artists, ensure_fallback_embeddings

logger = logging.getLogger(__name__)


async def run():
    logger.info("Starting scoring job...")
    async with async_session_factory() as db:
        # Compute features for all roster artists
        result = await db.execute(select(RosterMembership.artist_id).distinct())
        roster_ids = [r[0] for r in result.all()]
        logger.info(f"Computing features for {len(roster_ids)} roster artists")
        for aid in roster_ids:
            try:
                await compute_artist_features(db, aid)
            except Exception as e:
                logger.error(f"Feature computation failed for {aid}: {e}")

        # Compute features for all candidates
        logger.info("Computing features for candidate artists")
        await compute_all_candidate_features(db)

        # Ensure embeddings exist for all artists (fallback if no metrics)
        await ensure_fallback_embeddings(db, roster_ids)
        # Also ensure candidate embeddings
        from app.models.tables import Artist
        result = await db.execute(select(Artist.id).where(Artist.is_candidate == True))
        candidate_ids = [r[0] for r in result.all()]
        await ensure_fallback_embeddings(db, candidate_ids)

        # Cluster and rank for each label
        result = await db.execute(select(Label.id))
        label_ids = [r[0] for r in result.all()]

        for lid in label_ids:
            try:
                logger.info(f"Clustering label {lid}")
                await cluster_label_artists(db, lid)

                logger.info(f"Ranking candidates for label {lid}")
                recs = await rank_candidates(db, lid)
                logger.info(f"Generated {len(recs)} recommendations for label {lid}")
            except Exception as e:
                logger.error(f"Scoring failed for label {lid}: {e}")

        await db.commit()
    logger.info("Scoring complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
