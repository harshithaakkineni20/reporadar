from __future__ import annotations

from collections.abc import Callable
from math import log2
from typing import Any

from reporadar.features import baseline_score


EXPLANATION_SIGNALS = (
    ("stars", "star growth"),
    ("forks", "fork growth"),
    ("unique_actors", "many unique actors"),
    ("pull_requests_opened", "pull request activity"),
    ("issues_opened", "issue activity"),
    ("commits", "commit burst"),
    ("releases", "release activity"),
    ("activity_velocity", "fast event velocity"),
)


def rank_repositories(
    rows: list[dict[str, Any]],
    scorer: Callable[[dict[str, Any]], float] | None = None,
) -> list[dict[str, Any]]:
    """Attach scores, ranks, and short explanations."""
    scored = []
    for row in rows:
        enriched = dict(row)
        enriched["score"] = round(float(scorer(row) if scorer else baseline_score(row)), 4)
        enriched["why"] = explain_row(row)
        scored.append(enriched)

    scored.sort(key=lambda item: (-float(item["score"]), item["repo_name"]))
    for index, row in enumerate(scored, start=1):
        row["rank"] = index
    return scored


def explain_row(row: dict[str, Any], max_reasons: int = 4) -> str:
    """Create a compact explanation from the strongest non-zero feature signals."""
    signals: list[tuple[float, str]] = []
    for key, label in EXPLANATION_SIGNALS:
        value = float(row.get(key) or 0)
        if value > 0:
            signals.append((value, label))

    signals.sort(reverse=True)
    reasons = [label for _, label in signals[:max_reasons]]
    if not reasons:
        return "limited observed activity"
    return ", ".join(reasons)


def precision_at_k(rows: list[dict[str, Any]], k: int) -> float:
    """Measure how many of the top-k repos had future growth."""
    if k <= 0:
        raise ValueError("k must be positive")
    top = rows[:k]
    if not top:
        return 0.0
    hits = sum(1 for row in top if float(row.get("future_growth") or 0) > 0)
    return hits / len(top)


def recall_at_k(rows: list[dict[str, Any]], k: int) -> float:
    """Measure how much future-growth signal appears in the top-k."""
    total_relevant = sum(1 for row in rows if float(row.get("future_growth") or 0) > 0)
    if total_relevant == 0:
        return 0.0
    hits = sum(1 for row in rows[:k] if float(row.get("future_growth") or 0) > 0)
    return hits / total_relevant


def ndcg_at_k(rows: list[dict[str, Any]], k: int) -> float:
    """Measure ranking quality using future_growth as graded relevance."""
    if k <= 0:
        raise ValueError("k must be positive")

    def dcg(relevances: list[float]) -> float:
        return sum((rel / log2(index + 2)) for index, rel in enumerate(relevances))

    observed = [float(row.get("future_growth") or 0) for row in rows[:k]]
    ideal = sorted((float(row.get("future_growth") or 0) for row in rows), reverse=True)[:k]
    ideal_dcg = dcg(ideal)
    if ideal_dcg == 0:
        return 0.0
    return dcg(observed) / ideal_dcg
