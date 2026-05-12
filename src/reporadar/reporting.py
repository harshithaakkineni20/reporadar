from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def build_discovery_report(
    rows: list[dict[str, str]],
    source_name: str,
    top: int = 5,
    min_quality: float = 5.0,
    max_noise: float = 3.5,
) -> str:
    filtered = [
        row
        for row in rows
        if row.get("category") not in {"personal_content_noise", "uncategorized"}
        and as_float(row, "quality_score") >= min_quality
        and as_float(row, "noise_score") <= max_noise
    ]
    filtered.sort(key=lambda row: -as_float(row, "discovery_score"))

    category_counts = Counter(row.get("category", "uncategorized") for row in rows)
    report_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# RepoRadar Discovery Report",
        "",
        f"Generated: {report_time}",
        f"Source: `{source_name}`",
        "",
        "## Summary",
        "",
        f"- Repositories analyzed: {len(rows)}",
        f"- Discovery candidates after filters: {len(filtered)}",
        f"- Minimum quality: {min_quality}",
        f"- Maximum noise: {max_noise}",
        "",
        "## Category Counts",
        "",
        "| Category | Count |",
        "|---|---:|",
    ]

    for category, count in sorted(category_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{category}` | {count} |")

    lines.extend(
        [
            "",
            "## Top Discovery Candidates",
            "",
            "| Rank | Repo | Category | Discovery | Quality | Noise | Why |",
            "|---:|---|---|---:|---:|---:|---|",
        ]
    )

    for index, row in enumerate(filtered[:top], start=1):
        repo = row.get("repo_name", "")
        url = row.get("html_url", "")
        repo_link = f"[{repo}]({url})" if url else f"`{repo}`"
        lines.append(
            "| "
            f"{index} | {repo_link} | `{row.get('category', '')}` | "
            f"{as_float(row, 'discovery_score'):.3f} | "
            f"{as_float(row, 'quality_score'):.3f} | "
            f"{as_float(row, 'noise_score'):.3f} | "
            f"{escape_table(row.get('category_reason', ''))} |"
        )

    if not filtered:
        lines.append("| - | No candidates passed the filters. | - | - | - | - | - |")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `discovery_score` combines model momentum, metadata quality, and noise penalties.",
            "- `personal_content_noise` catches test repos, image beds, logs, blogs, and similar low-discovery-value repos.",
            "- This report is generated from a small top-N enrichment pass, so results improve as more ranked repos are enriched.",
            "",
        ]
    )

    return "\n".join(lines)


def write_report(markdown: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")


def as_float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    if value in ("", None):
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def escape_table(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
