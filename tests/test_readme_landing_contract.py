from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class ReadmeLandingContractTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
