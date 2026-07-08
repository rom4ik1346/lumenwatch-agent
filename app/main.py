from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.config import browser_enabled, capture_directory, database_path
from app.database import Database
from app.demo_data import seed_demo_data
from app.probes import ProbeError
from app.schemas import TargetCreate
from app.service import MonitorService, ProbeFactory, TargetNotFoundError, default_probe_factory


def create_app(
    database_file: Path | None = None,
    capture_path: Path | None = None,
    probe_factory: ProbeFactory = default_probe_factory,
) -> FastAPI:
    database = Database(database_file or database_path())
    service = MonitorService(
        database=database,
        capture_directory=capture_path or capture_directory(),
        browser_enabled=browser_enabled(),
        probe_factory=probe_factory,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        database.initialize()
        seed_demo_data(database)
        yield

    application = FastAPI(
        title="LumenWatch Agent",
        version="0.2.0",
        description="Website change intelligence through REST and MCP.",
        lifespan=lifespan,
    )
    application.state.database = database
    application.state.monitor_service = service

    @application.get("/api/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "lumenwatch-agent"}

    @application.get("/api/overview", tags=["monitoring"])
    async def overview() -> dict:
        return database.overview()

    @application.get("/api/targets", tags=["targets"])
    async def list_targets() -> list[dict]:
        return database.list_targets()

    @application.get("/api/targets/{target_id}", tags=["targets"])
    async def get_target(target_id: str) -> dict:
        target = database.get_target(target_id)
        if not target:
            raise HTTPException(status_code=404, detail="Watch target not found.")
        target["snapshots"] = database.list_snapshots(limit=20, target_id=target_id)
        return target

    @application.post("/api/targets", status_code=201, tags=["targets"])
    async def create_target(payload: TargetCreate) -> dict:
        return database.create_target(
            name=payload.name.strip(),
            url=payload.url,
            interval_minutes=payload.interval_minutes,
            render_js=payload.render_js,
        )

    @application.post("/api/targets/{target_id}/run", status_code=201, tags=["monitoring"])
    async def run_target(target_id: str) -> dict:
        try:
            return await service.run_target(target_id)
        except TargetNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ProbeError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @application.get("/api/runs", tags=["monitoring"])
    async def list_runs(limit: int = 50, target_id: str | None = None) -> list[dict]:
        return database.list_snapshots(
            limit=max(1, min(limit, 200)),
            target_id=target_id,
        )

    @application.get("/api/changes", tags=["monitoring"])
    async def list_changes(limit: int = 50) -> list[dict]:
        return database.list_snapshots(
            limit=max(1, min(limit, 200)),
            changes_only=True,
        )

    @application.get("/api/runs/{snapshot_id}", tags=["monitoring"])
    async def get_run(snapshot_id: str) -> dict:
        snapshot = database.get_snapshot(snapshot_id)
        if not snapshot:
            raise HTTPException(status_code=404, detail="Snapshot not found.")
        return snapshot

    return application


app = create_app()
