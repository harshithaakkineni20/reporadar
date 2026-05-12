from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from reporadar.features import build_feature_rows, infer_cutoff, parse_github_time
from reporadar.gharchive import fetch_archive, iter_events
from reporadar.io import read_rankings_csv, write_rankings_csv
from reporadar.ranking import precision_at_k, rank_repositories, recall_at_k


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reporadar",
        description="Rank GitHub repositories by early momentum signals.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="Download GH Archive hourly files.")
    fetch_parser.add_argument("--date", required=True, help="UTC date in YYYY-MM-DD format.")
    fetch_parser.add_argument("--hours", nargs="+", type=int, required=True, help="UTC hours 0-23.")
    fetch_parser.add_argument("--output", type=Path, default=Path("data/raw/gharchive"))
    fetch_parser.set_defaults(func=fetch_command)

    rank_parser = subparsers.add_parser("rank", help="Build features and rank repositories.")
    add_input_args(rank_parser)
    rank_parser.add_argument("--output", type=Path, default=Path("outputs/rankings.csv"))
    rank_parser.add_argument("--top", type=int, default=10)
    rank_parser.set_defaults(func=rank_command)

    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate ranking against future growth.")
    add_input_args(evaluate_parser)
    evaluate_parser.add_argument("--top-k", type=int, default=10)
    evaluate_parser.set_defaults(func=evaluate_command)

    explain_parser = subparsers.add_parser("explain", help="Explain one repo from a rankings CSV.")
    explain_parser.add_argument("--rankings", type=Path, default=Path("outputs/rankings.csv"))
    explain_parser.add_argument("--repo", required=True)
    explain_parser.set_defaults(func=explain_command)

    return parser


def add_input_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--input",
        nargs="+",
        type=Path,
        required=True,
        help="One or more JSON/JSONL/JSON.GZ event files or directories.",
    )
    parser.add_argument(
        "--cutoff",
        help="Observation cutoff timestamp, for example 2026-05-11T12:00:00Z. "
        "If omitted, RepoRadar infers a cutoff inside the event timeline.",
    )
    parser.add_argument(
        "--target-hours",
        type=int,
        default=168,
        help="Future label window after cutoff. Defaults to 168 hours.",
    )


def fetch_command(args: argparse.Namespace) -> None:
    day = date.fromisoformat(args.date)
    downloaded = []
    for hour in args.hours:
        downloaded.append(fetch_archive(day, hour, args.output))

    print(f"Downloaded {len(downloaded)} archive file(s):")
    for path in downloaded:
        print(f"- {path}")


def load_rows(args: argparse.Namespace) -> list[dict]:
    events = list(iter_events(args.input))
    if not events:
        raise SystemExit("No events found.")

    cutoff = parse_github_time(args.cutoff) if args.cutoff else infer_cutoff(events)
    rows = build_feature_rows(events, cutoff=cutoff, target_hours=args.target_hours)
    if not rows:
        raise SystemExit("No repositories had observed activity before the cutoff.")
    return rank_repositories(rows)


def rank_command(args: argparse.Namespace) -> None:
    ranked = load_rows(args)
    write_rankings_csv(ranked, args.output)

    print(f"Wrote {len(ranked)} ranked repositories to {args.output}")
    print()
    print(f"Top {min(args.top, len(ranked))}:")
    for row in ranked[: args.top]:
        print(
            f"{row['rank']:>2}. {row['repo_name']} "
            f"score={row['score']} future_growth={row['future_growth']} why={row['why']}"
        )


def evaluate_command(args: argparse.Namespace) -> None:
    ranked = load_rows(args)
    top_k = min(args.top_k, len(ranked))
    precision = precision_at_k(ranked, top_k)
    recall = recall_at_k(ranked, top_k)

    print(f"repos={len(ranked)}")
    print(f"top_k={top_k}")
    print(f"precision_at_k={precision:.3f}")
    print(f"recall_at_k={recall:.3f}")
    print()
    print("Top repos:")
    for row in ranked[:top_k]:
        print(
            f"- {row['repo_name']}: score={row['score']}, "
            f"future_growth={row['future_growth']}, why={row['why']}"
        )


def explain_command(args: argparse.Namespace) -> None:
    rows = read_rankings_csv(args.rankings)
    matches = [row for row in rows if row.get("repo_name") == args.repo]
    if not matches:
        raise SystemExit(f"Repo not found in rankings: {args.repo}")

    row = matches[0]
    print(f"{row['repo_name']} ranked #{row['rank']} with score {row['score']}")
    print(f"Why: {row['why']}")
    print(
        "Signals: "
        f"stars={row['stars']}, forks={row['forks']}, actors={row['unique_actors']}, "
        f"PRs={row['pull_requests_opened']}, issues={row['issues_opened']}, "
        f"velocity={row['activity_velocity']}"
    )
    print(f"Future growth label: {row['future_growth']}")
