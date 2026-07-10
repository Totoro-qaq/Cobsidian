from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from skills.cobsidian.scripts.cobsidian_config import CobsidianConfig


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "cobsidian" / "scripts"


class ConfigAndDryRunTests(unittest.TestCase):
    def knowledge_read_policy_for(self, value: object = ...) -> str:
        raw = (
            {}
            if value is ...
            else {"interaction": {"knowledge_read": value}}
        )
        config = CobsidianConfig(config_path=None, raw=raw)
        if not hasattr(type(config), "knowledge_read_policy"):
            self.fail("CobsidianConfig.knowledge_read_policy is missing.")
        return config.knowledge_read_policy

    def test_knowledge_read_policy_defaults_to_auto(self) -> None:
        self.assertEqual("auto", self.knowledge_read_policy_for())

    def test_knowledge_read_policy_accepts_all_supported_values(self) -> None:
        for policy in ("auto", "always", "off"):
            with self.subTest(policy=policy):
                self.assertEqual(
                    policy,
                    self.knowledge_read_policy_for(policy),
                )

    def test_knowledge_read_policy_normalizes_string_input(self) -> None:
        values = {
            "  AuTo  ": "auto",
            "\tALWAYS\n": "always",
            " Off ": "off",
        }
        for configured, expected in values.items():
            with self.subTest(configured=configured):
                self.assertEqual(
                    expected,
                    self.knowledge_read_policy_for(configured),
                )

    def test_knowledge_read_policy_rejects_invalid_strings(self) -> None:
        for policy in ("", "sometimes", "auto-ish"):
            with self.subTest(policy=policy):
                with self.assertRaisesRegex(
                    ValueError,
                    r"interaction\.knowledge_read",
                ):
                    self.knowledge_read_policy_for(policy)

    def test_knowledge_read_policy_rejects_non_string_values(self) -> None:
        invalid_values = (None, True, 1, ["auto"], {"value": "auto"})
        for value in invalid_values:
            with self.subTest(value=value):
                with self.assertRaisesRegex(
                    ValueError,
                    r"interaction\.knowledge_read",
                ):
                    self.knowledge_read_policy_for(value)

    def test_public_summary_defensively_copies_interaction(self) -> None:
        config = CobsidianConfig(
            config_path=None,
            raw={"interaction": {"knowledge_read": "off"}},
        )

        summary = config.public_summary()

        self.assertEqual(
            {"knowledge_read": "off"},
            summary.get("interaction"),
        )
        interaction = summary.get("interaction")
        self.assertIsInstance(interaction, dict)
        assert isinstance(interaction, dict)
        interaction["knowledge_read"] = "always"
        self.assertEqual(
            "off",
            config.raw["interaction"]["knowledge_read"],
        )

    def test_public_summary_uses_empty_dict_for_invalid_interaction(self) -> None:
        config = CobsidianConfig(
            config_path=None,
            raw={"interaction": "off"},
        )

        self.assertEqual({}, config.public_summary().get("interaction"))

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

    def test_dry_run_uses_note_body_for_backlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault_path = Path(temp_dir)
            (vault_path / "Vector Search.md").write_text(
                "# Vector Search\n\nSemantic retrieval through embeddings.\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "dry_run.py"),
                    str(vault_path),
                    "--topic",
                    "Retrieval Pipeline",
                    "--text",
                    "semantic retrieval through embeddings",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            payload = json.loads(result.stdout)
            self.assertEqual(
                "Vector Search.md",
                payload["suggested_backlinks"][0]["path"],
            )


if __name__ == "__main__":
    unittest.main()
