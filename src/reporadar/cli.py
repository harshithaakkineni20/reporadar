from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from reporadar.categorize import categorize_rows
from reporadar.feedback import attach_feedback, read_feedback
from reporadar.features import (
    build_dataset_rows,
    build_feature_rows,
    generate_cutoffs,
    infer_cutoff,
    parse_github_time,
)
from reporadar.gharchive import fetch_archive, iter_dates, iter_events
from reporadar.github_api import GitHubClient, enrich_repo
from reporadar.io import (
    read_rankings_csv,
    read_rows_csv,
    write_rows_csv,
    write_dataset_csv,
    write_enriched_csv,
    write_rankings_csv,
)
from reporadar.ml import PairwiseLinearRanker, pairwise_accuracy, train_pairwise_ranker
from reporadar.ranking import ndcg_at_k, precision_at_k, rank_repositories, recall_at_k
from reporadar.reporting import build_discovery_report, write_report


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

    fetch_range_parser = subparsers.add_parser(
        "fetch-range",
        help="Download a range of GH Archive hourly files.",
    )
    fetch_range_parser.add_argument("--start-date", required=True, help="UTC date in YYYY-MM-DD.")
    fetch_range_parser.add_argument("--end-date", required=True, help="UTC date in YYYY-MM-DD.")
    fetch_range_parser.add_argument(
        "--hours",
        nargs="+",
        type=int,
        default=list(range(24)),
        help="UTC hours 0-23. Defaults to all hours.",
    )
    fetch_range_parser.add_argument("--output", type=Path, default=Path("data/raw/gharchive"))
    fetch_range_parser.set_defaults(func=fetch_range_command)

    dataset_parser = subparsers.add_parser(
        "dataset",
        help="Create rolling feature/label rows for ML training.",
    )
    dataset_parser.add_argument(
        "--input",
        nargs="+",
        type=Path,
        required=True,
        help="One or more JSON/JSONL/JSON.GZ event files or directories.",
    )
    dataset_parser.add_argument("--output", type=Path, default=Path("data/processed/training_rows.csv"))
    dataset_parser.add_argument(
        "--cutoffs",
        nargs="*",
        help="Optional cutoff timestamps. If omitted, RepoRadar creates rolling windows.",
    )
    dataset_parser.add_argument("--observation-hours", type=int, default=8)
    dataset_parser.add_argument("--target-hours", type=int, default=6)
    dataset_parser.add_argument("--stride-hours", type=int, default=3)
    dataset_parser.set_defaults(func=dataset_command)

    train_parser = subparsers.add_parser("train", help="Train a pairwise ML ranking model.")
    train_parser.add_argument("--dataset", type=Path, required=True)
    train_parser.add_argument("--model", type=Path, default=Path("outputs/reporadar_ranker.json"))
    train_parser.add_argument("--epochs", type=int, default=250)
    train_parser.add_argument("--learning-rate", type=float, default=0.03)
    train_parser.add_argument("--l2", type=float, default=0.001)
    train_parser.add_argument("--max-pairs", type=int, default=50_000)
    train_parser.set_defaults(func=train_command)

    rank_parser = subparsers.add_parser("rank", help="Build features and rank repositories.")
    add_input_args(rank_parser)
    rank_parser.add_argument("--output", type=Path, default=Path("outputs/rankings.csv"))
    rank_parser.add_argument("--model", type=Path, help="Optional trained model JSON.")
    rank_parser.add_argument("--top", type=int, default=10)
    rank_parser.set_defaults(func=rank_command)

    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate ranking against future growth.")
    add_input_args(evaluate_parser)
    evaluate_parser.add_argument("--model", type=Path, help="Optional trained model JSON.")
    evaluate_parser.add_argument("--top-k", type=int, default=10)
    evaluate_parser.set_defaults(func=evaluate_command)

    explain_parser = subparsers.add_parser("explain", help="Explain one repo from a rankings CSV.")
    explain_parser.add_argument("--rankings", type=Path, default=Path("outputs/rankings.csv"))
    explain_parser.add_argument("--repo", required=True)
    explain_parser.set_defaults(func=explain_command)

    enrich_parser = subparsers.add_parser(
        "enrich",
        help="Fetch GitHub metadata for ranked repositories.",
    )
    enrich_parser.add_argument("--rankings", type=Path, required=True)
    enrich_parser.add_argument("--output", type=Path, default=Path("data/processed/enriched_repos.csv"))
    enrich_parser.add_argument("--top", type=int, default=30)
    enrich_parser.add_argument("--readme-chars", type=int, default=2500)
    enrich_parser.add_argument(
        "--skip-readme",
        action="store_true",
        help="Skip README fetches to reduce API calls.",
    )
    enrich_parser.set_defaults(func=enrich_command)

    categorize_parser = subparsers.add_parser(
        "categorize",
        help="Categorize enriched repos into discovery use cases.",
    )
    categorize_parser.add_argument("--input", type=Path, required=True)
    categorize_parser.add_argument("--output", type=Path, default=Path("outputs/discovery.csv"))
    categorize_parser.set_defaults(func=categorize_command)

    discover_parser = subparsers.add_parser(
        "discover",
        help="Show category-specific discovery leaderboards.",
    )
    discover_parser.add_argument("--input", type=Path, required=True)
    discover_parser.add_argument("--category", default="all")
    discover_parser.add_argument("--top", type=int, default=10)
    discover_parser.add_argument("--hide-noise", action="store_true")
    discover_parser.add_argument("--hide-uncategorized", action="store_true")
    discover_parser.add_argument("--min-quality", type=float, default=0.0)
    discover_parser.add_argument("--max-noise", type=float)
    discover_parser.add_argument("--min-confidence", type=float, default=0.0)
    discover_parser.set_defaults(func=discover_command)

    report_parser = subparsers.add_parser(
        "report",
        help="Generate a Markdown report from categorized discovery results.",
    )
    report_parser.add_argument("--input", type=Path, required=True)
    report_parser.add_argument("--output", type=Path, default=Path("reports/discovery_report.md"))
    report_parser.add_argument("--top", type=int, default=10)
    report_parser.add_argument("--min-quality", type=float, default=5.0)
    report_parser.add_argument("--max-noise", type=float, default=3.5)
    report_parser.add_argument("--labels", type=Path, help="Optional human review labels CSV.")
    report_parser.set_defaults(func=report_command)

    continuous_parser = subparsers.add_parser(
        "continuous",
        help="Run the full scheduled discovery pipeline for one date.",
    )
    continuous_parser.add_argument(
        "--run-date",
        help="UTC date to analyze. Defaults to yesterday UTC.",
    )
    continuous_parser.add_argument(
        "--hours",
        nargs="+",
        type=int,
        default=[0, 1, 2, 3, 4, 5],
        help="UTC hours to fetch. Defaults to 0-5.",
    )
    continuous_parser.add_argument("--workspace", type=Path, default=Path("runs/reporadar"))
    continuous_parser.add_argument("--top", type=int, default=50)
    continuous_parser.add_argument("--observation-hours", type=int, default=2)
    continuous_parser.add_argument("--target-hours", type=int, default=1)
    continuous_parser.add_argument("--stride-hours", type=int, default=1)
    continuous_parser.add_argument("--epochs", type=int, default=50)
    continuous_parser.add_argument("--max-pairs", type=int, default=10_000)
    continuous_parser.add_argument("--min-quality", type=float, default=5.0)
    continuous_parser.add_argument("--max-noise", type=float, default=3.5)
    continuous_parser.add_argument("--labels", type=Path, default=Path("data/labels/review_labels.csv"))
    continuous_parser.add_argument("--skip-readme", action="store_true")
    continuous_parser.set_defaults(func=continuous_command)

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
    parser.add_argument(
        "--observation-hours",
        type=int,
        help="Trailing feature window before cutoff. Defaults to all observed history.",
    )


