from __future__ import annotations

import asyncio
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skills.cobsidian.mcp_server import (
    build_dry_run_payload,
    create_mcp_server,
    ensure_relative_path_inside_vault,
    resolve_vault_from_inputs,
    scan_vault,
    tool_cobsidian_dry_run,
    tool_cobsidian_find_duplicates,
    tool_cobsidian_scan_vault,
    tool_cobsidian_suggest_backlinks,
)


def snapshot_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


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

            forbidden_write_terms = ("write", "mutate", "create", "update", "delete")
            self.assertEqual(
                [],
                sorted(
                    tool_name
                    for tool_name in tool_names
                    if any(term in tool_name.casefold() for term in forbidden_write_terms)
                ),
            )

            dry_run_tool = next(
                tool for tool in tools if tool.name == "cobsidian_dry_run"
            )
            dry_run_properties = dry_run_tool.inputSchema["properties"]
            self.assertTrue(
                {
                    "mode_explicit",
                    "recommended_modes",
                    "depth",
                    "granularity",
                    "evidence",
                    "knowledge_read_policy",
                    "capability_level",
                }.issubset(dry_run_properties)
            )
            self.assertEqual(
                "mcp-readonly",
                dry_run_properties["capability_level"]["default"],
            )

        asyncio.run(run())

    def test_server_instructions_and_prompts_describe_read_only_readiness(self) -> None:
        async def run() -> None:
            server = create_mcp_server()
            instructions = server.instructions.casefold()
            for expected in (
                "read-only",
                "knowledge_read",
                "preflight",
                "writes=[]",
                "active host",
            ):
                with self.subTest(surface="instructions", expected=expected):
                    self.assertIn(expected, instructions)

            dry_run_result = await server.get_prompt(
                "cobsidian-dry-run",
                {"vault": "vault", "topic": "RAG", "material": "notes"},
            )
            dry_run_text = dry_run_result.messages[0].content.text.casefold()
            for expected in (
                "knowledge_read",
                "preflight",
                "read-only readiness",
                "writes=[]",
            ):
                with self.subTest(surface="dry-run prompt", expected=expected):
                    self.assertIn(expected, dry_run_text)

            organize_result = await server.get_prompt(
                "cobsidian-organize-after-confirmation",
                {"vault": "vault", "topic": "RAG", "material": "notes"},
            )
            organize_text = organize_result.messages[0].content.text.casefold()
            self.assertIn("active host", organize_text)
            self.assertIn("mcp server remains read-only", organize_text)

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
            before = snapshot_files(vault)

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
            self.assertEqual(before, snapshot_files(vault))

    def test_dry_run_defaults_to_mcp_readonly_after_completed_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)

            payload = tool_cobsidian_dry_run(
                vault=str(vault),
                topic="RAG",
                text="Retrieval augmented generation.",
                mode="learning",
            )

            self.assertTrue(payload["preflight"]["vault_resolved"])
            self.assertTrue(payload["preflight"]["existing_notes_scanned"])
            self.assertTrue(payload["preflight"]["duplicate_check_completed"])
            self.assertTrue(payload["preflight"]["backlink_check_completed"])
            self.assertEqual(
                "mcp-readonly",
                payload["preflight"]["capability_level"],
            )
            self.assertFalse(payload["preflight"]["ready"])
            self.assertEqual(
                ["write_capability_unavailable"],
                payload["preflight"]["blocked_reasons"],
            )
            self.assertEqual([], payload["writes"])

    def test_dry_run_optional_fields_match_shared_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            (vault / "Vector Search.md").write_text(
                "# Vector Search\n\nSemantic retrieval through embeddings.\n",
                encoding="utf-8",
            )
            before = snapshot_files(vault)
            vault_path, config = resolve_vault_from_inputs(vault=str(vault))
            optional_fields = {
                "mode_explicit": False,
                "depth": "deep",
                "granularity": "multi-note",
                "evidence": "verified",
                "knowledge_read_policy": "off",
                "capability_level": "filesystem-only",
            }

            expected = build_dry_run_payload(
                vault_path=vault_path,
                config=config,
                topic="Retrieval Pipeline",
                mode="learning",
                text="Semantic retrieval through embeddings.",
                notes=scan_vault(vault_path),
                **optional_fields,
            )
            actual = tool_cobsidian_dry_run(
                vault=str(vault),
                topic="Retrieval Pipeline",
                mode="learning",
                text="Semantic retrieval through embeddings.",
                **optional_fields,
            )

            self.assertEqual(expected, actual)
            self.assertTrue(actual["preflight"]["ready"])
            self.assertEqual([], actual["writes"])
            self.assertEqual(before, snapshot_files(vault))

    def test_dry_run_mode_explicitness_distinguishes_direct_and_config_modes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            vault = workspace / "vault"
            vault.mkdir()
            config = workspace / "cobsidian.config.yml"
            config.write_text(
                'vault:\n  path: "vault"\ndefaults:\n  mode: "learning"\n',
                encoding="utf-8",
            )

            cases = (
                ({"mode": "project"}, True),
                ({}, False),
                ({"mode": "project", "mode_explicit": False}, False),
                ({"mode_explicit": True}, True),
            )
            for arguments, expected in cases:
                with self.subTest(arguments=arguments):
                    payload = tool_cobsidian_dry_run(
                        config=str(config),
                        topic="RAG",
                        text="Retrieval augmented generation.",
                        **arguments,
                    )
                    self.assertEqual(
                        expected,
                        payload["knowledge_read"]["mode_explicit"],
                    )

    def test_dry_run_accepts_recommendations_only_for_unresolved_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload = tool_cobsidian_dry_run(
                vault=temp_dir,
                topic="Adaptive Notes",
                text="",
                recommended_modes=["learning", "dissection"],
            )

            self.assertEqual(
                ["learning", "dissection"],
                payload["knowledge_read"]["recommended_modes"],
            )
            self.assertIn("mode_unresolved", payload["preflight"]["blocked_reasons"])
            self.assertEqual([], payload["writes"])

    def test_dry_run_rejects_invalid_enums_and_recommendation_combinations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            vault = workspace / "vault"
            vault.mkdir()
            config = workspace / "cobsidian.config.yml"
            config.write_text(
                'vault:\n  path: "vault"\ndefaults:\n  mode: "learning"\n',
                encoding="utf-8",
            )
            invalid_cases = (
                {"mode": ""},
                {"mode": "unknown"},
                {"depth": "shallow"},
                {"granularity": "per-topic"},
                {"evidence": "assumed"},
                {"knowledge_read_policy": "sometimes"},
                {"capability_level": "writer"},
                {"mode": "learning", "recommended_modes": ["project"]},
                {"recommended_modes": ["learning", "project", "review"]},
            )

            for arguments in invalid_cases:
                with self.subTest(arguments=arguments):
                    with self.assertRaises(ValueError):
                        tool_cobsidian_dry_run(
                            config=str(config),
                            topic="RAG",
                            text="Retrieval augmented generation.",
                            **arguments,
                        )

    def test_chat_only_dry_run_does_not_scan_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("skills.cobsidian.mcp_server.scan_vault") as scan_mock:
                payload = tool_cobsidian_dry_run(
                    vault=temp_dir,
                    topic="RAG",
                    text="Retrieval augmented generation.",
                    mode="learning",
                    capability_level="chat-only",
                )

            scan_mock.assert_not_called()
            self.assertFalse(payload["preflight"]["existing_notes_scanned"])
            self.assertFalse(payload["preflight"]["duplicate_check_completed"])
            self.assertFalse(payload["preflight"]["backlink_check_completed"])
            self.assertEqual([], payload["writes"])

    def test_scan_capable_dry_run_scans_before_building_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            events: list[str] = []
            original_scan_vault = scan_vault
            original_build_payload = build_dry_run_payload

            def tracked_scan_vault(vault_path: Path) -> object:
                events.append("scan")
                return original_scan_vault(vault_path)

            def tracked_build_payload(**arguments: object) -> dict[str, object]:
                events.append("build")
                return original_build_payload(**arguments)

            with (
                patch(
                    "skills.cobsidian.mcp_server.scan_vault",
                    side_effect=tracked_scan_vault,
                ),
                patch(
                    "skills.cobsidian.mcp_server.build_dry_run_payload",
                    side_effect=tracked_build_payload,
                ),
            ):
                tool_cobsidian_dry_run(
                    vault=temp_dir,
                    topic="RAG",
                    text="Retrieval augmented generation.",
                    mode="learning",
                )

            self.assertEqual(["scan", "build"], events)

    def test_dry_run_preserves_legacy_five_argument_call(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload = tool_cobsidian_dry_run(
                "RAG",
                "Retrieval augmented generation.",
                temp_dir,
                None,
                "learning",
            )

            self.assertTrue(payload["dry_run"])
            self.assertEqual([], payload["writes"])

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
