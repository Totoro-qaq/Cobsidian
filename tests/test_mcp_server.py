from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

from skills.cobsidian.mcp_server import (
    create_mcp_server,
    ensure_relative_path_inside_vault,
    tool_cobsidian_dry_run,
    tool_cobsidian_scan_vault,
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


if __name__ == "__main__":
    unittest.main()
