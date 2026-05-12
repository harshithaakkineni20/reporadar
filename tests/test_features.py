from __future__ import annotations

import unittest

from reporadar.features import build_feature_rows, parse_github_time
from reporadar.ranking import precision_at_k, rank_repositories


class FeatureTests(unittest.TestCase):
    def test_build_feature_rows_splits_observed_and_future_events(self) -> None:
        events = [
            {
                "type": "WatchEvent",
                "actor": {"login": "a"},
                "repo": {"id": 1, "name": "demo/repo"},
                "payload": {"action": "started"},
                "created_at": "2026-05-11T01:00:00Z",
            },
            {
                "type": "PushEvent",
                "actor": {"login": "b"},
                "repo": {"id": 1, "name": "demo/repo"},
                "payload": {"commits": [{"sha": "1"}, {"sha": "2"}]},
                "created_at": "2026-05-11T02:00:00Z",
            },
            {
                "type": "WatchEvent",
                "actor": {"login": "c"},
                "repo": {"id": 1, "name": "demo/repo"},
                "payload": {"action": "started"},
                "created_at": "2026-05-11T04:00:00Z",
            },
        ]

        rows = build_feature_rows(
            events,
            cutoff=parse_github_time("2026-05-11T02:30:00Z"),
            target_hours=24,
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["stars"], 1)
        self.assertEqual(rows[0]["commits"], 2)
        self.assertEqual(rows[0]["unique_actors"], 2)
        self.assertEqual(rows[0]["future_stars"], 1)

    def test_ranking_prefers_stronger_observed_signal(self) -> None:
        rows = [
            {
                "repo_name": "quiet/repo",
                "stars": 0,
                "forks": 0,
                "unique_actors": 1,
                "issues_opened": 0,
                "pull_requests_opened": 0,
                "commits": 1,
                "releases": 0,
                "activity_velocity": 0.2,
                "future_growth": 0,
            },
            {
                "repo_name": "loud/repo",
                "stars": 4,
                "forks": 1,
                "unique_actors": 5,
                "issues_opened": 2,
                "pull_requests_opened": 1,
                "commits": 8,
                "releases": 1,
                "activity_velocity": 2.0,
                "future_growth": 1,
            },
        ]

        ranked = rank_repositories(rows)

        self.assertEqual(ranked[0]["repo_name"], "loud/repo")
        self.assertEqual(precision_at_k(ranked, 1), 1.0)


if __name__ == "__main__":
    unittest.main()
