from __future__ import annotations

import unittest

from reporadar.categorize import categorize_row, categorize_rows
from reporadar.github_api import split_repo_name


class CategorizationTests(unittest.TestCase):
    def test_ai_repo_gets_ai_category(self) -> None:
        row = {
            "repo_name": "vectorflux/mini-rag",
            "description": "A tiny RAG framework for local LLM agents",
            "topics": "rag;llm;vector-search;agents",
            "primary_language": "Python",
            "license_key": "mit",
            "readme_excerpt": "Build retrieval augmented generation apps with embeddings.",
            "score": "22.5",
            "stars": "8",
            "forks": "2",
            "stargazers_count": "120",
            "forks_count": "15",
            "pull_requests_opened": "1",
        }

        categorized = categorize_row(row)

        self.assertEqual(categorized["category"], "ai_ml_data")
        self.assertGreater(float(categorized["quality_score"]), 8)
        self.assertGreater(float(categorized["discovery_score"]), 10)

    def test_noisy_repo_gets_noise_category(self) -> None:
        row = {
            "repo_name": "user/my-img-bed",
            "description": "",
            "topics": "",
            "primary_language": "",
            "readme_excerpt": "",
            "score": "240",
            "stars": "0",
            "forks": "0",
            "pushes": "4",
        }

        categorized = categorize_row(row)

        self.assertEqual(categorized["category"], "personal_content_noise")
        self.assertGreaterEqual(float(categorized["noise_score"]), 5)

    def test_categorized_rows_keep_original_fields(self) -> None:
        rows = categorize_rows(
            [
                {
                    "rank": "1",
                    "repo_name": "secure/vault-scanner",
                    "description": "Security scanner for vault secrets",
                    "topics": "security;scanner;vault",
                    "primary_language": "Go",
                    "score": "5",
                }
            ]
        )

        self.assertEqual(rows[0]["rank"], "1")
        self.assertEqual(rows[0]["category"], "security_privacy")

    def test_split_repo_name(self) -> None:
        self.assertEqual(split_repo_name("owner/repo"), ("owner", "repo"))
        with self.assertRaises(ValueError):
            split_repo_name("not-a-full-name")


if __name__ == "__main__":
    unittest.main()
