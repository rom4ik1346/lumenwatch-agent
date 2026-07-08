from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from app.config import browser_enabled, capture_directory, database_path
from app.database import Database
from app.demo_data import seed_demo_data
from app.service import MonitorService

mcp = FastMCP("LumenWatch Agent", json_response=True)
database = Database(database_path())
database.initialize()
seed_demo_data(database)
service = MonitorService(database, capture_directory(), browser_enabled())


@mcp.tool()
def create_watch_target(
    name: str,
    url: str,
    interval_minutes: int = 30,
    render_js: bool = False,
) -> dict:
    """Create a website watch target in the local LumenWatch database."""
    return database.create_target(
        name=name,
        url=url,
        interval_minutes=max(5, min(interval_minutes, 10_080)),
        render_js=render_js,
    )


@mcp.tool()
async def run_watch(target_id: str) -> dict:
    """Capture a target now and compare it with the previous snapshot."""
    return await service.run_target(target_id)


@mcp.tool()
def list_watch_targets() -> list[dict]:
    """List monitored websites with their latest snapshot."""
    return database.list_targets()


@mcp.tool()
def list_recent_changes(limit: int = 20) -> list[dict]:
    """List recent website changes excluding baselines and unchanged checks."""
    return database.list_snapshots(limit=max(1, min(limit, 100)), changes_only=True)


@mcp.tool()
def get_change_details(snapshot_id: str) -> dict:
    """Get the diff summary and captured content for one snapshot."""
    return database.get_snapshot(snapshot_id) or {
        "error": "Snapshot not found",
        "snapshot_id": snapshot_id,
    }


if __name__ == "__main__":
    mcp.run(transport=os.getenv("MCP_TRANSPORT", "stdio"))