def fetch_command(args: argparse.Namespace) -> None:
    day = date.fromisoformat(args.date)
    downloaded = []
    for hour in args.hours:
        downloaded.append(fetch_archive(day, hour, args.output))

    print(f"Downloaded {len(downloaded)} archive file(s):")
    for path in downloaded:
        print(f"- {path}")


def fetch_range_command(args: argparse.Namespace) -> None:
    start = date.fromisoformat(args.start_date)
    end = date.fromisoformat(args.end_date)
    downloaded = []
    for day in iter_dates(start, end):
        for hour in args.hours:
            downloaded.append(fetch_archive(day, hour, args.output))

    print(f"Downloaded {len(downloaded)} archive file(s) to {args.output}")


def dataset_command(args: argparse.Namespace) -> None:
    events = list(iter_events(args.input))
    if not events:
        raise SystemExit("No events found.")

    if args.cutoffs:
        cutoffs = [parse_github_time(value) for value in args.cutoffs]
    else:
        cutoffs = generate_cutoffs(
            events,
            observation_hours=args.observation_hours,
            target_hours=args.target_hours,
            stride_hours=args.stride_hours,
        )

    rows = build_dataset_rows(
        events,
        cutoffs=cutoffs,
        observation_hours=args.observation_hours,
        target_hours=args.target_hours,
    )
    if not rows:
        raise SystemExit("No dataset rows created. Try wider observation/target windows.")

    write_dataset_csv(rows, args.output)
    positives = sum(1 for row in rows if float(row.get("future_growth") or 0) > 0)
    print(f"Wrote {len(rows)} dataset rows across {len(cutoffs)} cutoff window(s) to {args.output}")
    print(f"positive_rows={positives}")


