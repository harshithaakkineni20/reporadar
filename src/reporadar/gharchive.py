from __future__ import annotations

import gzip
import json
import urllib.request
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path
from typing import Any


GHARCHIVE_BASE_URL = "https://data.gharchive.org"


def archive_url(day: date, hour: int) -> str:
    """Build the GH Archive URL for one UTC hour."""
    if hour < 0 or hour > 23:
        raise ValueError("hour must be between 0 and 23")
    return f"{GHARCHIVE_BASE_URL}/{day.isoformat()}-{hour}.json.gz"


def fetch_archive(day: date, hour: int, output_dir: Path) -> Path:
    """Download one GH Archive hourly gzip file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{day.isoformat()}-{hour}.json.gz"
    if destination.exists():
        return destination

    url = archive_url(day, hour)
    request = urllib.request.Request(url, headers={"User-Agent": "RepoRadar/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        destination.write_bytes(response.read())
    return destination


def iter_dates(start: date, end: date) -> Iterator[date]:
    """Yield every date in a closed date range."""
    if end < start:
        raise ValueError("end date must be on or after start date")
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def iter_event_files(path: Path) -> Iterator[Path]:
    """Yield supported event files from a file or directory."""
    if path.is_file():
        yield path
        return

    if not path.exists():
        raise FileNotFoundError(path)

    patterns = ("*.json", "*.jsonl", "*.json.gz")
    for pattern in patterns:
        yield from sorted(path.rglob(pattern))


def iter_events(paths: list[Path]) -> Iterator[dict[str, Any]]:
    """Read JSON or gzip-compressed JSONL GH Archive events."""
    for input_path in paths:
        for event_file in iter_event_files(input_path):
            opener = gzip.open if event_file.suffix == ".gz" else open
            with opener(event_file, "rt", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"Invalid JSON in {event_file}:{line_number}") from exc
                    if isinstance(event, dict):
                        yield event
