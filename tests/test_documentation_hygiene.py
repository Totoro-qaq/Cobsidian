from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_PATTERNS = ("*.md", "*.yml", "*.yaml", "*.json")
FORBIDDEN_CURRENT_STATUS_PHRASES = ("Early MVP", "早期 MVP")
FORBIDDEN_LOCAL_PATHS = (
    "D:/python/Cobsidian",
    "D:\\python\\Cobsidian",
    "D:/path/to",
    "C:/Users/62683",
    "C:\\Users\\62683",
)
PUBLIC_USER_DOCS = (
    "README.md",
    "docs/README.zh-CN.md",
    "docs/modes.md",
    "docs/modes.zh-CN.md",
    "docs/agent-compatibility.md",
    "docs/agent-compatibility.zh-CN.md",
    "docs/integrations.md",
    "docs/integrations.zh-CN.md",
    "docs/mcp-server.md",
    "docs/mcp-server.zh-CN.md",
    "CHANGELOG.md",
)


def read_public_doc(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def iter_documentation_files() -> list[Path]:
    paths: list[Path] = []
    for pattern in DOCUMENTATION_PATTERNS:
        paths.extend(REPO_ROOT.rglob(pattern))
    return [
        path
        for path in sorted(set(paths))
        if ".git" not in path.parts and "__pycache__" not in path.parts
    ]


class DocumentationHygieneTests(unittest.TestCase):
    def test_current_docs_do_not_describe_project_as_early_mvp(self) -> None:
        violations: list[str] = []
        for path in iter_documentation_files():
            text = path.read_text(encoding="utf-8")
            for phrase in FORBIDDEN_CURRENT_STATUS_PHRASES:
                if phrase in text:
                    violations.append(f"{path.relative_to(REPO_ROOT)} contains {phrase!r}")

        self.assertEqual([], violations)

    def test_public_docs_do_not_include_local_machine_paths(self) -> None:
        violations: list[str] = []
        for path in iter_documentation_files():
            text = path.read_text(encoding="utf-8")
            for local_path in FORBIDDEN_LOCAL_PATHS:
                if local_path in text:
                    violations.append(f"{path.relative_to(REPO_ROOT)} contains {local_path!r}")

        self.assertEqual([], violations)

    def test_public_user_docs_do_not_include_user_profile_paths(self) -> None:
        profile_patterns = (
            re.compile(r"[A-Za-z]:[/\\]Users[/\\](?!<|your[-_])[^/\\\s]+"),
            re.compile(r"/(?:Users|home)/(?!<|your[-_])[^/\s]+"),
        )
        violations: list[str] = []

        for relative_path in PUBLIC_USER_DOCS:
            text = read_public_doc(relative_path)
            for pattern in profile_patterns:
                if match := pattern.search(text):
                    violations.append(f"{relative_path} contains {match.group(0)!r}")

        self.assertEqual([], violations)

    def test_modes_docs_explain_outcomes_and_contextual_routing(self) -> None:
        for relative_path in ("docs/modes.md", "docs/modes.zh-CN.md"):
            text = read_public_doc(relative_path)
            with self.subTest(path=relative_path):
                self.assertIn("natural-language routing", text)
                self.assertIn("at most two", text)
                self.assertIn("create | append | blocked", text)
                self.assertIn("mode-level note plan", text)
                self.assertIn("skills/cobsidian/references/modes/", text)

    def test_agent_docs_define_capability_detection_and_readiness(self) -> None:
        for relative_path in (
            "docs/agent-compatibility.md",
            "docs/agent-compatibility.zh-CN.md",
        ):
            text = read_public_doc(relative_path)
            with self.subTest(path=relative_path):
                for level in (
                    "full-local",
                    "filesystem-only",
                    "mcp-readonly",
                    "chat-only",
                ):
                    self.assertIn(level, text)
                self.assertIn("capability detection", text)
                self.assertIn("capability-based degradation", text)
                self.assertIn("ready", text)
                self.assertIn("write_capability_unavailable", text)
                self.assertIn("read-only", text)
                self.assertIn("transport-neutral effective read-only", text)
                self.assertIn("validation_available", text)
                self.assertIn("validation_capability_unavailable", text)
                self.assertIn("independently", text)

    def test_integration_docs_explain_adaptive_fallbacks(self) -> None:
        for relative_path in ("docs/integrations.md", "docs/integrations.zh-CN.md"):
            text = read_public_doc(relative_path)
            with self.subTest(path=relative_path):
                self.assertIn("capability detection", text)
                self.assertIn("capability-based degradation", text)
                self.assertIn("full-local", text)
                self.assertIn("filesystem-only", text)
                self.assertIn("mcp-readonly", text)
                self.assertIn("chat-only", text)
                self.assertIn("zero-write MCP", text)
                self.assertIn("transport-neutral effective read-only", text)
                self.assertIn("validation_available", text)
                self.assertIn("independently", text)

    def test_mcp_docs_lock_parity_and_fail_closed_boundaries(self) -> None:
        parity_parameters = (
            "mode",
            "mode_explicit",
            "recommended_modes",
            "depth",
            "granularity",
            "evidence",
            "source_read_completed",
            "verification_completed",
            "validation_available",
            "knowledge_read_policy",
            "capability_level",
        )
        for relative_path in ("docs/mcp-server.md", "docs/mcp-server.zh-CN.md"):
            text = read_public_doc(relative_path)
            with self.subTest(path=relative_path):
                self.assertIn("CLI/MCP parameter parity", text)
                for parameter in parity_parameters:
                    self.assertIn(f"`{parameter}`", text)
                self.assertIn("mcp-readonly", text)
                self.assertIn("writes", text)
                self.assertIn("[]", text)
                self.assertIn("fail closed", text)
                self.assertIn("mode_unresolved", text)
                self.assertIn("write_capability_unavailable", text)
                self.assertIn("validation_capability_unavailable", text)
                self.assertIn("transport-neutral effective read-only", text)
                self.assertIn("host-completed", text)
                self.assertIn("granularity=append", text)
                self.assertIn("independently", text)

    def test_modes_docs_define_evidence_provenance(self) -> None:
        for relative_path in ("docs/modes.md", "docs/modes.zh-CN.md"):
            text = read_public_doc(relative_path)
            with self.subTest(path=relative_path):
                self.assertIn("source_read_completed=true", text)
                self.assertIn("verification_completed=true", text)
                self.assertIn("host-completed", text)
                self.assertIn("granularity=append", text)

    def test_changelog_has_an_undated_v05_release_section(self) -> None:
        changelog = read_public_doc("CHANGELOG.md")
        self.assertRegex(changelog, r"(?m)^## Unreleased\s*$")
        self.assertRegex(changelog, r"(?m)^## v0\.5\.0\s*$")
        self.assertNotRegex(changelog, r"(?m)^## v0\.5\.0\s+-\s+\d{4}-\d{2}-\d{2}")

        v05_section = changelog.split("## v0.5.0", maxsplit=1)[1].split(
            "## v0.4.0", maxsplit=1
        )[0]
        for fragment in (
            "adaptive routing",
            "mode and host references",
            "Knowledge Read",
            "preflight",
            "interaction.knowledge_read",
            "CLI/MCP parity",
            "compatibility and safety fixes",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, v05_section)

    def test_public_adapter_has_no_owner_specific_workflow_rules(self) -> None:
        adapter = (
            REPO_ROOT / "skills" / "cobsidian" / "agents" / "claude.md"
        ).read_text(encoding="utf-8")

        self.assertNotIn("做后端就用superpowers", adapter)
        self.assertNotIn("做知识整理就用cobsidian skill", adapter)


if __name__ == "__main__":
    unittest.main()
