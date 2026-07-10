from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skills.cobsidian.mcp_server import tool_cobsidian_suggest_backlinks
from skills.cobsidian.scripts.cobsidian_config import CobsidianConfig
from skills.cobsidian.scripts.dry_run import build_payload
from skills.cobsidian.scripts.retrieval import build_search_documents, rank_backlinks
from skills.cobsidian.scripts.scan_vault import scan_vault


class RetrievalEntrypointTests(unittest.TestCase):
    def test_dry_run_mcp_and_shared_ranker_return_same_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            (vault / "Vector Search.md").write_text(
                "# Vector Search\n\nSemantic retrieval through embeddings.\n",
                encoding="utf-8",
            )
            (vault / "Agent Workflows.md").write_text(
                "# Agent Workflows\n\nAgents validate retrieval workflows.\n",
                encoding="utf-8",
            )
            query = "semantic retrieval embeddings"
            notes = scan_vault(vault)

            dry_run = build_payload(
                vault_path=vault,
                config=CobsidianConfig(config_path=None, raw={}),
                topic="Retrieval Pipeline",
                mode="learning",
                text=query,
                notes=notes,
            )
            mcp = tool_cobsidian_suggest_backlinks(vault=str(vault), text=query)
            shared = rank_backlinks(
                query,
                build_search_documents(vault, notes),
                limit=8,
            )

            self.assertEqual(
                [item["path"] for item in dry_run["suggested_backlinks"]],
                [item["path"] for item in mcp["suggestions"]],
            )
            self.assertEqual(
                [item["path"] for item in mcp["suggestions"]],
                [item.path for item in shared],
            )


if __name__ == "__main__":
    unittest.main()
