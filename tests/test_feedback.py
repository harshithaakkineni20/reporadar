from __future__ import annotations

import unittest

from reporadar.feedback import attach_feedback


class FeedbackTests(unittest.TestCase):
    def test_attach_feedback_adds_human_label_and_corrects_category(self) -> None:
        rows = [{"repo_name": "demo/repo", "category": "uncategorized"}]
        feedback = {
            "demo/repo": {
                "label": "keep",
                "corrected_category": "developer_tools",
                "reason": "Useful CLI.",
                "reviewed_at": "2026-05-12",
            }
        }

        updated = attach_feedback(rows, feedback)

        self.assertEqual(updated[0]["human_label"], "keep")
        self.assertEqual(updated[0]["category"], "developer_tools")
        self.assertEqual(updated[0]["human_reason"], "Useful CLI.")


if __name__ == "__main__":
    unittest.main()
