from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from app.database import Database
from app.probes import ProbeError
from app.service import MonitorService, TargetNotFoundError


def target_is_due(target: dict, now: datetime | None = None) -> bool:
    if not target.get("enabled", False):
        return False

    latest = target.get("latest_snapshot")
    if not latest:
        return True

    checked_at = datetime.fromisoformat(latest["created_at"])
    if checked_at.tzinfo is None:
        checked_at = checked_at.replace(tzinfo=UTC)
    current_time = now or datetime.now(UTC)
    return current_time - checked_at >= timedelta(minutes=target["interval_minutes"])


class MonitorScheduler:
    def __init__(
        self,
        database: Database,
        service: MonitorService,
        tick_seconds: int = 60,
    ) -> None:
        self.database = database
        self.service = service
        self.tick_seconds = max(5, tick_seconds)
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task[None] | None = None

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        if self.running:
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run(), name="lumenwatch-scheduler")

    async def stop(self) -> None:
        if not self._task:
            return
        self._stop_event.set()
        await self._task
        self._task = None

    async def run_due_targets(self, now: datetime | None = None) -> list[dict]:
        outcomes: list[dict] = []
        for target in self.database.list_targets():
            if not target_is_due(target, now):
                continue
            try:
                snapshot = await self.service.run_target(target["id"])
                outcomes.append(
                    {
                        "target_id": target["id"],
                        "status": "captured",
                        "snapshot_id": snapshot["id"],
                    }
                )
            except (ProbeError, TargetNotFoundError) as error:
                outcomes.append(
                    {
                        "target_id": target["id"],
                        "status": "failed",
                        "error": str(error),
                    }
                )
        return outcomes

    async def _run(self) -> None:
        while not self._stop_event.is_set():
            await self.run_due_targets()
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.tick_seconds)
            except TimeoutError:
                continue