def train_command(args: argparse.Namespace) -> None:
    rows = read_rows_csv(args.dataset)
    model = train_pairwise_ranker(
        rows,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        l2=args.l2,
        max_pairs=args.max_pairs,
    )
    model.save(args.model)

    print(f"Wrote trained pairwise ranker to {args.model}")
    print(f"training_pairwise_accuracy={pairwise_accuracy(rows, model):.3f}")
    print("Top learned weights:")
    for feature, weight in model.feature_importance()[:6]:
        print(f"- {feature}: {weight:.4f}")


def load_rows(args: argparse.Namespace) -> list[dict]:
    events = list(iter_events(args.input))
    if not events:
        raise SystemExit("No events found.")

    cutoff = parse_github_time(args.cutoff) if args.cutoff else infer_cutoff(events)
    rows = build_feature_rows(
        events,
        cutoff=cutoff,
        target_hours=args.target_hours,
        observation_hours=args.observation_hours,
    )
    if not rows:
        raise SystemExit("No repositories had observed activity before the cutoff.")
    model = load_model(args.model) if getattr(args, "model", None) else None
    return rank_repositories(rows, scorer=model.score if model else None)


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
    ndcg = ndcg_at_k(ranked, top_k)

    print(f"repos={len(ranked)}")
    print(f"top_k={top_k}")
    print(f"precision_at_k={precision:.3f}")
    print(f"recall_at_k={recall:.3f}")
    print(f"ndcg_at_k={ndcg:.3f}")
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


def enrich_command(args: argparse.Namespace) -> None:
    rows = read_rankings_csv(args.rankings)
    if args.top > 0:
        rows = rows[: args.top]
    if not rows:
        raise SystemExit("No ranking rows found.")

    client = GitHubClient.from_environment()
    enriched_rows = []
    for index, row in enumerate(rows, start=1):
        repo_name = row.get("repo_name", "")
        metadata = enrich_repo(
            repo_name,
            client=client,
            include_readme=not args.skip_readme,
            readme_chars=args.readme_chars,
        )
        enriched = dict(row)
        enriched.update(metadata)
        enriched_rows.append(enriched)
        print(f"[{index}/{len(rows)}] enriched {repo_name}")

    write_enriched_csv(enriched_rows, args.output)
    print(f"Wrote {len(enriched_rows)} enriched repos to {args.output}")


def categorize_command(args: argparse.Namespace) -> None:
    rows = read_rows_csv(args.input)
    if not rows:
        raise SystemExit("No rows found.")

    categorized = categorize_rows(rows)
    categorized.sort(key=lambda row: -float(row.get("discovery_score") or 0))
    write_enriched_csv(categorized, args.output)

    categories = sorted({row["category"] for row in categorized})
    print(f"Wrote {len(categorized)} categorized repos to {args.output}")
    print("Categories:")
    for category in categories:
        count = sum(1 for row in categorized if row["category"] == category)
        print(f"- {category}: {count}")


def discover_command(args: argparse.Namespace) -> None:
    rows = read_rows_csv(args.input)
    if not rows:
        raise SystemExit("No rows found.")

    if args.hide_noise:
        rows = [row for row in rows if row.get("category") != "personal_content_noise"]
    if args.hide_uncategorized:
        rows = [row for row in rows if row.get("category") != "uncategorized"]
    rows = [
        row
        for row in rows
        if float(row.get("quality_score") or 0) >= args.min_quality
        and float(row.get("category_confidence") or 0) >= args.min_confidence
        and (args.max_noise is None or float(row.get("noise_score") or 0) <= args.max_noise)
    ]
    if args.category != "all":
        rows = [row for row in rows if row.get("category") == args.category]

    rows.sort(key=lambda row: -float(row.get("discovery_score") or 0))
    if args.category == "all":
        print_category_leaderboards(rows, top=args.top)
    else:
        print_repo_rows(rows[: args.top])


def print_category_leaderboards(rows: list[dict[str, str]], top: int) -> None:
    categories = []
    for row in rows:
        category = row.get("category", "uncategorized")
        if category not in categories:
            categories.append(category)

    for category in categories:
        category_rows = [row for row in rows if row.get("category") == category][:top]
        if not category_rows:
            continue
        print()
        print(f"{category}:")
        print_repo_rows(category_rows)


def print_repo_rows(rows: list[dict[str, str]]) -> None:
    for row in rows:
        print(
            f"- {row.get('repo_name')}: discovery={row.get('discovery_score')}, "
            f"quality={row.get('quality_score')}, noise={row.get('noise_score')}, "
            f"category={row.get('category')}, why={row.get('category_reason')}"
        )


