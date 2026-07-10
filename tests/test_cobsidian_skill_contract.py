from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO_ROOT / "skills" / "cobsidian" / "SKILL.md"


class CobsidianSkillContractTests(unittest.TestCase):
    def test_skill_documents_vault_resolution_sources(self) -> None:
        text = SKILL_PATH.read_text(encoding="utf-8")

        required_fragments = [
            "## Vault Resolution",
            "cobsidian.config.yml",
            "COBSIDIAN_CONFIG",
            "COBSIDIAN_VAULT",
            "Do not guess a private vault path",
        ]

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

    def test_skill_documents_contextual_bilingual_mode_routing(self) -> None:
        text = SKILL_PATH.read_text(encoding="utf-8")

        required_fragments = [
            "## Response Language",
            "Chinese request -> Chinese mode names",
            "English request -> English mode names",
            "recommend at most two modes",
            "`learning` / 学习",
            "`project` / 项目",
            "`review` / 复盘",
            "`comparison` / 对比",
            "`index` / 索引",
            "`capture` / 捕获",
            "`dissection` / 拆解",
        ]

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

        forbidden_menus = [
            "English mode picker",
            "中文模式选择",
            "Cobsidian can organize this in several modes:",
            "Cobsidian 可以按这些模式整理：",
        ]
        for menu in forbidden_menus:
            with self.subTest(menu=menu):
                self.assertNotIn(menu, text)


if __name__ == "__main__":
    unittest.main()
