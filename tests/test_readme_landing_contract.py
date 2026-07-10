from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
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
SUPPORTED_MODES = {
    "learning",
    "project",
    "review",
    "comparison",
    "index",
    "capture",
    "dissection",
}
SUPPORTED_DEPTHS = {"capture", "standard", "deep"}
SUPPORTED_GRANULARITIES = {"append", "single-note", "multi-note"}
SUPPORTED_EVIDENCE = {"conversation", "source-grounded", "verified"}
SUPPORTED_DISPLAY_POLICIES = {"auto", "always", "off"}
SUPPORTED_DISPLAY_STYLES = {"compact", "expanded", "hidden"}


def extract_json_example(readme: str, heading: str) -> dict[str, object]:
    pattern = rf"{re.escape(heading)}.*?```json\s+(.*?)\s+```"
    match = re.search(pattern, readme, flags=re.DOTALL)
    if match is None:
        raise AssertionError(f"Missing JSON example after {heading!r}.")
    payload = json.loads(match.group(1))
    if not isinstance(payload, dict):
        raise AssertionError(f"Example after {heading!r} must be a JSON object.")
    return payload


class ReadmeLandingContractTests(unittest.TestCase):
    def assert_valid_knowledge_read(
        self,
        payload: dict[str, object],
        expected_style: str,
    ) -> None:
        self.assertEqual(KNOWLEDGE_READ_FIELDS, set(payload))
        self.assertIn(payload["mode"], SUPPORTED_MODES | {None})
        self.assertIsInstance(payload["mode_explicit"], bool)
        self.assertIsInstance(payload["recommended_modes"], list)
        self.assertLessEqual(len(payload["recommended_modes"]), 2)
        self.assertTrue(set(payload["recommended_modes"]) <= SUPPORTED_MODES)
        self.assertIn(payload["depth"], SUPPORTED_DEPTHS)
        self.assertIn(payload["granularity"], SUPPORTED_GRANULARITIES)
        self.assertIn(payload["evidence"], SUPPORTED_EVIDENCE)
        self.assertIn(payload["display_policy"], SUPPORTED_DISPLAY_POLICIES)
        self.assertIn(payload["display_style"], SUPPORTED_DISPLAY_STYLES)
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

    def test_readmes_present_the_v05_adaptive_surface_concisely(self) -> None:
        english_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        chinese_readme = (REPO_ROOT / "docs" / "README.zh-CN.md").read_text(
            encoding="utf-8"
        )

        shared_fragments = [
            "Knowledge Read",
            "整理判读",
            "auto | always | off",
            "capability-based degradation",
            "v0.5.0",
        ]
        for readme in (english_readme, chinese_readme):
            for fragment in shared_fragments:
                with self.subTest(fragment=fragment):
                    self.assertIn(fragment, readme)
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

    def test_banner_svg_is_parseable_and_self_contained(self) -> None:
        banner_path = REPO_ROOT / "docs" / "assets" / "cobsidian-banner.svg"
        banner = banner_path.read_text(encoding="utf-8")

        ET.fromstring(banner)

        required_fragments = [
            'width="1200" height="360" viewBox="0 0 1200 360"',
            "<title>Cobsidian banner</title>",
            "Turn AI conversations into linked Obsidian knowledge, safely.",
            "neutral-surface",
            "linked-note-mark",
            "glass-panel",
            "linearGradient",
            "feGaussianBlur",
        ]

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, banner)

        self.assertNotIn('href="http://', banner)
        self.assertNotIn('href="https://', banner)
        self.assertNotIn('xlink:href="http', banner)
        self.assertNotIn("obsidian-icon", banner.lower())
        self.assertNotIn("obsidian-crystal", banner.lower())

    def test_banner_labels_use_centered_layout(self) -> None:
        banner_path = REPO_ROOT / "docs" / "assets" / "cobsidian-banner.svg"
        banner = banner_path.read_text(encoding="utf-8")

        required_fragments = [
            '<text x="77" y="-9" class="micro" text-anchor="middle" dominant-baseline="middle">LOCAL FIRST</text>',
            '<text x="66" y="19" class="chip-text" text-anchor="middle" dominant-baseline="middle">dry-run first</text>',
            '<text x="212" y="19" class="chip-text" text-anchor="middle" dominant-baseline="middle">wiki links</text>',
            '<text x="354" y="19" class="chip-text" text-anchor="middle" dominant-baseline="middle">MCP ready</text>',
            '<text x="143" y="126" class="micro" text-anchor="middle">7 modes · auto-link · dry-run</text>',
            '<path d="M770 316 C850 302 930 306 990 322 S1080 334 1140 310" class="circuit-line"/>',
        ]

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, banner)


if __name__ == "__main__":
    unittest.main()
