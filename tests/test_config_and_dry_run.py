from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "cobsidian" / "scripts"


class ConfigAndDryRunTests(unittest.TestCase):
    def test_scan_vault_uses_config_vault_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            vault_path = workspace / "vault"
            vault_path.mkdir()
            (vault_path / "RAG.md").write_text("# RAG\n\nRetrieval augmented generation.\n", encoding="utf-8")
            config_path = workspace / "cobsidian.config.yml"
            config_path.write_text(
                """
vault:
  path: "vault"
defaults:
  mode: "learning"
""".strip(),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "scan_vault.py"),
                    "--config",
                    str(config_path),
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            payload = json.loads(result.stdout)
            self.assertEqual(payload["vault"], str(vault_path.resolve()))
            self.assertEqual(payload["note_count"], 1)
            self.assertEqual(payload["config"]["defaults"]["mode"], "learning")

    def test_find_duplicates_uses_config_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            vault_path = workspace / "vault"
            vault_path.mkdir()
            (vault_path / "api-trade.md").write_text("# API Trade\n", encoding="utf-8")
            (vault_path / "api-trader.md").write_text("# API Trader\n", encoding="utf-8")
            config_path = workspace / "cobsidian.config.yml"
            config_path.write_text(
                """
vault:
  path: "vault"
duplicates:
  similar_title_threshold: 0.5
""".strip(),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "find_duplicates.py"),
                    "--config",
                    str(config_path),
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertIn("API Trade", result.stdout)
            self.assertIn("API Trader", result.stdout)

    def test_dry_run_json_reports_append_decision_and_backlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            vault_path = workspace / "vault"
            vault_path.mkdir()
            (vault_path / "RAG.md").write_text("# RAG\n\nRetrieval with [[Embedding Models]].\n", encoding="utf-8")
            (vault_path / "Embedding Models.md").write_text("# Embedding Models\n\nVector representations.\n", encoding="utf-8")
            config_path = workspace / "cobsidian.config.yml"
            config_path.write_text(
                """
vault:
  path: "vault"
defaults:
  mode: "learning"
linking:
  max_suggested_backlinks: 3
duplicates:
  similar_title_threshold: 0.8
validation:
  strict: true
""".strip(),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "dry_run.py"),
                    "--config",
                    str(config_path),
                    "--topic",
                    "RAG",
                    "--text",
                    "RAG uses embedding models and vector search.",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            payload = json.loads(result.stdout)
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["mode"], "learning")
            self.assertEqual(payload["decision"]["action"], "append")
            self.assertEqual(payload["decision"]["target_note"], "RAG.md")
            self.assertIn("Embedding Models", [item["title"] for item in payload["suggested_backlinks"]])
            self.assertEqual(payload["writes"], [])
            self.assertTrue(payload["validation"]["would_run"])


if __name__ == "__main__":
    unittest.main()
