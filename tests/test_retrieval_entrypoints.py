from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
import re
import subprocess
import sys
from unittest.mock import patch

from skills.cobsidian.mcp_server import tool_cobsidian_suggest_backlinks
from skills.cobsidian.scripts import dry_run as dry_run_module
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
    def test_six_argument_build_payload_call_remains_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            config = CobsidianConfig(config_path=None, raw={})

            payload = build_payload(
                vault,
                config,
                "Retrieval Pipeline",
                "learning",
                "semantic retrieval",
                scan_vault(vault),
            )

            self.assertTrue(
                {
                    "dry_run",
                    "vault",
                    "config",
                    "mode",
                    "topic",
                    "decision",
                    "duplicate_risks",
                    "suggested_backlinks",
                    "validation",
                    "writes",
                }.issubset(payload)
            )
            self.assertIn("knowledge_read", payload)
            self.assertIn("preflight", payload)
            self.assertEqual([], payload["writes"])

    def test_explicit_learning_builds_compact_ready_local_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)

            payload = build_payload(
                vault_path=vault,
                config=CobsidianConfig(config_path=None, raw={}),
                topic="Retrieval Pipeline",
                mode="learning",
                text="semantic retrieval",
                notes=scan_vault(vault),
                mode_explicit=True,
            )

            self.assertEqual(
                {
                    "mode": "learning",
                    "mode_explicit": True,
                    "recommended_modes": [],
                    "depth": "standard",
                    "granularity": "single-note",
                    "evidence": "conversation",
                    "display_policy": "auto",
                    "display_style": "compact",
                },
                payload["knowledge_read"],
            )
            self.assertEqual("filesystem-only", payload["preflight"]["capability_level"])
            self.assertTrue(payload["preflight"]["ready"])
            self.assertEqual([], payload["preflight"]["blocked_reasons"])
            self.assertEqual([], payload["writes"])

    def test_append_decision_forces_append_granularity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            (vault / "RAG.md").write_text("# RAG\n", encoding="utf-8")

            payload = build_payload(
                vault_path=vault,
                config=CobsidianConfig(config_path=None, raw={}),
                topic="RAG",
                mode="learning",
                text="retrieval augmented generation",
                notes=scan_vault(vault),
                mode_explicit=True,
                granularity="multi-note",
            )

            self.assertEqual("append", payload["decision"]["action"])
            self.assertEqual("append", payload["knowledge_read"]["granularity"])

    def test_unresolved_mode_recommends_two_modes_and_blocks_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)

            payload = build_payload(
                vault_path=vault,
                config=CobsidianConfig(config_path=None, raw={}),
                topic="Adaptive Notes",
                mode=None,
                text="organize this material",
                notes=scan_vault(vault),
                recommended_modes=["learning", "dissection"],
            )

            self.assertIsNone(payload["knowledge_read"]["mode"])
            self.assertEqual(
                ["learning", "dissection"],
                payload["knowledge_read"]["recommended_modes"],
            )
            self.assertEqual("expanded", payload["knowledge_read"]["display_style"])
            self.assertFalse(payload["preflight"]["mode_selected"])
            self.assertFalse(payload["preflight"]["ready"])
            self.assertEqual(["mode_unresolved"], payload["preflight"]["blocked_reasons"])
            self.assertEqual([], payload["writes"])

    def test_mcp_readonly_reports_completed_scans_without_write_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)

            payload = build_payload(
                vault_path=vault,
                config=CobsidianConfig(config_path=None, raw={}),
                topic="Retrieval Pipeline",
                mode="learning",
                text="semantic retrieval",
                notes=scan_vault(vault),
                mode_explicit=True,
                capability_level="mcp-readonly",
            )

            self.assertTrue(payload["preflight"]["vault_resolved"])
            self.assertTrue(payload["preflight"]["existing_notes_scanned"])
            self.assertTrue(payload["preflight"]["duplicate_check_completed"])
            self.assertTrue(payload["preflight"]["backlink_check_completed"])
            self.assertFalse(payload["preflight"]["ready"])
            self.assertEqual(
                ["write_capability_unavailable"],
                payload["preflight"]["blocked_reasons"],
            )

    def test_chat_only_skips_scan_derived_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            (vault / "Portable Draft.md").write_text(
                "# Portable Draft\n\nRelated material.\n",
                encoding="utf-8",
            )

            with (
                patch.object(
                    dry_run_module,
                    "choose_decision",
                    wraps=dry_run_module.choose_decision,
                ) as choose_decision,
                patch.object(
                    dry_run_module,
                    "find_duplicate_risks",
                    wraps=dry_run_module.find_duplicate_risks,
                ) as find_duplicate_risks,
                patch.object(
                    dry_run_module,
                    "rank_backlinks",
                    wraps=dry_run_module.rank_backlinks,
                ) as rank_backlinks,
            ):
                payload = build_payload(
                    vault_path=vault,
                    config=CobsidianConfig(config_path=None, raw={}),
                    topic="Portable Draft",
                    mode="capture",
                    text="draft material",
                    notes=scan_vault(vault),
                    mode_explicit=True,
                    capability_level="chat-only",
                )

            preflight = payload["preflight"]
            self.assertEqual(
                {
                    "action": "blocked",
                    "target_note": "",
                    "reason": "Scan capability is unavailable.",
                },
                payload["decision"],
            )
            self.assertEqual([], payload["duplicate_risks"])
            self.assertEqual([], payload["suggested_backlinks"])
            self.assertFalse(preflight["ready"])
            self.assertIn("scan_capability_unavailable", preflight["blocked_reasons"])
            self.assertIn("write_capability_unavailable", preflight["blocked_reasons"])
            self.assertEqual([], payload["writes"])
            choose_decision.assert_not_called()
            find_duplicate_risks.assert_not_called()
            rank_backlinks.assert_not_called()

    def test_nonexistent_programmatic_vault_is_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "Portable Draft.md").write_text(
                "# Portable Draft\n\nRelated material.\n",
                encoding="utf-8",
            )
            missing_vault = workspace / "missing"

            with (
                patch.object(
                    dry_run_module,
                    "choose_decision",
                    return_value={
                        "action": "create",
                        "target_note": "Portable Draft.md",
                        "reason": "Unexpected scan-derived decision.",
                    },
                ) as choose_decision,
                patch.object(
                    dry_run_module,
                    "find_duplicate_risks",
                    return_value=[],
                ) as find_duplicate_risks,
                patch.object(
                    dry_run_module,
                    "rank_backlinks",
                    return_value=[],
                ) as rank_backlinks,
            ):
                payload = build_payload(
                    vault_path=missing_vault,
                    config=CobsidianConfig(config_path=None, raw={}),
                    topic="Portable Draft",
                    mode="capture",
                    text="draft material",
                    notes=scan_vault(workspace),
                    mode_explicit=True,
                )

            preflight = payload["preflight"]
            self.assertEqual(
                {
                    "action": "blocked",
                    "target_note": "",
                    "reason": "Vault path is unavailable.",
                },
                payload["decision"],
            )
            self.assertEqual([], payload["duplicate_risks"])
            self.assertEqual([], payload["suggested_backlinks"])
            self.assertFalse(preflight["vault_resolved"])
            self.assertFalse(preflight["existing_notes_scanned"])
            self.assertFalse(preflight["duplicate_check_completed"])
            self.assertFalse(preflight["backlink_check_completed"])
            self.assertFalse(preflight["ready"])
            for reason in (
                "vault_unresolved",
                "existing_notes_not_scanned",
                "duplicate_check_incomplete",
                "backlink_check_incomplete",
            ):
                with self.subTest(reason=reason):
                    self.assertIn(reason, preflight["blocked_reasons"])
            choose_decision.assert_not_called()
            find_duplicate_risks.assert_not_called()
            rank_backlinks.assert_not_called()

    def test_chat_only_existing_vault_has_no_scan_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)

            payload = build_payload(
                vault_path=vault,
                config=CobsidianConfig(config_path=None, raw={}),
                topic="Portable Draft",
                mode="capture",
                text="draft material",
                notes=[],
                mode_explicit=True,
                capability_level="chat-only",
            )

            preflight = payload["preflight"]
            self.assertTrue(preflight["vault_resolved"])
            self.assertFalse(preflight["existing_notes_scanned"])
            self.assertFalse(preflight["duplicate_check_completed"])
            self.assertFalse(preflight["backlink_check_completed"])
            self.assertFalse(preflight["ready"])
            self.assertNotIn("vault_unresolved", preflight["blocked_reasons"])

    def test_chat_only_cli_does_not_scan_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            output = io.StringIO()
            argv = [
                str(SCRIPTS_DIR / "dry_run.py"),
                str(vault),
                "--topic",
                "Portable Draft",
                "--mode",
                "capture",
                "--capability-level",
                "chat-only",
                "--json",
            ]

            with (
                patch.object(sys, "argv", argv),
                patch.object(dry_run_module, "scan_vault", return_value=[]) as scan,
                redirect_stdout(output),
            ):
                exit_code = dry_run_module.main()

            payload = json.loads(output.getvalue())
            self.assertEqual(0, exit_code)
            scan.assert_not_called()
            self.assertEqual("blocked", payload["decision"]["action"])
            self.assertEqual([], payload["duplicate_risks"])
            self.assertEqual([], payload["suggested_backlinks"])

    def test_invalid_capability_is_rejected_by_domain_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)

            with self.assertRaisesRegex(ValueError, "capability_level"):
                build_payload(
                    vault_path=vault,
                    config=CobsidianConfig(config_path=None, raw={}),
                    topic="Retrieval Pipeline",
                    mode="learning",
                    text="semantic retrieval",
                    notes=scan_vault(vault),
                    capability_level="browser-only",
                )

    def test_empty_programmatic_knowledge_read_policy_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)

            with self.assertRaisesRegex(ValueError, "display_policy"):
                build_payload(
                    vault_path=vault,
                    config=CobsidianConfig(config_path=None, raw={}),
                    topic="Retrieval Pipeline",
                    mode="learning",
                    text="semantic retrieval",
                    notes=scan_vault(vault),
                    knowledge_read_policy="",
                )

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

    def test_topic_only_query_is_shared_by_all_entrypoints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            (vault / "Gamma Concepts.md").write_text(
                "# Gamma Concepts\n\nTopic signal.\n",
                encoding="utf-8",
            )
            topic = "Gamma Workflow"

            backlink_cli = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "suggest_backlinks.py"),
                    str(vault),
                    "--topic",
                    topic,
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            dry_run_cli = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "dry_run.py"),
                    str(vault),
                    "--topic",
                    topic,
                    "--mode",
                    "learning",
                    "--json",
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            mcp = tool_cobsidian_suggest_backlinks(
                vault=str(vault),
                topic=topic,
            )

            cli_paths = re.findall(
                r"path=(.+)$",
                backlink_cli.stdout,
                flags=re.MULTILINE,
            )
            dry_run_paths = [
                item["path"]
                for item in json.loads(dry_run_cli.stdout)["suggested_backlinks"]
            ]
            mcp_paths = [item["path"] for item in mcp["suggestions"]]
            self.assertEqual(["Gamma Concepts.md"], cli_paths)
            self.assertEqual(cli_paths, dry_run_paths)
            self.assertEqual(cli_paths, mcp_paths)

    def test_blank_and_empty_file_queries_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            empty_draft = vault / "Empty Draft.md"
            empty_draft.write_text("", encoding="utf-8")

            backlink_cli = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "suggest_backlinks.py"),
                    str(vault),
                    "--topic",
                    "   ",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            empty_file_cli = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "suggest_backlinks.py"),
                    str(vault),
                    "--file",
                    str(empty_draft),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            dry_run_cli = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "dry_run.py"),
                    str(vault),
                    "--topic",
                    "   ",
                    "--json",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertNotEqual(0, backlink_cli.returncode)
            self.assertNotEqual(0, empty_file_cli.returncode)
            self.assertNotEqual(0, dry_run_cli.returncode)
            with self.assertRaisesRegex(ValueError, "non-empty query"):
                tool_cobsidian_suggest_backlinks(
                    vault=str(vault),
                    topic="   ",
                )
            with self.assertRaisesRegex(ValueError, "non-empty query"):
                tool_cobsidian_suggest_backlinks(
                    vault=str(vault),
                    note_path=empty_draft.name,
                )


if __name__ == "__main__":
    unittest.main()
