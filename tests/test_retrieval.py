from __future__ import annotations

import unittest

from skills.cobsidian.scripts.retrieval import SearchDocument, rank_backlinks, tokenize


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


if __name__ == "__main__":
    unittest.main()
