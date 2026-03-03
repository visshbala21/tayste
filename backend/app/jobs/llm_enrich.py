"""LLM enrichment job: generate label DNA and artist briefs."""
import asyncio
import logging
from sqlalchemy import select
from app.db.session import async_session_factory
from app.models.tables import Label, Recommendation, Artist
from app.llm.label_dna import generate_label_dna
from app.llm.artist_brief import generate_artist_brief

logger = logging.getLogger(__name__)

LLM_DNA_CONCURRENCY = 3
LLM_BRIEF_CONCURRENCY = 5


async def run():
    logger.info("Starting LLM enrichment job...")
    async with async_session_factory() as db:
        # Generate Label DNA for each label (concurrently, semaphore-bounded)
        result = await db.execute(select(Label.id))
        label_ids = [r[0] for r in result.all()]

        dna_sem = asyncio.Semaphore(LLM_DNA_CONCURRENCY)

        async def _generate_dna(lid: str):
            async with dna_sem:
                async with async_session_factory() as task_db:
                    try:
                        logger.info(f"Generating Label DNA for {lid}")
                        await generate_label_dna(task_db, lid)
                        await task_db.commit()
                    except Exception as e:
                        logger.error(f"Label DNA failed for {lid}: {e}")

        await asyncio.gather(
            *[_generate_dna(lid) for lid in label_ids],
            return_exceptions=True,
        )

        # Generate briefs for top recommended candidates per label (concurrently)
        brief_sem = asyncio.Semaphore(LLM_BRIEF_CONCURRENCY)

        async def _generate_brief(artist_id: str, label_id: str):
            async with brief_sem:
                async with async_session_factory() as task_db:
                    try:
                        logger.info(f"Generating brief for artist {artist_id}")
                        await generate_artist_brief(task_db, artist_id, label_id)
                        await task_db.commit()
                    except Exception as e:
                        logger.error(f"Brief failed for {artist_id}: {e}")

        brief_tasks = []
        for lid in label_ids:
            result = await db.execute(
                select(Recommendation).where(Recommendation.label_id == lid)
                .order_by(Recommendation.final_score.desc()).limit(20)
            )
            recs = result.scalars().all()
            for rec in recs:
                brief_tasks.append(_generate_brief(rec.artist_id, lid))

        await asyncio.gather(*brief_tasks, return_exceptions=True)

    logger.info("LLM enrichment complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run())
