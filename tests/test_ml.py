from __future__ import annotations

import unittest

from reporadar.features import build_dataset_rows, parse_github_time
from reporadar.ml import pairwise_accuracy, train_pairwise_ranker
from reporadar.ranking import ndcg_at_k, rank_repositories


class RankingModelTests(unittest.TestCase):
    def test_pairwise_ranker_learns_future_growth_order(self) -> None:
        rows = [
            {
                "window_id": "w1",
                "repo_name": "future/winner",
                "stars": 3,
                "forks": 1,
                "issues_opened": 1,
                "pull_requests_opened": 1,
                "pushes": 1,
                "commits": 5,
                "releases": 0,
                "creates": 0,
                "observed_events": 5,
                "unique_actors": 4,
                "activity_velocity": 2.0,
                "future_growth": 2.0,
            },
            {
                "window_id": "w1",
                "repo_name": "future/loser",
                "stars": 0,
                "forks": 0,
                "issues_opened": 0,
                "pull_requests_opened": 0,
                "pushes": 1,
                "commits": 1,
                "releases": 0,
                "creates": 0,
                "observed_events": 1,
                "unique_actors": 1,
                "activity_velocity": 0.5,
                "future_growth": 0.0,
            },
        ]

        model = train_pairwise_ranker(rows, epochs=50, learning_rate=0.05)
        ranked = rank_repositories(rows, scorer=model.score)

        self.assertEqual(ranked[0]["repo_name"], "future/winner")
        self.assertEqual(pairwise_accuracy(rows, model), 1.0)
        self.assertEqual(ndcg_at_k(ranked, 1), 1.0)

    def test_build_dataset_rows_adds_window_metadata(self) -> None:
        events = [
            {
                "type": "WatchEvent",
                "actor": {"login": "a"},
                "repo": {"id": 1, "name": "demo/repo"},
                "payload": {"action": "started"},
                "created_at": "2026-05-11T01:00:00Z",
            },
            {
                "type": "WatchEvent",
                "actor": {"login": "b"},
                "repo": {"id": 1, "name": "demo/repo"},
                "payload": {"action": "started"},
                "created_at": "2026-05-11T03:00:00Z",
            },
        ]

        rows = build_dataset_rows(
            events,
            cutoffs=[parse_github_time("2026-05-11T02:00:00Z")],
            observation_hours=2,
            target_hours=2,
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["window_id"], "2026-05-11T02:00:00Z")
        self.assertEqual(rows[0]["future_stars"], 1)


if __name__ == "__main__":
    unittest.main()
