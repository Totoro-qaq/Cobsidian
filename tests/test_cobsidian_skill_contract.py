from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO_ROOT / "skills" / "cobsidian" / "SKILL.md"


def h2_section(text: str, heading: str) -> str:
    start_marker = f"## {heading}\n"
    start = text.index(start_marker) + len(start_marker)
    remainder = text[start:]
    end = remainder.find("\n## ")
    return remainder if end == -1 else remainder[:end]


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

    def test_representative_bilingual_cues_share_the_canonical_mode_row(self) -> None:
        text = SKILL_PATH.read_text(encoding="utf-8")
        expected_cues = {
            "learning": ("teach me about", "这个概念讲一下"),
            "project": ("document this repo", "这个仓库帮我分析一下"),
            "review": ("what went wrong", "失败复盘"),
            "comparison": ("which should I choose", "哪个更好"),
            "index": ("learning path", "学习路线"),
            "capture": ("just save this", "先记下来"),
            "dissection": ("how does X work internally", "这个怎么实现的"),
        }

        for mode, cues in expected_cues.items():
            with self.subTest(mode=mode):
                matching_rows = [
                    line
                    for line in text.splitlines()
                    if line.startswith(f"| `{mode}` /")
                ]
                self.assertEqual(1, len(matching_rows))
                for cue in cues:
                    self.assertIn(cue, matching_rows[0])

    def test_machine_action_is_separate_from_the_mode_level_note_plan(self) -> None:
        text = SKILL_PATH.read_text(encoding="utf-8")
        workflow = h2_section(text, "Common Workflow")
        completion = h2_section(text, "Completion Report")

        for section in (workflow, completion):
            with self.subTest(section=section[:30]):
                self.assertIn("`decision.action`: `create | append | blocked`", section)
                self.assertIn(
                    "mode-level note plan: `single-note | multi-note | report-only`",
                    section,
                )
        self.assertIn("split means `multi-note`", workflow)
        self.assertIn("not a machine action", completion)
        self.assertNotIn("decide create, append, split, or report-only", workflow)
        self.assertNotIn(
            "create, append, split, or report-only decision",
            completion,
        )

    def test_write_rules_require_relative_paths_and_minimum_disclosure(self) -> None:
        text = SKILL_PATH.read_text(encoding="utf-8")
        write_rules = h2_section(text, "Write Rules")

        self.assertIn("Use vault-relative paths in note content", write_rules)
        self.assertIn(
            "Local operational records still use minimum necessary disclosure",
            write_rules,
        )
        for sensitive_data in ("credentials", "tokens", "private identifiers"):
            with self.subTest(sensitive_data=sensitive_data):
                self.assertIn(sensitive_data, write_rules)
        self.assertIn("redact", write_rules)
        self.assertNotIn(
            "unless explicitly requested for local operational records",
            write_rules,
        )


if __name__ == "__main__":
    unittest.main()
