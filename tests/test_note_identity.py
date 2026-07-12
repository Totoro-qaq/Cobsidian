from __future__ import annotations

import tempfile
import unittest
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "cobsidian" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from skills.cobsidian.scripts.dry_run import find_duplicate_risks
from skills.cobsidian.scripts.note_identity import (
    build_note_identity,
    clean_markdown_title,
    parse_frontmatter_identity,
    strip_mode_prefix,
)
from skills.cobsidian.scripts.scan_vault import scan_vault


class NoteIdentityTests(unittest.TestCase):
    def test_markdown_h1_allows_standard_leading_spaces(self) -> None:
        identity = build_note_identity(Path("fallback.md"), "   # **Spaced H1**\n")
        self.assertEqual("Spaced H1", identity.heading_title)

    def test_cleans_wikilinks_links_and_emphasis_from_heading(self) -> None:
        self.assertEqual(
            "RAG 检索管线学习笔记",
            clean_markdown_title(
                "**[[学习-RAG检索管线|RAG]] "
                "[[学习-RAG检索管线|检索管线]]学习笔记**"
            ),
        )

    def test_reads_frontmatter_title_and_inline_or_block_aliases(self) -> None:
        inline_title, inline_aliases = parse_frontmatter_identity(
            "---\ntitle: Retrieval Augmented Generation\naliases: [RAG, 检索增强生成]\n---\n"
        )
        block_title, block_aliases = parse_frontmatter_identity(
            "---\ntitle: RAG\naliases:\n  - Retrieval Pipeline\n  - '检索增强'\n---\n"
        )

        self.assertEqual("Retrieval Augmented Generation", inline_title)
        self.assertEqual(("RAG", "检索增强生成"), inline_aliases)
        self.assertEqual("RAG", block_title)
        self.assertEqual(("Retrieval Pipeline", "检索增强"), block_aliases)

    def test_strips_only_known_mode_prefixes_with_separators(self) -> None:
        self.assertEqual("RAG检索管线", strip_mode_prefix("学习-RAG检索管线"))
        self.assertEqual("Agent Architecture", strip_mode_prefix("project: Agent Architecture"))
        self.assertEqual("Agent-Architecture", strip_mode_prefix("Agent-Architecture"))

    def test_identity_combines_filename_heading_frontmatter_aliases_and_core_titles(self) -> None:
        identity = build_note_identity(
            Path("学习-RAG检索管线.md"),
            "---\ntitle: Retrieval Knowledge\naliases: [RAG, 检索增强生成]\n---\n"
            "# **[[学习-RAG检索管线|RAG]] 检索管线**\n",
        )

        self.assertEqual("Retrieval Knowledge", identity.display_title)
        self.assertIn("学习-RAG检索管线", identity.candidate_titles)
        self.assertIn("RAG检索管线", identity.core_titles)
        self.assertIn("RAG", identity.aliases)

    def test_duplicate_matching_uses_filename_core_title_even_when_h1_differs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            (vault / "学习-RAG检索管线.md").write_text(
                "# [[学习-RAG检索管线|RAG]] 检索管线学习笔记\n",
                encoding="utf-8",
            )
            notes = scan_vault(vault)

            risks = find_duplicate_risks("RAG检索管线", notes, threshold=0.88)

            self.assertEqual(1, len(risks))
            self.assertEqual("exact", risks[0].kind)
            self.assertEqual("学习-RAG检索管线.md", risks[0].path)
            self.assertEqual("identity-exact", risks[0].match_basis)

    def test_scan_exposes_identity_fields_and_chinese_tags(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            (vault / "项目-Agent.md").write_text(
                "---\naliases: [智能体项目]\n---\n# **Agent Project**\n\n#项目/AI\n",
                encoding="utf-8",
            )

            note = scan_vault(vault)[0]

            self.assertEqual("Agent Project", note.title)
            self.assertEqual("项目-Agent", note.filename_title)
            self.assertIn("Agent", note.core_titles)
            self.assertIn("智能体项目", note.aliases)
            self.assertIn("项目/AI", note.tags)


if __name__ == "__main__":
    unittest.main()
