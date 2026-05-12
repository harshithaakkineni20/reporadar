from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any


RUN_COLUMNS = [
    "run_date",
    "events",
    "training_rows",
    "ranked_repos",
    "enriched_repos",
    "candidate_repos",
    "report",
]


OBSERVATION_COLUMNS = [
    "run_date",
    "repo_name",
    "rank",
    "category",
    "category_confidence",
    "discovery_score",
    "quality_score",
    "noise_score",
    "score",
    "future_growth",
    "human_label",
    "html_url",
    "description",
    "primary_language",
    "topics",
    "stargazers_count",
    "forks_count",
    "open_issues_count",
    "category_reason",
]


def append_run_history(
    *,
    run_date: str,
    summary: dict[str, Any],
    discovery_rows: list[dict[str, Any]],
    history_dir: Path,
) -> tuple[Path, Path]:
    """Append or replace one weekly run in the persistent history CSVs."""
    history_dir.mkdir(parents=True, exist_ok=True)
    runs_path = history_dir / "runs.csv"
    observations_path = history_dir / "repo_observations.csv"

    runs = [row for row in read_csv(runs_path) if row.get("run_date") != run_date]
    runs.append(
        {
            "run_date": run_date,
            "events": summary.get("events", ""),
            "training_rows": summary.get("training_rows", ""),
            "ranked_repos": summary.get("ranked_repos", ""),
            "enriched_repos": summary.get("enriched_repos", ""),
            "candidate_repos": len(discovery_rows),
            "report": summary.get("report", ""),
        }
    )
    runs.sort(key=lambda row: row.get("run_date", ""))
    write_csv(runs_path, runs, RUN_COLUMNS)

    observations = [
        row for row in read_csv(observations_path) if row.get("run_date") != run_date
    ]
    observations.extend(observation_row(run_date, row) for row in discovery_rows)
    observations.sort(
        key=lambda row: (
            row.get("run_date", ""),
            as_int(row, "rank", default=999_999),
            row.get("repo_name", ""),
        )
    )
    write_csv(observations_path, observations, OBSERVATION_COLUMNS)
    return runs_path, observations_path


def observation_row(run_date: str, row: dict[str, Any]) -> dict[str, Any]:
    return {column: row.get(column, "") for column in OBSERVATION_COLUMNS} | {
        "run_date": run_date
    }


def latest_run_date(history_dir: Path) -> str | None:
    runs = read_csv(history_dir / "runs.csv")
    if not runs:
        return None
    return max(row["run_date"] for row in runs if row.get("run_date"))


def load_observations(history_dir: Path) -> list[dict[str, str]]:
    return read_csv(history_dir / "repo_observations.csv")


def load_runs(history_dir: Path) -> list[dict[str, str]]:
    return read_csv(history_dir / "runs.csv")


def discoveries_for_run(
    history_dir: Path,
    run_date: str | None = None,
    *,
    limit: int = 20,
    category: str | None = None,
    hide_noise: bool = True,
    hide_uncategorized: bool = True,
    min_quality: float = 5.0,
    max_noise: float = 4.0,
) -> list[dict[str, str]]:
    run_date = run_date or latest_run_date(history_dir)
    if not run_date:
        return []

    rows = [row for row in load_observations(history_dir) if row.get("run_date") == run_date]
    if category:
        rows = [row for row in rows if row.get("category") == category]
    if hide_noise:
        rows = [row for row in rows if row.get("category") != "personal_content_noise"]
    if hide_uncategorized:
        rows = [row for row in rows if row.get("category") != "uncategorized"]

    rows = [
        row
        for row in rows
        if as_float(row, "quality_score") >= min_quality
        and as_float(row, "noise_score") <= max_noise
    ]
    rows.sort(key=lambda row: -as_float(row, "discovery_score"))
    return with_trend(rows[:limit], load_observations(history_dir))


def repo_timeline(history_dir: Path, repo_name: str) -> list[dict[str, str]]:
    rows = [row for row in load_observations(history_dir) if row.get("repo_name") == repo_name]
    rows.sort(key=lambda row: row.get("run_date", ""))
    return rows


def category_counts(history_dir: Path, run_date: str | None = None) -> dict[str, int]:
    run_date = run_date or latest_run_date(history_dir)
    rows = [row for row in load_observations(history_dir) if row.get("run_date") == run_date]
    return dict(Counter(row.get("category", "uncategorized") for row in rows))


def with_trend(
    rows: list[dict[str, str]],
    history_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    enriched = []
    for row in rows:
        previous = previous_observation(row, history_rows)
        updated = dict(row)
        updated["previous_rank"] = previous.get("rank", "") if previous else ""
        updated["previous_discovery_score"] = (
            previous.get("discovery_score", "") if previous else ""
        )
        updated["discovery_delta"] = (
            f"{as_float(row, 'discovery_score') - as_float(previous, 'discovery_score'):.3f}"
            if previous
            else ""
        )
        updated["appearances"] = str(
            sum(1 for item in history_rows if item.get("repo_name") == row.get("repo_name"))
        )
        updated["is_new"] = "false" if previous else "true"
        enriched.append(updated)
    return enriched


def previous_observation(
    row: dict[str, str],
    history_rows: list[dict[str, str]],
) -> dict[str, str] | None:
    repo_name = row.get("repo_name")
    run_date = row.get("run_date")
    earlier = [
        item
        for item in history_rows
        if item.get("repo_name") == repo_name and item.get("run_date", "") < run_date
    ]
    if not earlier:
        return None
    return max(earlier, key=lambda item: item.get("run_date", ""))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def as_float(row: dict[str, Any] | None, key: str) -> float:
    if not row:
        return 0.0
    value = row.get(key, 0)
    if value in ("", None):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def as_int(row: dict[str, Any], key: str, default: int = 0) -> int:
    value = row.get(key, "")
    if value in ("", None):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default
