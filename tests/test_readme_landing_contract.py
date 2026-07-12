from __future__ import annotations

import hashlib
import json
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import unittest
from pathlib import Path

from skills.cobsidian.scripts.knowledge_read import (
    DEPTHS,
    DISPLAY_POLICIES,
    EVIDENCE_LEVELS,
    GRANULARITIES,
    MODES,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_VAULT = REPO_ROOT / "examples" / "demo-vault"
KNOWLEDGE_READ_FIELDS = {
    "mode",
    "mode_explicit",
    "recommended_modes",
    "depth",
    "granularity",
    "evidence",
    "display_policy",
    "display_style",
}


def extract_json_example(readme: str, heading: str) -> dict[str, object]:
    pattern = rf"{re.escape(heading)}.*?```json\s+(.*?)\s+```"
    match = re.search(pattern, readme, flags=re.DOTALL)
    if match is None:
        raise AssertionError(f"Missing JSON example after {heading!r}.")
    payload = json.loads(match.group(1))
    if not isinstance(payload, dict):
        raise AssertionError(f"Example after {heading!r} must be a JSON object.")
    return payload


def extract_quick_start_args(readme: str, heading: str) -> list[str]:
    pattern = rf"{re.escape(heading)}.*?```bash\s+(.*?)\s+```"
    match = re.search(pattern, readme, flags=re.DOTALL)
    if match is None:
        raise AssertionError(f"Missing bash block after {heading!r}.")
    commands = [line.strip() for line in match.group(1).splitlines()]
    python_commands = [line for line in commands if line.startswith("python ")]
    if len(python_commands) != 1:
        raise AssertionError(
            f"Expected one Python command after {heading!r}, got {python_commands!r}."
        )
    return shlex.split(python_commands[0])


def extract_mermaid_blocks(readme: str) -> list[str]:
    return re.findall(r"```mermaid\s+(.*?)\s+```", readme, flags=re.DOTALL)


def directory_digest(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(path for path in directory.rglob("*") if path.is_file()):
        digest.update(path.relative_to(directory).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


class ReadmeLandingContractTests(unittest.TestCase):
    def assert_valid_knowledge_read(
        self,
        payload: dict[str, object],
        expected_style: str,
    ) -> None:
        self.assertEqual(KNOWLEDGE_READ_FIELDS, set(payload))
        self.assertIn(payload["mode"], (*MODES, None))
        self.assertIsInstance(payload["mode_explicit"], bool)
        self.assertIsInstance(payload["recommended_modes"], list)
        self.assertLessEqual(len(payload["recommended_modes"]), 2)
        self.assertTrue(all(mode in MODES for mode in payload["recommended_modes"]))
        self.assertIn(payload["depth"], DEPTHS)
        self.assertIn(payload["granularity"], GRANULARITIES)
        self.assertIn(payload["evidence"], EVIDENCE_LEVELS)
        self.assertIn(payload["display_policy"], DISPLAY_POLICIES)
        self.assertEqual(expected_style, payload["display_style"])

    def test_english_readme_has_product_landing_sections(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        required_fragments = [
            "Turn AI conversations into linked Obsidian knowledge, safely.",
            "## Quick Start",
            "## Before / After",
            "## Dry-run Preview",
            "## Not Just Markdown Generation",
            "## Obsidian Vault Workflow",
            "```mermaid",
            "writes\": []",
        ]

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, readme)

    def test_chinese_readme_has_product_landing_sections(self) -> None:
        readme = (REPO_ROOT / "docs" / "README.zh-CN.md").read_text(encoding="utf-8")

        required_fragments = [
            "安全地把 AI 对话整理成带双链的 Obsidian 知识库。",
            "## 快速开始",
            "## 前后对比",
            "## Dry-run 预览",
            "## 不是普通 Markdown 生成器",
            "## Obsidian Vault 工作流",
            "```mermaid",
            "writes\": []",
        ]

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, readme)

    def test_readmes_reference_local_landing_assets(self) -> None:
        english_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        chinese_readme = (REPO_ROOT / "docs" / "README.zh-CN.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("docs/assets/cobsidian-banner.svg", english_readme)
        self.assertIn("docs/assets/cobsidian-demo.gif", english_readme)
        self.assertIn("assets/cobsidian-banner.svg", chinese_readme)
        self.assertIn("assets/cobsidian-demo.gif", chinese_readme)
        self.assertTrue((REPO_ROOT / "docs" / "assets" / "cobsidian-banner.svg").is_file())
        self.assertTrue((REPO_ROOT / "docs" / "assets" / "cobsidian-demo.gif").is_file())
        self.assertNotIn("readme-typing-svg", english_readme + chinese_readme)
        self.assertNotIn("capsule-render", english_readme + chinese_readme)

    def test_readmes_present_the_adaptive_and_transaction_surfaces_concisely(self) -> None:
        english_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        chinese_readme = (REPO_ROOT / "docs" / "README.zh-CN.md").read_text(
            encoding="utf-8"
        )

        shared_fragments = [
            "Knowledge Read",
            "整理判读",
            "auto | always | off",
            "capability-based degradation",
            "write_executor.py",
        ]
        for readme in (english_readme, chinese_readme):
            for fragment in shared_fragments:
                with self.subTest(fragment=fragment):
                    self.assertIn(fragment.casefold(), readme.casefold())
            self.assertIn("skills/cobsidian/references/", readme)
            self.assertNotIn("## Default Knowledge Read", readme)
            self.assertNotIn("## Append, Single-Note, and Split Criteria", readme)

        self.assertIn("complete JSON", english_readme)
        self.assertIn("完整 JSON", chinese_readme)
        self.assertIn("supported config surface", english_readme)
        self.assertIn("当前支持的配置面", chinese_readme)

    def test_readmes_include_valid_compact_and_expanded_knowledge_reads(self) -> None:
        readmes = {
            "english": (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            "chinese": (REPO_ROOT / "docs" / "README.zh-CN.md").read_text(
                encoding="utf-8"
            ),
        }

        for language, readme in readmes.items():
            with self.subTest(language=language, style="compact"):
                compact = extract_json_example(readme, "### Compact Knowledge Read")
                self.assert_valid_knowledge_read(compact, "compact")
            with self.subTest(language=language, style="expanded"):
                expanded = extract_json_example(readme, "### Expanded Knowledge Read")
                self.assert_valid_knowledge_read(expanded, "expanded")

    def test_readme_quick_starts_execute_as_ready_learning_dry_runs(self) -> None:
        readmes = {
            "english": (
                (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
                "## Quick Start",
            ),
            "chinese": (
                (REPO_ROOT / "docs" / "README.zh-CN.md").read_text(
                    encoding="utf-8"
                ),
                "## 快速开始",
            ),
        }

        for language, (readme, heading) in readmes.items():
            with self.subTest(language=language):
                args = extract_quick_start_args(readme, heading)
                self.assertEqual("python", args[0])
                self.assertEqual(
                    "skills/cobsidian/scripts/dry_run.py",
                    args[1],
                )

                with tempfile.TemporaryDirectory() as temp_dir:
                    vault = Path(temp_dir) / "demo-vault"
                    shutil.copytree(DEMO_VAULT, vault)
                    command_args = args[1:]
                    vault_index = command_args.index("examples/demo-vault")
                    command_args[vault_index] = str(vault)
                    before = directory_digest(vault)

                    result = subprocess.run(
                        [sys.executable, *command_args],
                        cwd=REPO_ROOT,
                        check=True,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                    )
                    payload = json.loads(result.stdout)

                    self.assertEqual(before, directory_digest(vault))
                    self.assertEqual("learning", payload["mode"])
                    self.assertEqual("learning", payload["knowledge_read"]["mode"])
                    self.assertIs(True, payload["knowledge_read"]["mode_explicit"])
                    self.assertEqual(
                        "compact",
                        payload["knowledge_read"]["display_style"],
                    )
                    self.assertIs(True, payload["preflight"]["ready"])
                    self.assertEqual([], payload["preflight"]["blocked_reasons"])
                    self.assertEqual([], payload["writes"])

    def test_readme_mermaid_diagrams_separate_action_from_note_plan(self) -> None:
        readmes = {
            "english": (REPO_ROOT / "README.md").read_text(encoding="utf-8"),
            "chinese": (REPO_ROOT / "docs" / "README.zh-CN.md").read_text(
                encoding="utf-8"
            ),
        }
        conflated_phrases = (
            "Create, append, or split?",
            "Plan: create, append, split, or ask",
            "新建、追加、拆分？",
            "规划：新建、追加、拆分或询问",
            "先判断新建、追加还是拆分",
        )

        for language, readme in readmes.items():
            blocks = extract_mermaid_blocks(readme)
            with self.subTest(language=language, check="diagram-count"):
                self.assertEqual(2, len(blocks))
            for index, block in enumerate(blocks):
                with self.subTest(language=language, diagram=index):
                    self.assertIn("create | append | blocked", block)
                    self.assertIn(
                        "single-note | multi-note | report-only",
                        block,
                    )
                    self.assertIn("split = multi-note", block)
            for phrase in conflated_phrases:
                with self.subTest(language=language, phrase=phrase):
                    self.assertNotIn(phrase, readme)

    def test_banner_svg_is_parseable_and_self_contained(self) -> None:
        banner_path = REPO_ROOT / "docs" / "assets" / "cobsidian-banner.svg"
        banner = banner_path.read_text(encoding="utf-8")

        ET.fromstring(banner)

        required_fragments = [
            'width="1200" height="360" viewBox="0 0 1200 360"',
            "<title>Cobsidian banner</title>",
            "A minimal light banner",
            "linked-note-mark",
            "Maintain a linked Obsidian vault with your coding agent.",
            "signature-edge",
        ]

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, banner)

        self.assertNotIn('href="http://', banner)
        self.assertNotIn('href="https://', banner)
        self.assertNotIn('xlink:href="http', banner)
        self.assertNotIn("obsidian-icon", banner.lower())
        self.assertNotIn("obsidian-crystal", banner.lower())

    def test_banner_keeps_a_single_brand_thesis(self) -> None:
        banner_path = REPO_ROOT / "docs" / "assets" / "cobsidian-banner.svg"
        banner = banner_path.read_text(encoding="utf-8")

        required_fragments = [
            'font-size="90">Cobsidian</text>',
            "One note growing into useful connections",
            'fill="#28a6bb"',
            'fill="#e8a43b"',
            'fill="#32b783"',
        ]

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, banner)

        forbidden_fragments = [
            "Cobsidian Demo Vault",
            "RAG Retrieval Pipeline",
            "GRAPH VIEW",
            "Saved · Validated",
            "[[Vector Search]]",
        ]
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, banner)


if __name__ == "__main__":
    unittest.main()
