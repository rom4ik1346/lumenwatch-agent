from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _resolve_path(env_name: str, default: str) -> Path:
    configured = Path(os.getenv(env_name, default))
    return configured if configured.is_absolute() else PROJECT_ROOT / configured


def database_path() -> Path:
    return _resolve_path("LUMENWATCH_DATABASE_PATH", "data/lumenwatch.db")


def capture_directory() -> Path:
    return _resolve_path("LUMENWATCH_CAPTURE_DIR", "data/captures")


def browser_enabled() -> bool:
    return os.getenv("LUMENWATCH_BROWSER_ENABLED", "false").lower() in {"1", "true", "yes", "on"}


def scheduler_enabled() -> bool:
    return os.getenv("LUMENWATCH_SCHEDULER_ENABLED", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def scheduler_tick_seconds() -> int:
    return max(5, int(os.getenv("LUMENWATCH_SCHEDULER_TICK_SECONDS", "60")))
