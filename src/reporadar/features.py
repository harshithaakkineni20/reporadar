from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from math import log1p
from typing import Any


def parse_github_time(value: str) -> datetime:
    """Parse GitHub's ISO timestamp format into an aware UTC datetime."""
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass
class RepoAccumulator:
    repo_name: str
    repo_id: int | None = None
    stars: int = 0
    forks: int = 0
    issues_opened: int = 0
    pull_requests_opened: int = 0
    pushes: int = 0
    commits: int = 0
    releases: int = 0
    creates: int = 0
    observed_events: int = 0
    future_stars: int = 0
    future_forks: int = 0
    future_events: int = 0
    actors: set[str] = field(default_factory=set)
    first_seen: datetime | None = None
    last_seen: datetime | None = None

    def add_observed(self, event: dict[str, Any], event_time: datetime) -> None:
        self.observed_events += 1
        self._track_actor(event)
        self._track_time(event_time)

        event_type = event.get("type")
        payload = event.get("payload") or {}

        if event_type == "WatchEvent" and payload.get("action", "started") == "started":
            self.stars += 1
        elif event_type == "ForkEvent":
            self.forks += 1
        elif event_type == "IssuesEvent" and payload.get("action") == "opened":
            self.issues_opened += 1
        elif event_type == "PullRequestEvent" and payload.get("action") == "opened":
            self.pull_requests_opened += 1
        elif event_type == "PushEvent":
            self.pushes += 1
            self.commits += len(payload.get("commits") or [])
        elif event_type == "ReleaseEvent" and payload.get("action") == "published":
            self.releases += 1
        elif event_type == "CreateEvent":
            self.creates += 1

    def add_future(self, event: dict[str, Any]) -> None:
        self.future_events += 1
        event_type = event.get("type")
        payload = event.get("payload") or {}
        if event_type == "WatchEvent" and payload.get("action", "started") == "started":
            self.future_stars += 1
        elif event_type == "ForkEvent":
            self.future_forks += 1

    def to_row(self) -> dict[str, Any]:
        observation_hours = 1.0
        if self.first_seen and self.last_seen and self.last_seen > self.first_seen:
            observation_hours = max(
                (self.last_seen - self.first_seen).total_seconds() / 3600,
                1.0,
            )

        activity_velocity = self.observed_events / observation_hours
        future_growth = self.future_stars + (0.5 * self.future_forks) + (0.1 * self.future_events)

        return {
            "repo_name": self.repo_name,
            "repo_id": self.repo_id or "",
            "stars": self.stars,
            "forks": self.forks,
            "issues_opened": self.issues_opened,
            "pull_requests_opened": self.pull_requests_opened,
            "pushes": self.pushes,
            "commits": self.commits,
            "releases": self.releases,
            "creates": self.creates,
            "observed_events": self.observed_events,
            "unique_actors": len(self.actors),
            "observation_hours": round(observation_hours, 3),
            "activity_velocity": round(activity_velocity, 3),
            "future_stars": self.future_stars,
            "future_forks": self.future_forks,
            "future_events": self.future_events,
            "future_growth": round(future_growth, 3),
        }

    def _track_actor(self, event: dict[str, Any]) -> None:
        actor = event.get("actor") or {}
        login = actor.get("login")
        if login:
            self.actors.add(str(login))

    def _track_time(self, event_time: datetime) -> None:
        if self.first_seen is None or event_time < self.first_seen:
            self.first_seen = event_time
        if self.last_seen is None or event_time > self.last_seen:
            self.last_seen = event_time


def infer_cutoff(events: list[dict[str, Any]], fraction: float = 0.7) -> datetime:
    """Pick a cutoff inside the event timeline when the user does not provide one."""
    if not events:
        raise ValueError("Cannot infer a cutoff from an empty event list")

    times = sorted(parse_github_time(event["created_at"]) for event in events if event.get("created_at"))
    if not times:
        raise ValueError("Events do not contain created_at timestamps")

    index = min(max(int(len(times) * fraction), 0), len(times) - 1)
    return times[index]


def build_feature_rows(
    events: list[dict[str, Any]],
    cutoff: datetime,
    target_hours: int | None = 168,
) -> list[dict[str, Any]]:
    """Aggregate raw events into one row per repository.

    Events at or before the cutoff become model features. Events after the cutoff become
    future-growth labels, optionally capped by target_hours.
    """
    cutoff = cutoff.astimezone(timezone.utc)
    target_end = cutoff + timedelta(hours=target_hours) if target_hours else None
    accumulators: dict[str, RepoAccumulator] = {}

    for event in sorted(events, key=lambda item: item.get("created_at", "")):
        repo = event.get("repo") or {}
        repo_name = repo.get("name")
        created_at = event.get("created_at")
        if not repo_name or not created_at:
            continue

        repo_name = str(repo_name)
        event_time = parse_github_time(created_at)
        accumulator = accumulators.get(repo_name)

        if event_time <= cutoff:
            if accumulator is None:
                accumulator = RepoAccumulator(repo_name=repo_name, repo_id=repo.get("id"))
                accumulators[repo_name] = accumulator
            accumulator.add_observed(event, event_time)
        elif accumulator is not None and (target_end is None or event_time <= target_end):
            accumulator.add_future(event)

    return [accumulator.to_row() for accumulator in accumulators.values()]


def baseline_score(row: dict[str, Any]) -> float:
    """A transparent v0 score for early repo momentum."""
    community = 2.2 * log1p(float(row["unique_actors"]))
    attention = 2.8 * log1p(float(row["stars"])) + 2.0 * log1p(float(row["forks"]))
    collaboration = 1.4 * log1p(float(row["issues_opened"]) + float(row["pull_requests_opened"]))
    shipping = 0.7 * log1p(float(row["commits"])) + 1.1 * log1p(float(row["releases"]))
    velocity = 1.8 * log1p(float(row["activity_velocity"]))
    return round(community + attention + collaboration + shipping + velocity, 4)