def report_command(args: argparse.Namespace) -> None:
    rows = read_rows_csv(args.input)
    if not rows:
        raise SystemExit("No rows found.")
    rows = attach_feedback(rows, read_feedback(args.labels))

    markdown = build_discovery_report(
        rows,
        source_name=str(args.input),
        top=args.top,
        min_quality=args.min_quality,
        max_noise=args.max_noise,
    )
    write_report(markdown, args.output)
    print(f"Wrote discovery report to {args.output}")


def continuous_command(args: argparse.Namespace) -> None:
    run_day = (
        date.fromisoformat(args.run_date)
        if args.run_date
        else (datetime.now(timezone.utc).date() - timedelta(days=1))
    )
    run_dir = args.workspace / run_day.isoformat()
    raw_dir = run_dir / "raw"
    dataset_path = run_dir / "training_rows.csv"
    model_path = run_dir / "ranker.json"
    rankings_path = run_dir / "rankings.csv"
    enriched_path = run_dir / "enriched_repos.csv"
    discovery_path = run_dir / "discovery.csv"
    report_path = run_dir / "discovery_report.md"

    print(f"RepoRadar continuous run for {run_day.isoformat()}")
    print(f"Run directory: {run_dir}")

    print("\n[1/7] Fetch GH Archive files")
    for hour in args.hours:
        path = fetch_archive(run_day, hour, raw_dir)
        print(f"- {path}")

    print("\n[2/7] Load events")
    events = list(iter_events([raw_dir]))
    if not events:
        raise SystemExit("No events found after fetch.")
    print(f"events={len(events)}")

    print("\n[3/7] Build rolling training rows")
    cutoffs = generate_cutoffs(
        events,
        observation_hours=args.observation_hours,
        target_hours=args.target_hours,
        stride_hours=args.stride_hours,
    )
    dataset_rows = build_dataset_rows(
        events,
        cutoffs=cutoffs,
        observation_hours=args.observation_hours,
        target_hours=args.target_hours,
    )
    if not dataset_rows:
        raise SystemExit("No training rows created.")
    write_dataset_csv(dataset_rows, dataset_path)
    print(f"rows={len(dataset_rows)} cutoffs={len(cutoffs)} path={dataset_path}")

    print("\n[4/7] Train pairwise ranker")
    model = train_pairwise_ranker(
        dataset_rows,
        epochs=args.epochs,
        max_pairs=args.max_pairs,
    )
    model.save(model_path)
    print(f"model={model_path}")
    print(f"training_pairwise_accuracy={pairwise_accuracy(dataset_rows, model):.3f}")

    print("\n[5/7] Rank repositories")
    cutoff = infer_cutoff(events)
    feature_rows = build_feature_rows(
        events,
        cutoff=cutoff,
        target_hours=args.target_hours,
        observation_hours=args.observation_hours,
    )
    ranked = rank_repositories(feature_rows, scorer=model.score)
    write_rankings_csv(ranked, rankings_path)
    print(f"ranked_repos={len(ranked)} path={rankings_path}")

    print("\n[6/7] Enrich and categorize top repos")
    client = GitHubClient.from_environment()
    enriched_rows = []
    for index, row in enumerate(ranked[: args.top], start=1):
        repo_name = row.get("repo_name", "")
        metadata = enrich_repo(
            repo_name,
            client=client,
            include_readme=not args.skip_readme,
        )
        enriched = dict(row)
        enriched.update(metadata)
        enriched_rows.append(enriched)
        print(f"[{index}/{min(args.top, len(ranked))}] {repo_name}")

    write_enriched_csv(enriched_rows, enriched_path)
    categorized = categorize_rows(enriched_rows)
    categorized.sort(key=lambda row: -float(row.get("discovery_score") or 0))
    write_enriched_csv(categorized, discovery_path)
    print(f"enriched={len(enriched_rows)} discovery={discovery_path}")

    print("\n[7/7] Write report")
    labeled_rows = attach_feedback(categorized, read_feedback(args.labels))
    markdown = build_discovery_report(
        labeled_rows,
        source_name=str(discovery_path),
        top=args.top,
        min_quality=args.min_quality,
        max_noise=args.max_noise,
    )
    write_report(markdown, report_path)
    print(f"report={report_path}")

    summary_path = run_dir / "summary.txt"
    write_rows_csv(
        [
            {
                "run_date": run_day.isoformat(),
                "events": len(events),
                "training_rows": len(dataset_rows),
                "ranked_repos": len(ranked),
                "enriched_repos": len(enriched_rows),
                "report": report_path,
            }
        ],
        summary_path,
    )
    print(f"summary={summary_path}")


def load_model(path: Path) -> PairwiseLinearRanker:
    return PairwiseLinearRanker.load(path)
