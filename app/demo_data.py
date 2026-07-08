from __future__ import annotations

import hashlib

from app.database import Database
from app.diff_engine import compare_snapshots


def _capture(text: str, response_ms: int) -> dict:
    return {
        "status_code": 200,
        "title": "Lumen Commerce Status",
        "content_text": text,
        "content_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "response_ms": response_ms,
        "engine": "demo",
        "screenshot_path": None,
    }


def seed_demo_data(database: Database) -> None:
    if database.count_targets() > 0:
        return

    target = database.create_target(
        name="Checkout status",
        url="https://status.example.com/checkout",
        interval_minutes=15,
        render_js=True,
    )
    baseline = _capture(
        "All systems operational. Checkout API healthy. Payment latency 184 milliseconds.",
        184,
    )
    database.save_snapshot(target["id"], baseline, compare_snapshots(None, baseline))

    changed = _capture(
        "Partial service disruption. Checkout API degraded in Europe. "
        "Payment latency 980 milliseconds. Engineers are investigating.",
        980,
    )
    previous = database.latest_snapshot(target["id"])
    database.save_snapshot(target["id"], changed, compare_snapshots(previous, changed))

    docs = database.create_target(
        name="Developer changelog",
        url="https://docs.example.com/changelog",
        interval_minutes=60,
        render_js=False,
    )
    docs_capture = _capture(
        "Developer platform changelog. Version 2.4 adds webhook retries and audit exports.",
        132,
    )
    database.save_snapshot(docs["id"], docs_capture, compare_snapshots(None, docs_capture))
