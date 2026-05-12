from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def build_discovery_report(
    rows: list[dict[str, str]],
    source_name: str,
    top: int = 5,
    min_quality: float = 5.0,
    max_noise: float = 4.0,
) -> str:
    filtered = [row for row in rows if passes_report_filters(row, min_quality, max_noise)]
    filtered.sort(key=lambda row: -as_float(row, "discovery_score"))
    near_misses = find_near_misses(rows, min_quality, max_noise, limit=5)

    category_counts = Counter(row.get("category", "uncategorized") for row in rows)
    noise_count = category_counts.get("personal_content_noise", 0)
    uncategorized_count = category_counts.get("uncategorized", 0)
    report_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# RepoRadar Discovery Review",
        "",
        f"Generated: {report_time}",
        f"Source: `{source_name}`",
        "",
        "## How To Read This",
        "",
        "This report is a review queue, not a final truth list. RepoRadar first ranks repositories by activity momentum, then enriches the highest-ranked repos with GitHub metadata, labels their likely use case, and filters obvious noise.",
        "",
        "Your job as the reviewer is to ask: Is this repo a real useful project, is the category right, and should RepoRadar promote, hide, or relabel similar repos next time?",
        "",
        "## What Happened",
        "",
        f"- Repositories analyzed: {len(rows)}",
        f"- Discovery candidates after filters: {len(filtered)}",
        f"- Human-reviewed candidates: {human_review_count(rows)}",
        f"- Repos labeled as noise: {noise_count}",
        f"- Repos left uncategorized: {uncategorized_count}",
        f"- Minimum quality: {min_quality}",
        f"- Maximum noise: {max_noise}",
        "",
        "## Category Mix",
        "",
        "| Category | Count |",
        "|---|---:|",
    ]

    for category, count in sorted(category_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{category}` | {count} |")

    lines.extend(
        [
            "",
            "## Candidate Cards",
            "",
        ]
    )

    for index, row in enumerate(filtered[:top], start=1):
        lines.extend(candidate_card(row, index))

    if not filtered:
        lines.append("No candidates passed the current filters. Try lowering `--min-quality`, raising `--max-noise`, or enriching more ranked repositories.")

    lines.extend(
        [
            "",
            "## Near Misses To Debug",
            "",
            "These repos had enough signal to be worth inspecting, but they did not pass the report filters. This section is for improving the model, not for final recommendations.",
            "",
        ]
    )

    if near_misses:
        lines.extend(
            [
                "| Repo | Category | Discovery | Quality | Noise | Why filtered |",
                "|---|---|---:|---:|---:|---|",
            ]
        )
        for row in near_misses:
            lines.append(near_miss_row(row, min_quality, max_noise))
    else:
        lines.append("No strong near misses found under the current filters.")

    lines.extend(
        [
            "",
            "## What To Check Manually",
            "",
            "For each candidate, answer:",
            "",
            "1. Is this a real reusable tool, dataset, app, or library?",
            "2. Is the assigned category correct?",
            "3. Would a developer actually want to discover this?",
            "4. Did the model overvalue raw activity, vague keywords, or noisy metadata?",
            "5. Should similar repos be promoted, hidden, or relabeled?",
            "",
            "## If You Run This Again Next Week",
            "",
            "If you use the same downloaded GH Archive files, the output should be mostly the same because the input data is the same.",
            "",
            "If you fetch newer GH Archive data seven days later, RepoRadar will rank a new slice of GitHub activity. Some repos may repeat if they keep gaining momentum, but many should change because the event stream changed.",
            "",
            "Use a new dated raw-data folder for each run. If you keep adding files to the same directory, RepoRadar will analyze the combined old and new data.",
            "",
            "The practical user value is a weekly discovery brief: instead of browsing GitHub Trending manually, a user can ask RepoRadar for fresh candidates by category, hide noisy repos, and inspect a short list of emerging projects.",
            "",
            "Typical weekly flow:",
            "",
            "```bash",
            "PYTHONPATH=src python3 -m reporadar fetch-range --start-date YYYY-MM-DD --end-date YYYY-MM-DD --hours 0 1 2 --output data/raw/gharchive/YYYY-MM-DD",
            "PYTHONPATH=src python3 -m reporadar rank --input data/raw/gharchive/YYYY-MM-DD --model outputs/gharchive_ranker.json --observation-hours 2 --target-hours 1 --output outputs/gharchive_rankings.csv",
            "PYTHONPATH=src python3 -m reporadar enrich --rankings outputs/gharchive_rankings.csv --output data/processed/enriched_repos.csv --top 50",
            "PYTHONPATH=src python3 -m reporadar categorize --input data/processed/enriched_repos.csv --output outputs/discovery.csv",
            "PYTHONPATH=src python3 -m reporadar report --input outputs/discovery.csv --output reports/discovery_report.md",
            "```",
            "",
            "## Model Notes",
            "",
            "- `discovery_score` combines model momentum, metadata quality, and noise penalties.",
            "- `quality_score` rewards useful metadata such as description, topics, README, license, language, stars, forks, PRs, and issues.",
            "- `noise_score` penalizes signals common in test repos, image beds, personal pages, logs, backups, and generated content.",
            "- `personal_content_noise` catches test repos, image beds, logs, blogs, and similar low-discovery-value repos.",
            "- `Near Misses To Debug` shows repos that the filters removed even though they had momentum or useful metadata.",
            "- This report is generated from a small top-N enrichment pass, so results improve as more ranked repos are enriched.",
            "",
        ]
    )

    return "\n".join(lines)


