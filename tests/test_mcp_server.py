from __future__ import annotations

import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skills.cobsidian.mcp_server import (
    create_mcp_server,
    ensure_relative_path_inside_vault,
    tool_cobsidian_dry_run,
    tool_cobsidian_find_duplicates,
    tool_cobsidian_scan_vault,
    tool_cobsidian_suggest_backlinks,
)


class McpServerTests(unittest.TestCase):
    def test_server_registers_core_tools_and_prompts(self) -> None:
        async def run() -> None:
            server = create_mcp_server()
            tools = await server.list_tools()
            prompts = await server.list_prompts()

            tool_names = {tool.name for tool in tools}
            prompt_names = {prompt.name for prompt in prompts}

            self.assertIn("cobsidian_scan_vault", tool_names)
            self.assertIn("cobsidian_find_duplicates", tool_names)
            self.assertIn("cobsidian_suggest_backlinks", tool_names)
            self.assertIn("cobsidian_validate_notes", tool_names)
            self.assertIn("cobsidian_dry_run", tool_names)
            self.assertIn("cobsidian-dry-run", prompt_names)
            self.assertIn("cobsidian-organize-after-confirmation", prompt_names)

        asyncio.run(run())

    def test_scan_tool_reads_config_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            vault = workspace / "vault"
            vault.mkdir()
            (vault / "Agent Workflows.md").write_text("# Agent Workflows\n", encoding="utf-8")
            config = workspace / "cobsidian.config.yml"
            config.write_text('vault:\n  path: "vault"\n', encoding="utf-8")

            payload = tool_cobsidian_scan_vault(config=str(config))

            self.assertEqual(payload["vault"], str(vault.resolve()))
            self.assertEqual(payload["note_count"], 1)
            self.assertEqual(payload["notes"][0]["title"], "Agent Workflows")

    def test_dry_run_tool_does_not_write_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            vault = workspace / "vault"
            vault.mkdir()
            note = vault / "AI Conversations.md"
            note.write_text("# AI Conversations\n\nRelated to [[Agent Workflows]].\n", encoding="utf-8")
            (vault / "Agent Workflows.md").write_text("# Agent Workflows\n\nAI workflow notes.\n", encoding="utf-8")

            payload = tool_cobsidian_dry_run(
                vault=str(vault),
                topic="AI Conversations",
                text="AI conversations should become linked agent workflow notes.",
                mode="learning",
            )

            self.assertEqual(payload["decision"]["action"], "append")
            self.assertEqual(payload["decision"]["target_note"], "AI Conversations.md")
            self.assertEqual(payload["writes"], [])
            self.assertEqual(note.read_text(encoding="utf-8"), "# AI Conversations\n\nRelated to [[Agent Workflows]].\n")

    def test_note_resource_path_must_stay_inside_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir) / "vault"
            vault.mkdir()

            allowed = ensure_relative_path_inside_vault(vault, "safe.md")
            self.assertEqual(allowed, (vault / "safe.md").resolve())

            with self.assertRaises(ValueError):
                ensure_relative_path_inside_vault(vault, "../outside.md")

    def test_scan_tool_paginates_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            for index in range(4):
                (vault / f"Note {index}.md").write_text(
                    f"# Note {index}\n",
                    encoding="utf-8",
                )

            payload = tool_cobsidian_scan_vault(
                vault=str(vault),
                offset=1,
                limit=2,
            )

            self.assertEqual(4, payload["total_note_count"])
            self.assertEqual(
                {"offset": 1, "limit": 2, "returned": 2},
                payload["page"],
            )
            self.assertEqual(2, len(payload["notes"]))

    def test_scan_tool_rejects_invalid_page_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            invalid_values = [
                {"offset": -1, "limit": 1},
                {"offset": 0, "limit": 0},
                {"offset": 0, "limit": 501},
            ]

            for values in invalid_values:
                with self.subTest(values=values):
                    with self.assertRaises(ValueError):
                        tool_cobsidian_scan_vault(vault=str(vault), **values)

    def test_duplicate_tool_reports_comparison_truncation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            for title in ("Agent Workflow", "Agent Workflows", "Agent Work"):
                (vault / f"{title}.md").write_text(f"# {title}\n", encoding="utf-8")

            payload = tool_cobsidian_find_duplicates(
                vault=str(vault),
                threshold=0.5,
                max_comparisons=1,
            )

            self.assertEqual(1, payload["comparisons"])
            self.assertTrue(payload["truncated"])

    def test_static_vault_summary_preserves_complete_resource_contract(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp_dir:
                vault = Path(temp_dir)
                for index in range(101):
                    (vault / f"Note {index:03d}.md").write_text(
                        f"# Note {index:03d}\n",
                        encoding="utf-8",
                    )
                with patch.dict(os.environ, {"COBSIDIAN_VAULT": str(vault)}):
                    contents = await create_mcp_server().read_resource(
                        "cobsidian://vault-summary"
                    )

                payload = json.loads(contents[0].content)
                self.assertEqual(101, payload["total_note_count"])
                self.assertEqual(101, len(payload["notes"]))

        asyncio.run(run())

    def test_vault_page_resource_supports_bounded_followup_pages(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as temp_dir:
                vault = Path(temp_dir)
                for index in range(101):
                    (vault / f"Note {index:03d}.md").write_text(
                        f"# Note {index:03d}\n",
                        encoding="utf-8",
                    )
                with patch.dict(os.environ, {"COBSIDIAN_VAULT": str(vault)}):
                    contents = await create_mcp_server().read_resource(
                        "cobsidian://vault-page/100/10"
                    )

                payload = json.loads(contents[0].content)
                self.assertEqual(
                    {"offset": 100, "limit": 10, "returned": 1},
                    payload["page"],
                )
                self.assertEqual("Note 100.md", payload["notes"][0]["path"])

        asyncio.run(run())

    def test_backlink_tool_rejects_invalid_limits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            (vault / "RAG.md").write_text("# RAG\n", encoding="utf-8")

            for invalid_limit in (-1, 0, 101):
                with self.subTest(invalid_limit=invalid_limit):
                    with self.assertRaisesRegex(ValueError, "limit"):
                        tool_cobsidian_suggest_backlinks(
                            vault=str(vault),
                            text="RAG",
                            limit=invalid_limit,
                        )

    def test_backlink_tool_requires_at_least_one_query_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError, "non-empty query"):
                tool_cobsidian_suggest_backlinks(vault=temp_dir)


if __name__ == "__main__":
    unittest.main()
