from __future__ import annotations

import unittest

from reporadar.reporting import build_discovery_report


class ReportingTests(unittest.TestCase):
    def test_build_discovery_report_contains_summary_and_top_repo(self) -> None:
        rows = [
            {
                "repo_name": "hyperspaceai/agi",
                "html_url": "https://github.com/hyperspaceai/agi",
                "category": "ai_ml_data",
                "discovery_score": "39.239",
                "quality_score": "13.8",
                "noise_score": "1.5",
                "category_reason": "matched: ai, llm, agent",
                "human_label": "keep",
                "human_reason": "Active and interesting AI repo.",
                "reviewed_at": "2026-05-12",
            },
            {
                "repo_name": "user/my-img-bed",
                "category": "personal_content_noise",
                "discovery_score": "20",
                "quality_score": "0",
                "noise_score": "5.5",
                "category_reason": "noise indicators: img",
            },
        ]

        markdown = build_discovery_report(rows, source_name="outputs/discovery.csv", top=5)

        self.assertIn("# RepoRadar Discovery Review", markdown)
        self.assertIn("Repositories analyzed: 2", markdown)
        self.assertIn("How To Read This", markdown)
        self.assertIn("[hyperspaceai/agi]", markdown)
        self.assertIn("personal_content_noise", markdown)
        self.assertIn("Human-reviewed candidates: 1", markdown)
        self.assertIn("Human review: `keep`", markdown)
        self.assertIn("Next review action: keep / reject / relabel?", markdown)
        self.assertIn("If You Run This Again Next Week", markdown)


if __name__ == "__main__":
    unittest.main()
