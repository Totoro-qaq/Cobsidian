from __future__ import annotations

import unittest

from skills.cobsidian.scripts.duplicates import find_title_duplicates
from skills.cobsidian.scripts.scan_vault import NoteInfo


class DuplicateTests(unittest.TestCase):
    def test_duplicate_search_reports_truncation(self) -> None:
        notes = [
            NoteInfo("one.md", "Agent Workflow", [], [], 1),
            NoteInfo("two.md", "Agent Workflows", [], [], 1),
            NoteInfo("three.md", "Agent Work", [], [], 1),
        ]

        report = find_title_duplicates(notes, threshold=0.5, max_comparisons=1)

        self.assertEqual(1, report.comparisons)
        self.assertTrue(report.truncated)

    def test_exact_duplicates_are_complete_when_similar_search_is_capped(self) -> None:
        notes = [
            NoteInfo("one.md", "RAG", [], [], 1),
            NoteInfo("two.md", "rag", [], [], 1),
            NoteInfo("three.md", "Vector Search", [], [], 1),
        ]

        report = find_title_duplicates(notes, threshold=0.8, max_comparisons=0)

        self.assertEqual(
            [["one.md", "two.md"]],
            [[note.path for note in group] for group in report.exact_duplicates],
        )
        self.assertTrue(report.truncated)

    def test_negative_comparison_cap_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "max_comparisons"):
            find_title_duplicates([], threshold=0.8, max_comparisons=-1)


if __name__ == "__main__":
    unittest.main()
