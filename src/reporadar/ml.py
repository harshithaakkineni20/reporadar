from __future__ import annotations

import json
import random
from dataclasses import dataclass
from math import exp
from pathlib import Path
from typing import Any


FEATURE_COLUMNS = [
    "stars",
    "forks",
    "issues_opened",
    "pull_requests_opened",
    "pushes",
    "commits",
    "releases",
    "creates",
    "observed_events",
    "unique_actors",
    "activity_velocity",
]


def as_float(row: dict[str, Any], key: str) -> float:
    value = row.get(key, 0)
    if value in ("", None):
        return 0.0
    return float(value)


def sigmoid(value: float) -> float:
    if value >= 0:
        z = exp(-value)
        return 1 / (1 + z)
    z = exp(value)
    return z / (1 + z)


@dataclass
class FeatureScaler:
    means: dict[str, float]
    stds: dict[str, float]

    @classmethod
    def fit(cls, rows: list[dict[str, Any]], feature_columns: list[str]) -> "FeatureScaler":
        means: dict[str, float] = {}
        stds: dict[str, float] = {}
        for column in feature_columns:
            values = [as_float(row, column) for row in rows]
            mean = sum(values) / len(values)
            variance = sum((value - mean) ** 2 for value in values) / len(values)
            std = variance**0.5
            means[column] = mean
            stds[column] = std if std > 1e-12 else 1.0
        return cls(means=means, stds=stds)

    def transform_row(self, row: dict[str, Any], feature_columns: list[str]) -> list[float]:
        return [
            (as_float(row, column) - self.means[column]) / self.stds[column]
            for column in feature_columns
        ]


@dataclass
class PairwiseLinearRanker:
    feature_columns: list[str]
    weights: list[float]
    scaler: FeatureScaler

    def score(self, row: dict[str, Any]) -> float:
        vector = self.scaler.transform_row(row, self.feature_columns)
        return sum(weight * value for weight, value in zip(self.weights, vector, strict=True))

    def feature_importance(self) -> list[tuple[str, float]]:
        pairs = list(zip(self.feature_columns, self.weights, strict=True))
        return sorted(pairs, key=lambda item: abs(item[1]), reverse=True)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "kind": "pairwise_linear_ranker",
            "version": 1,
            "feature_columns": self.feature_columns,
            "weights": self.weights,
            "scaler": {
                "means": self.scaler.means,
                "stds": self.scaler.stds,
            },
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "PairwiseLinearRanker":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("kind") != "pairwise_linear_ranker":
            raise ValueError(f"Unsupported model kind in {path}")
        scaler = FeatureScaler(
            means={key: float(value) for key, value in payload["scaler"]["means"].items()},
            stds={key: float(value) for key, value in payload["scaler"]["stds"].items()},
        )
        return cls(
            feature_columns=list(payload["feature_columns"]),
            weights=[float(value) for value in payload["weights"]],
            scaler=scaler,
        )


def train_pairwise_ranker(
    rows: list[dict[str, Any]],
    epochs: int = 250,
    learning_rate: float = 0.03,
    l2: float = 0.001,
    max_pairs: int = 50_000,
    seed: int = 7,
) -> PairwiseLinearRanker:
    """Train a simple pairwise learning-to-rank model with SGD."""
    if not rows:
        raise ValueError("Cannot train on an empty dataset")

    scaler = FeatureScaler.fit(rows, FEATURE_COLUMNS)
    vectors = [scaler.transform_row(row, FEATURE_COLUMNS) for row in rows]
    pairs = build_training_pairs(rows, max_pairs=max_pairs, seed=seed)
    if not pairs:
        raise ValueError("Need rows with different future_growth values to train a ranker")

    rng = random.Random(seed)
    weights = [0.0 for _ in FEATURE_COLUMNS]

    for _ in range(epochs):
        rng.shuffle(pairs)
        for winner_index, loser_index in pairs:
            winner = vectors[winner_index]
            loser = vectors[loser_index]
            diff = [left - right for left, right in zip(winner, loser, strict=True)]
            margin = sum(weight * value for weight, value in zip(weights, diff, strict=True))
            gradient_scale = sigmoid(margin) - 1.0
            for index, value in enumerate(diff):
                gradient = gradient_scale * value + (l2 * weights[index])
                weights[index] -= learning_rate * gradient

    return PairwiseLinearRanker(
        feature_columns=list(FEATURE_COLUMNS),
        weights=weights,
        scaler=scaler,
    )


def build_training_pairs(
    rows: list[dict[str, Any]],
    max_pairs: int = 50_000,
    seed: int = 7,
) -> list[tuple[int, int]]:
    """Build winner/loser pairs, preferably comparing repos inside the same time window."""
    groups: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        groups.setdefault(str(row.get("window_id") or "__all__"), []).append(index)

    pairs: list[tuple[int, int]] = []
    for indices in groups.values():
        for left_pos, left_index in enumerate(indices):
            left_growth = as_float(rows[left_index], "future_growth")
            for right_index in indices[left_pos + 1 :]:
                right_growth = as_float(rows[right_index], "future_growth")
                if left_growth == right_growth:
                    continue
                if left_growth > right_growth:
                    pairs.append((left_index, right_index))
                else:
                    pairs.append((right_index, left_index))

    rng = random.Random(seed)
    rng.shuffle(pairs)
    return pairs[:max_pairs]


def pairwise_accuracy(rows: list[dict[str, Any]], model: PairwiseLinearRanker) -> float:
    pairs = build_training_pairs(rows, max_pairs=100_000, seed=1)
    if not pairs:
        return 0.0
    hits = 0
    for winner_index, loser_index in pairs:
        if model.score(rows[winner_index]) > model.score(rows[loser_index]):
            hits += 1
    return hits / len(pairs)
