import asyncio
from datetime import UTC, datetime, timedelta

from app.scheduler import MonitorScheduler, target_is_due

NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def _target(minutes_ago: int | None, *, enabled: bool = True) -> dict:
    latest = None
    if minutes_ago is not None:
        latest = {"created_at": (NOW - timedelta(minutes=minutes_ago)).isoformat()}
    return {
        "id": "target-1",
        "enabled": enabled,
        "interval_minutes": 30,
        "latest_snapshot": latest,
    }


def test_target_is_due_respects_interval_and_enabled_state() -> None:
    assert target_is_due(_target(None), NOW)
    assert target_is_due(_target(31), NOW)
    assert not target_is_due(_target(10), NOW)
    assert not target_is_due(_target(60, enabled=False), NOW)


class FakeDatabase:
    def list_targets(self) -> list[dict]:
        return [_target(31), {**_target(5), "id": "target-2"}]


class FakeService:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def run_target(self, target_id: str) -> dict:
        self.calls.append(target_id)
        return {"id": f"snapshot-{target_id}"}


def test_scheduler_runs_only_due_targets() -> None:
    service = FakeService()
    scheduler = MonitorScheduler(FakeDatabase(), service, tick_seconds=5)

    outcomes = asyncio.run(scheduler.run_due_targets(NOW))

    assert service.calls == ["target-1"]
    assert outcomes == [
        {
            "target_id": "target-1",
            "status": "captured",
            "snapshot_id": "snapshot-target-1",
        }
    ]
