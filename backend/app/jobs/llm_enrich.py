"""LLM enrichment job: generate label DNA and artist briefs."""
import asyncio
import logging
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.tables import Label, Recommendation, Artist
from app.llm.label_dna import generate_label_dna
from app.llm.artist_brief import generate_artist_brief

logger = logging.getLogger(__name__)


async def run():
    logger.info("Starting LLM enrichment job...")
    async with async_session_factory() as db:
        # Generate Label DNA for each label
        result = await db.execute(select(Label.id))
        label_ids = [r[0] for r in result.all()]

        for lid in label_ids:
            try:
                logger.info(f"Generating Label DNA for {lid}")
                await generate_label_dna(db, lid)
            except Exception as e:
                logger.error(f"Label DNA failed for {lid}: {e}")

        # Generate briefs for top recommended candidates per label
        for lid in label_ids:
            result = await db.execute(
                select(Recommendation).where(Recommendation.label_id == lid)
                .order_by(Recommendation.final_score.desc()).limit(20)
            )
            recs = result.scalars().all()
            for rec in recs:
                try:
                    logger.info(f"Generating brief for artist {rec.artist_id}")
                    await generate_artist_brief(db, rec.artist_id, lid)
                except Exception as e:
                    logger.error(f"Brief failed for {rec.artist_id}: {e}")

        await db.commit()
    logger.info("LLM enrichment complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
