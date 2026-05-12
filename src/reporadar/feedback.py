from __future__ import annotations

import csv
from pathlib import Path


def read_feedback(path: Path | None) -> dict[str, dict[str, str]]:
    if path is None or not path.exists():
        return {}
    with path.open("r", newline="", encoding="utf-8") as handle:
        return {row["repo_name"]: row for row in csv.DictReader(handle)}


def attach_feedback(
    rows: list[dict[str, str]],
    feedback: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    enriched = []
    for row in rows:
        repo_feedback = feedback.get(row.get("repo_name", ""))
        if not repo_feedback:
            enriched.append(dict(row))
            continue

        updated = dict(row)
        updated["human_label"] = repo_feedback.get("label", "")
        updated["human_reason"] = repo_feedback.get("reason", "")
        updated["reviewed_at"] = repo_feedback.get("reviewed_at", "")
        corrected_category = repo_feedback.get("corrected_category", "")
        if corrected_category:
            updated["category"] = corrected_category
        enriched.append(updated)
    return enriched
