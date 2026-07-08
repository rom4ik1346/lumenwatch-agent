import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.models import CaptureResult


class FakeProbe:
    async def capture(self, url: str, target_id: str) -> CaptureResult:
        content = f"Stable content for {url} and {target_id}"
        return CaptureResult(
            status_code=200,
            title="Fake page",
            content_text=content,
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
            response_ms=42,
            engine="fake",
        )


def fake_probe_factory(*_) -> FakeProbe:
    return FakeProbe()


def test_create_target_and_run_check(tmp_path: Path) -> None:
    application = create_app(
        database_file=tmp_path / "lumenwatch.db",
        capture_path=tmp_path / "captures",
        probe_factory=fake_probe_factory,
    )

    with TestClient(application) as client:
        created = client.post(
            "/api/targets",
            json={
                "name": "Example",
                "url": "https://example.com",
                "interval_minutes": 30,
                "render_js": False,
            },
        )
        target_id = created.json()["id"]
        run = client.post(f"/api/targets/{target_id}/run")
        overview = client.get("/api/overview")

    assert created.status_code == 201
    assert run.status_code == 201
    assert run.json()["severity"] == "baseline"
    assert overview.json()["targets"] == 3
