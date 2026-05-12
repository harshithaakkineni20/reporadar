from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


RANKING_COLUMNS = [
    "rank",
    "repo_name",
    "score",
    "why",
    "stars",
    "forks",
    "unique_actors",
    "issues_opened",
    "pull_requests_opened",
    "pushes",
    "commits",
    "releases",
    "creates",
    "observed_events",
    "observation_hours",
    "activity_velocity",
    "future_stars",
    "future_forks",
    "future_events",
    "future_growth",
]


def write_rankings_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RANKING_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_rankings_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
