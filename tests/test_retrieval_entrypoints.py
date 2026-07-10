from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import re
import subprocess
import sys

from skills.cobsidian.mcp_server import tool_cobsidian_suggest_backlinks
from skills.cobsidian.scripts.cobsidian_config import CobsidianConfig
from skills.cobsidian.scripts.dry_run import build_payload
from skills.cobsidian.scripts.retrieval import (
    build_query,
    build_search_documents,
    rank_backlinks,
)
from skills.cobsidian.scripts.scan_vault import scan_vault


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "cobsidian" / "scripts"


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
            topic = "Retrieval Pipeline"
            notes = scan_vault(vault)

            dry_run = build_payload(
                vault_path=vault,
                config=CobsidianConfig(config_path=None, raw={}),
                topic=topic,
                mode="learning",
                text=query,
                notes=notes,
            )
            mcp = tool_cobsidian_suggest_backlinks(
                vault=str(vault),
                topic=topic,
                text=query,
            )
            shared = rank_backlinks(
                build_query(topic=topic, text=query),
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

    def test_topic_and_text_query_is_shared_by_all_entrypoints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            (vault / "A Gamma Details.md").write_text(
                "# A Gamma Details\n\nTopic-only signal.\n",
                encoding="utf-8",
            )
            (vault / "Z Beta.md").write_text(
                "# Z Beta\n\nMaterial-only signal.\n",
                encoding="utf-8",
            )
            topic = "Gamma"
            text = "Beta"
            notes = scan_vault(vault)

            dry_run = build_payload(
                vault_path=vault,
                config=CobsidianConfig(config_path=None, raw={}),
                topic=topic,
                mode="learning",
                text=text,
                notes=notes,
            )
            mcp = tool_cobsidian_suggest_backlinks(
                vault=str(vault),
                topic=topic,
                text=text,
            )
            cli = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "suggest_backlinks.py"),
                    str(vault),
                    "--topic",
                    topic,
                    "--text",
                    text,
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            shared = rank_backlinks(
                build_query(topic=topic, text=text),
                build_search_documents(vault, notes),
                limit=8,
            )

            expected_paths = [item.path for item in shared]
            cli_paths = re.findall(r"path=(.+)$", cli.stdout, flags=re.MULTILINE)
            self.assertEqual(
                expected_paths,
                [item["path"] for item in dry_run["suggested_backlinks"]],
            )
            self.assertEqual(
                expected_paths,
                [item["path"] for item in mcp["suggestions"]],
            )
            self.assertEqual(expected_paths, cli_paths)

    def test_cli_uses_topic_when_file_body_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            (vault / "Gamma.md").write_text(
                "# Gamma\n\nTopic signal.\n",
                encoding="utf-8",
            )
            empty_draft = vault / "Empty Draft.md"
            empty_draft.write_text("", encoding="utf-8")

            cli = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "suggest_backlinks.py"),
                    str(vault),
                    "--topic",
                    "Gamma",
                    "--file",
                    str(empty_draft),
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertIn("path=Gamma.md", cli.stdout)
            self.assertNotIn("No usable tokens", cli.stdout)


if __name__ == "__main__":
    unittest.main()
