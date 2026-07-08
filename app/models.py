from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CaptureResult:
    status_code: int
    title: str
    content_text: str
    content_hash: str
    response_ms: int
    engine: str
    screenshot_path: str | None = None
