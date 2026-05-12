from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from reporadar.emailer import build_weekly_digest
from reporadar.history import append_run_history


class EmailerTests(unittest.TestCase):
    def test_build_weekly_digest_contains_top_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history_dir = Path(tmp)
            append_run_history(
                run_date="2026-05-11",
                summary={
                    "events": "886405",
                    "training_rows": "377522",
                    "ranked_repos": "135165",
                    "enriched_repos": "50",
                    "report": "report.md",
                },
                discovery_rows=[
                    {
                        "repo_name": "hyperspaceai/agi",
                        "category": "ai_ml_data",
                        "discovery_score": "39.239",
                        "quality_score": "13.8",
                        "noise_score": "1.5",
                        "html_url": "https://github.com/hyperspaceai/agi",
                        "description": "Distributed AGI system.",
                    }
                ],
                history_dir=history_dir,
            )

            subject, body = build_weekly_digest(history_dir)

            self.assertIn("2026-05-11", subject)
            self.assertIn("hyperspaceai/agi", body)
            self.assertIn("886405", body)
            self.assertIn("[new]", body)


if __name__ == "__main__":
    unittest.main()
