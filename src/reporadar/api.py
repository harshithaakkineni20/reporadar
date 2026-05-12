from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reporadar.emailer import SUBSCRIBER_COLUMNS
from reporadar.history import (
    category_counts,
    discoveries_for_run,
    latest_run_date,
    load_runs,
    repo_timeline,
)

try:
    from fastapi import FastAPI, HTTPException
except ImportError:  # pragma: no cover - exercised only when backend extra is missing.
    FastAPI = None  # type: ignore[assignment]
    HTTPException = None  # type: ignore[assignment]


def create_app(
    history_dir: Path = Path("data/history"),
    subscribers_path: Path = Path("data/subscribers.csv"),
) -> Any:
    if FastAPI is None:
        raise RuntimeError("Install backend dependencies with `python3 -m pip install -e .[backend]`.")

    app = FastAPI(
        title="RepoRadar API",
        version="0.1.0",
        description="Persistent API for weekly GitHub repository discovery signals.",
    )

    @app.get("/health")
    def health() -> dict[str, str | bool | None]:
        return {
            "ok": True,
            "latest_run_date": latest_run_date(history_dir),
        }

    @app.get("/runs")
    def runs() -> list[dict[str, str]]:
        return load_runs(history_dir)

    @app.get("/discoveries")
    def discoveries(
        run_date: str | None = None,
        category: str | None = None,
        limit: int = 20,
        min_quality: float = 5.0,
        max_noise: float = 4.0,
    ) -> list[dict[str, str]]:
        return discoveries_for_run(
            history_dir,
            run_date=run_date,
            category=category,
            limit=limit,
            min_quality=min_quality,
            max_noise=max_noise,
        )

    @app.get("/categories")
    def categories(run_date: str | None = None) -> dict[str, int]:
        return category_counts(history_dir, run_date=run_date)

    @app.get("/repos/{repo_name:path}")
    def repo(repo_name: str) -> dict[str, Any]:
        timeline = repo_timeline(history_dir, repo_name)
        if not timeline:
            raise HTTPException(status_code=404, detail=f"Repo not found: {repo_name}")
        return {
            "repo_name": repo_name,
            "appearances": len(timeline),
            "timeline": timeline,
        }

    @app.post("/subscribe")
    def subscribe(payload: dict[str, str]) -> dict[str, str]:
        email = payload.get("email", "").strip()
        if "@" not in email:
            raise HTTPException(status_code=400, detail="A valid email is required.")
        name = payload.get("name", "").strip()
        upsert_subscriber(subscribers_path, email=email, name=name)
        return {"status": "active", "email": email}

    return app


def upsert_subscriber(path: Path, *, email: str, name: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    if path.exists():
        with path.open("r", newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))

    now = datetime.now(timezone.utc).date().isoformat()
    found = False
    for row in rows:
        if row.get("email", "").lower() == email.lower():
            row["name"] = name or row.get("name", "")
            row["status"] = "active"
            found = True
            break

    if not found:
        rows.append({"email": email, "name": name, "status": "active", "created_at": now})

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUBSCRIBER_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


app = create_app()
