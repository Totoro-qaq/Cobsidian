from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from skills.cobsidian.scripts import retrieval
from skills.cobsidian.scripts.retrieval import (
    MAX_BACKLINK_LIMIT,
    SearchDocument,
    build_search_documents,
    rank_backlinks,
    tokenize,
)
from skills.cobsidian.scripts.scan_vault import NoteInfo


class RetrievalTests(unittest.TestCase):
    def test_chinese_related_phrases_share_tokens(self) -> None:
        long_text = tokenize("向量数据库使用嵌入模型进行语义检索")
        phrase = tokenize("嵌入模型")

        self.assertTrue(set(long_text) & set(phrase))

    def test_rank_backlinks_uses_body_and_stable_tie_breaking(self) -> None:
        documents = [
            SearchDocument(
                title="Vector Search",
                path="Vector Search.md",
                text="semantic retrieval through embeddings",
            ),
            SearchDocument(
                title="Agent Workflows",
                path="Agent Workflows.md",
                text="agents inspect context and validate",
            ),
        ]

        ranked = rank_backlinks("semantic retrieval embeddings", documents, limit=5)

        self.assertEqual(["Vector Search.md"], [item.path for item in ranked])

    def test_rank_backlinks_orders_equal_scores_by_path(self) -> None:
        documents = [
            SearchDocument("Second", "z-note.md", "shared"),
            SearchDocument("First", "a-note.md", "shared"),
        ]

        ranked = rank_backlinks("shared", documents, limit=5)

        self.assertEqual(["a-note.md", "z-note.md"], [item.path for item in ranked])

    def test_prose_punctuation_does_not_change_tokens(self) -> None:
        self.assertEqual(tokenize("SQLite"), tokenize("SQLite."))
        self.assertNotIn("##", tokenize("## Markdown heading"))

    def test_common_technical_tokens_are_preserved(self) -> None:
        tokens = tokenize("C++ C# node.js .venv pg-vector Qwen2.5")

        for expected in ("c++", "c#", "node.js", ".venv", "pg-vector", "qwen2.5"):
            with self.subTest(expected=expected):
                self.assertIn(expected, tokens)

    def test_embedded_punctuation_does_not_create_hidden_file_tokens(self) -> None:
        self.assertEqual(tokenize("foo bar"), tokenize("foo...bar"))
        self.assertNotIn(".bar", tokenize("foo...bar"))

    def test_versioned_cpp_token_is_preserved(self) -> None:
        self.assertIn("c++17", tokenize("C++17"))

    def test_backlink_limit_must_be_bounded(self) -> None:
        for invalid_limit in (-1, 0, MAX_BACKLINK_LIMIT + 1):
            with self.subTest(invalid_limit=invalid_limit):
                with self.assertRaisesRegex(ValueError, "limit"):
                    rank_backlinks("query", [], limit=invalid_limit)

    def test_search_documents_read_bodies_lazily(self) -> None:
        notes = [
            NoteInfo("one.md", "One", [], [], 1),
            NoteInfo("two.md", "Two", [], [], 1),
        ]

        with patch.object(
            retrieval,
            "read_utf8",
            side_effect=["first body", "second body"],
        ) as read_utf8:
            documents = build_search_documents(Path("vault"), notes)
            self.assertEqual(0, read_utf8.call_count)

            iterator = iter(documents)
            self.assertEqual("one.md", next(iterator).path)
            self.assertEqual(1, read_utf8.call_count)


if __name__ == "__main__":
    unittest.main()
