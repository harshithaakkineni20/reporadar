from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reporadar.history import append_run_history, discoveries_for_run, repo_timeline


class HistoryTests(unittest.TestCase):
    def test_append_history_replaces_same_run_and_computes_trend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history_dir = Path(tmp)
            append_run_history(
                run_date="2026-05-11",
                summary={
                    "events": "100",
                    "training_rows": "50",
                    "ranked_repos": "20",
                    "enriched_repos": "2",
                    "report": "runs/reporadar/2026-05-11/discovery_report.md",
                },
                discovery_rows=[
                    {
                        "repo_name": "demo/repo",
                        "rank": "2",
                        "category": "ai_ml_data",
                        "discovery_score": "20",
                        "quality_score": "10",
                        "noise_score": "1",
                    }
                ],
                history_dir=history_dir,
            )
            append_run_history(
                run_date="2026-05-18",
                summary={
                    "events": "120",
                    "training_rows": "60",
                    "ranked_repos": "25",
                    "enriched_repos": "2",
                    "report": "runs/reporadar/2026-05-18/discovery_report.md",
                },
                discovery_rows=[
                    {
                        "repo_name": "demo/repo",
                        "rank": "1",
                        "category": "ai_ml_data",
                        "discovery_score": "25",
                        "quality_score": "11",
                        "noise_score": "1",
                    }
                ],
                history_dir=history_dir,
            )

            latest = discoveries_for_run(history_dir, run_date="2026-05-18")
            timeline = repo_timeline(history_dir, "demo/repo")

            self.assertEqual(len(latest), 1)
            self.assertEqual(latest[0]["previous_rank"], "2")
            self.assertEqual(latest[0]["discovery_delta"], "5.000")
            self.assertEqual(latest[0]["is_new"], "false")
            self.assertEqual(len(timeline), 2)

            append_run_history(
                run_date="2026-05-18",
                summary={
                    "events": "130",
                    "training_rows": "65",
                    "ranked_repos": "26",
                    "enriched_repos": "2",
                    "report": "updated.md",
                },
                discovery_rows=[
                    {
                        "repo_name": "demo/repo",
                        "rank": "3",
                        "category": "ai_ml_data",
                        "discovery_score": "22",
                        "quality_score": "11",
                        "noise_score": "1",
                    }
                ],
                history_dir=history_dir,
            )

            self.assertEqual(len(repo_timeline(history_dir, "demo/repo")), 2)


if __name__ == "__main__":
    unittest.main()
