from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


RANKING_COLUMNS = [
    "rank",
    "window_id",
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
    "observation_start",
    "cutoff",
    "target_end",
]


DATASET_COLUMNS = [
    "window_id",
    "repo_name",
    "repo_id",
    "observation_start",
    "cutoff",
    "target_end",
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


ENRICHED_COLUMNS = [
    "rank",
    "repo_name",
    "category",
    "category_confidence",
    "discovery_score",
    "quality_score",
    "noise_score",
    "category_reason",
    "score",
    "future_growth",
    "why",
    "html_url",
    "description",
    "homepage",
    "primary_language",
    "topics",
    "license_key",
    "stargazers_count",
    "forks_count",
    "open_issues_count",
    "owner_type",
    "created_at",
    "updated_at",
    "pushed_at",
    "is_fork",
    "is_archived",
    "has_issues",
    "has_pages",
    "has_discussions",
    "metadata_error",
    "languages_json",
    "readme_excerpt",
]


def write_rows_csv(
    rows: list[dict[str, Any]],
    output_path: Path,
    columns: list[str] | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        columns = sorted({key for row in rows for key in row})
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_rankings_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    write_rows_csv(rows, output_path, RANKING_COLUMNS)


def write_dataset_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    write_rows_csv(rows, output_path, DATASET_COLUMNS)


def write_enriched_csv(rows: list[dict[str, Any]], output_path: Path) -> None:
    extra_columns = sorted({key for row in rows for key in row} - set(ENRICHED_COLUMNS))
    write_rows_csv(rows, output_path, ENRICHED_COLUMNS + extra_columns)


def read_rows_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_rankings_csv(path: Path) -> list[dict[str, str]]:
    return read_rows_csv(path)
