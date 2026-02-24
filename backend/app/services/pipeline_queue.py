import asyncio
import logging
from datetime import datetime

from sqlalchemy import update

from app.db.session import async_session_factory
from app.models.tables import Label
from app.jobs import ingest as ingest_job
from app.jobs import discover as discover_job
from app.jobs import score as score_job
from app.jobs import llm_enrich as llm_job

logger = logging.getLogger(__name__)


class PipelineQueue:
    def __init__(self):
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._current_task: asyncio.Task | None = None
        self._current_label_id: str | None = None
        self._lock = asyncio.Lock()

    def start(self):
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._worker())

    async def enqueue(self, label_id: str, replace: bool = False):
        async with self._lock:
            if replace:
                await self._cancel_current_locked()
                await self._clear_queue_locked()
            await self._queue.put(label_id)
            await self._set_status(label_id, "queued")

    async def cancel(self, label_id: str) -> bool:
        async with self._lock:
            canceled = False
            if self._current_label_id == label_id and self._current_task and not self._current_task.done():
                self._current_task.cancel()
                canceled = True

            removed = await self._remove_from_queue_locked(label_id)
            if removed:
                canceled = True
                await self._set_status(label_id, "canceled", completed_at=datetime.utcnow())

            return canceled

    async def _worker(self):
        while True:
            label_id = await self._queue.get()
            self._current_label_id = label_id
            self._current_task = asyncio.create_task(self._run_pipeline(label_id))
            try:
                await self._current_task
            except asyncio.CancelledError:
                # Current task cancellation is handled inside _run_pipeline
                pass
            finally:
                self._current_task = None
                self._current_label_id = None
                self._queue.task_done()

    async def _run_pipeline(self, label_id: str):
        await self._set_status(label_id, "running", started_at=datetime.utcnow())
        try:
            await ingest_job.run()
            await discover_job.run()
            await score_job.run()
            await llm_job.run()
            await self._set_status(label_id, "complete", completed_at=datetime.utcnow())
        except asyncio.CancelledError:
            await self._set_status(label_id, "canceled", completed_at=datetime.utcnow())
            raise
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            await self._set_status(label_id, "error", completed_at=datetime.utcnow())

    async def _cancel_current_locked(self):
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()

    async def _clear_queue_locked(self):
        drained: list[str] = []
        while not self._queue.empty():
            try:
                drained.append(self._queue.get_nowait())
                self._queue.task_done()
            except asyncio.QueueEmpty:
                break
        if drained:
            now = datetime.utcnow()
            async with async_session_factory() as db:
                await db.execute(
                    update(Label)
                    .where(Label.id.in_(drained))
                    .values(pipeline_status="canceled", pipeline_completed_at=now)
                )
                await db.commit()

    async def _remove_from_queue_locked(self, label_id: str) -> bool:
        removed = False
        keep: list[str] = []
        while not self._queue.empty():
            try:
                item = self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            if item == label_id and not removed:
                removed = True
                self._queue.task_done()
            else:
                keep.append(item)
                self._queue.task_done()
        for item in keep:
            await self._queue.put(item)
        return removed

    async def _set_status(
        self,
        label_id: str,
        status: str,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ):
        async with async_session_factory() as db:
            values = {"pipeline_status": status}
            if status == "queued":
                values["pipeline_started_at"] = None
                values["pipeline_completed_at"] = None
            if started_at is not None:
                values["pipeline_started_at"] = started_at
            if completed_at is not None:
                values["pipeline_completed_at"] = completed_at
            await db.execute(
                update(Label).where(Label.id == label_id).values(**values)
            )
            await db.commit()


pipeline_queue = PipelineQueue()
