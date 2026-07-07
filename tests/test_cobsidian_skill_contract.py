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

    def test_skill_documents_language_aware_mode_picker(self) -> None:
        text = SKILL_PATH.read_text(encoding="utf-8")

        required_fragments = [
            "## Response Language",
            "Chinese request -> Chinese mode names",
            "English request -> English mode names",
            "中文模式选择",
            "English mode picker",
        ]

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
