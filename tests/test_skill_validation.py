from __future__ import annotations

import unittest
from pathlib import Path

from skills.cobsidian.scripts.validate_skill import validate_skill


REPO_ROOT = Path(__file__).resolve().parents[1]


class SkillValidationTests(unittest.TestCase):
    def test_cobsidian_skill_has_valid_frontmatter(self) -> None:
        result = validate_skill(REPO_ROOT / "skills" / "cobsidian")

        self.assertEqual([], result.errors)

    def test_description_is_trigger_focused(self) -> None:
        result = validate_skill(REPO_ROOT / "skills" / "cobsidian")

        self.assertTrue(result.description.startswith("Use when"))
        self.assertLessEqual(len(result.description), 500)


if __name__ == "__main__":
    unittest.main()
