from __future__ import annotations

import unittest

from reporadar.categorize import categorize_row, categorize_rows, keyword_matches, tokenize
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

    def test_description_and_topics_override_readme_boilerplate(self) -> None:
        row = {
            "repo_name": "openclaw/openclaw",
            "description": "Your own personal AI assistant for any OS",
            "topics": "ai;assistant;agent;llm",
            "primary_language": "TypeScript",
            "readme_excerpt": "Docker CI cloud deploy instructions for contributors",
            "license_key": "mit",
            "score": "100",
            "stargazers_count": "2500",
            "forks_count": "200",
        }

        categorized = categorize_row(row)

        self.assertEqual(categorized["category"], "ai_ml_data")
        self.assertIn("assistant", categorized["category_reason"])

    def test_deepseek_terminal_agent_is_ai_not_generic_library(self) -> None:
        row = {
            "repo_name": "Hmbown/DeepSeek-TUI",
            "description": "Coding agent for DeepSeek models that runs in terminal",
            "topics": "cli;deepseek;llm;rust;terminal;tui",
            "primary_language": "Rust",
            "readme_excerpt": "A terminal UI for model-powered coding workflows",
            "license_key": "mit",
            "score": "80",
            "stargazers_count": "1000",
            "forks_count": "50",
        }

        categorized = categorize_row(row)

        self.assertEqual(categorized["category"], "ai_ml_data")
        self.assertIn("deepseek", categorized["category_reason"])

    def test_smoke_delete_after_repo_gets_noise_category(self) -> None:
        row = {
            "repo_name": "mtplayground/mpg-smoke-01",
            "description": "Provisioning smoke test, delete after validation",
            "topics": "",
            "primary_language": "Python",
            "readme_excerpt": "",
            "score": "120",
            "stars": "0",
            "forks": "0",
            "pushes": "3",
        }

        categorized = categorize_row(row)

        self.assertEqual(categorized["category"], "personal_content_noise")
        self.assertGreaterEqual(float(categorized["noise_score"]), 6)

    def test_missing_github_metadata_gets_noise_category(self) -> None:
        row = {
            "repo_name": "xhjsh13-bot/xhjsh13",
            "metadata_error": "not_found",
            "description": "",
            "topics": "",
            "primary_language": "",
            "score": "90",
        }

        categorized = categorize_row(row)

        self.assertEqual(categorized["category"], "personal_content_noise")
        self.assertGreaterEqual(float(categorized["noise_score"]), 4.5)
        self.assertIn("metadata_error:not_found", categorized["category_reason"])

    def test_split_repo_name(self) -> None:
        self.assertEqual(split_repo_name("owner/repo"), ("owner", "repo"))
        with self.assertRaises(ValueError):
            split_repo_name("not-a-full-name")

    def test_short_keywords_do_not_match_inside_words(self) -> None:
        text = "available main starting application"
        tokens = tokenize(text)

        self.assertFalse(keyword_matches("ai", text, tokens))
        self.assertFalse(keyword_matches("ml", text, tokens))
        self.assertFalse(keyword_matches("ci", text, tokens))
        self.assertFalse(keyword_matches("api", text, tokens))
        self.assertFalse(keyword_matches("art", text, tokens))

    def test_short_keywords_match_as_tokens(self) -> None:
        text = "ai ml ci api art"
        tokens = tokenize(text)

        self.assertTrue(keyword_matches("ai", text, tokens))
        self.assertTrue(keyword_matches("ml", text, tokens))
        self.assertTrue(keyword_matches("ci", text, tokens))
        self.assertTrue(keyword_matches("api", text, tokens))
        self.assertTrue(keyword_matches("art", text, tokens))


if __name__ == "__main__":
    unittest.main()
