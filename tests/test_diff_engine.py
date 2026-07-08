from app.diff_engine import compare_snapshots


def test_first_snapshot_is_baseline() -> None:
    current = {"title": "Status", "status_code": 200, "content_text": "All systems normal"}

    result = compare_snapshots(None, current)

    assert result["severity"] == "baseline"
    assert result["change_score"] == 0


def test_status_failure_is_high_severity() -> None:
    previous = {"title": "Status", "status_code": 200, "content_text": "All systems normal"}
    current = {"title": "Status", "status_code": 503, "content_text": "Service unavailable"}

    result = compare_snapshots(previous, current)

    assert result["severity"] == "high"
    assert "HTTP status changed" in result["summary"]
    assert result["added"]
    assert result["removed"]
