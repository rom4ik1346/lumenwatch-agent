from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

WHITESPACE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    return WHITESPACE.sub(" ", value).strip()


def _word_changes(previous: str, current: str) -> tuple[list[str], list[str]]:
    before = normalize_text(previous).split()
    after = normalize_text(current).split()
    matcher = SequenceMatcher(None, before, after, autojunk=False)
    added: list[str] = []
    removed: list[str] = []

    for operation, before_start, before_end, after_start, after_end in matcher.get_opcodes():
        if operation in {"insert", "replace"}:
            added.extend(after[after_start:after_end])
        if operation in {"delete", "replace"}:
            removed.extend(before[before_start:before_end])

    return added[:24], removed[:24]


def compare_snapshots(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
) -> dict[str, Any]:
    if previous is None:
        return {
            "similarity": 100.0,
            "change_score": 0.0,
            "severity": "baseline",
            "summary": "Baseline captured. Future checks will be compared with this version.",
            "added": [],
            "removed": [],
        }

    previous_text = normalize_text(previous.get("content_text", ""))
    current_text = normalize_text(current.get("content_text", ""))
    similarity = SequenceMatcher(None, previous_text, current_text, autojunk=False).ratio() * 100
    added, removed = _word_changes(previous_text, current_text)

    title_changed = previous.get("title") != current.get("title")
    status_changed = previous.get("status_code") != current.get("status_code")
    change_score = 100 - similarity
    if title_changed:
        change_score += 8
    if status_changed:
        change_score += 20
    change_score = round(min(change_score, 100), 1)

    if status_changed and int(current.get("status_code", 0)) >= 400:
        severity = "high"
    elif change_score < 2:
        severity = "none"
    elif change_score < 12:
        severity = "low"
    elif change_score < 30:
        severity = "medium"
    else:
        severity = "high"

    signals: list[str] = []
    if status_changed:
        previous_status = previous.get("status_code")
        current_status = current.get("status_code")
        signals.append(f"HTTP status changed from {previous_status} to {current_status}")
    if title_changed:
        signals.append("page title changed")
    if added:
        signals.append(f"{len(added)} added word(s)")
    if removed:
        signals.append(f"{len(removed)} removed word(s)")
    if not signals:
        signals.append("no meaningful content change")

    return {
        "similarity": round(similarity, 1),
        "change_score": change_score,
        "severity": severity,
        "summary": f"{severity.capitalize()} change: " + ", ".join(signals) + ".",
        "added": added,
        "removed": removed,
    }