def write_report(markdown: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown, encoding="utf-8")


def candidate_card(row: dict[str, str], index: int) -> list[str]:
    repo = row.get("repo_name", "")
    url = row.get("html_url", "")
    repo_title = f"[{repo}]({url})" if url else f"`{repo}`"
    description = row.get("description", "").strip() or "No description available."
    topics = format_topics(row.get("topics", ""))
    language = row.get("primary_language", "").strip() or "unknown"
    license_key = row.get("license_key", "").strip() or "unknown"

    return [
        f"### {index}. {repo_title}",
        "",
        f"- Category: `{row.get('category', '')}`",
        f"- Why it surfaced: {row.get('category_reason', '')}",
        f"- Human review: {format_human_review(row)}",
        f"- Scores: discovery `{as_float(row, 'discovery_score'):.3f}`, quality `{as_float(row, 'quality_score'):.3f}`, noise `{as_float(row, 'noise_score'):.3f}`, confidence `{as_float(row, 'category_confidence'):.3f}`",
        f"- Description: {description}",
        f"- Metadata: language `{language}`, license `{license_key}`, stars `{as_int(row, 'stargazers_count')}`, forks `{as_int(row, 'forks_count')}`, open issues `{as_int(row, 'open_issues_count')}`",
        f"- Topics: {topics}",
        "- Next review action: keep / reject / relabel?",
        "",
    ]


def passes_report_filters(row: dict[str, str], min_quality: float, max_noise: float) -> bool:
    return not filter_reasons(row, min_quality, max_noise)


def find_near_misses(
    rows: list[dict[str, str]],
    min_quality: float,
    max_noise: float,
    limit: int,
) -> list[dict[str, str]]:
    candidates = []
    for row in rows:
        if passes_report_filters(row, min_quality, max_noise):
            continue
        if as_float(row, "discovery_score") >= 18 or as_float(row, "quality_score") >= min_quality:
            candidates.append(row)
    candidates.sort(key=lambda row: (-as_float(row, "discovery_score"), -as_float(row, "quality_score")))
    return candidates[:limit]


def filter_reasons(row: dict[str, str], min_quality: float, max_noise: float) -> list[str]:
    reasons = []
    category = row.get("category", "uncategorized")
    quality = as_float(row, "quality_score")
    noise = as_float(row, "noise_score")

    if category == "personal_content_noise":
        reasons.append("noise category")
    if category == "uncategorized":
        reasons.append("uncategorized")
    if quality < min_quality:
        reasons.append(f"quality {quality:.3f} below min {min_quality:.3f}")
    if noise > max_noise:
        reasons.append(f"noise {noise:.3f} above max {max_noise:.3f}")
    return reasons


def near_miss_row(row: dict[str, str], min_quality: float, max_noise: float) -> str:
    repo = row.get("repo_name", "")
    url = row.get("html_url", "")
    repo_text = f"[{repo}]({url})" if url else f"`{repo}`"
    reasons = "; ".join(filter_reasons(row, min_quality, max_noise))
    return (
        f"| {repo_text} | `{row.get('category', '')}` | "
        f"{as_float(row, 'discovery_score'):.3f} | "
        f"{as_float(row, 'quality_score'):.3f} | "
        f"{as_float(row, 'noise_score'):.3f} | {reasons} |"
    )


def as_float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    if value in ("", None):
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def as_int(row: dict[str, str], key: str) -> int:
    return int(as_float(row, key))


def format_topics(value: str) -> str:
    topics = [topic for topic in value.split(";") if topic]
    if not topics:
        return "none"
    return ", ".join(f"`{topic}`" for topic in topics[:8])


def human_review_count(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if row.get("human_label"))


def format_human_review(row: dict[str, str]) -> str:
    label = row.get("human_label", "").strip()
    if not label:
        return "not reviewed yet"
    reason = row.get("human_reason", "").strip()
    reviewed_at = row.get("reviewed_at", "").strip()
    suffix = f" on {reviewed_at}" if reviewed_at else ""
    if reason:
        return f"`{label}`{suffix} - {reason}"
    return f"`{label}`{suffix}"
