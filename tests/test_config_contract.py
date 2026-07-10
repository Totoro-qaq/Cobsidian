from __future__ import annotations

import unittest
from pathlib import Path

from skills.cobsidian.scripts.cobsidian_config import (
    SUPPORTED_CONFIG_LEAF_PATHS,
    flatten_leaf_paths,
    parse_simple_yaml,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class ConfigContractTests(unittest.TestCase):
    def test_supported_paths_include_knowledge_read_policy(self) -> None:
        self.assertIn(
            "interaction.knowledge_read",
            SUPPORTED_CONFIG_LEAF_PATHS,
        )

    def test_example_contains_only_supported_keys(self) -> None:
        config_path = REPO_ROOT / "cobsidian.config.example.yml"
        parsed = parse_simple_yaml(config_path.read_text(encoding="utf-8"))

        self.assertEqual(SUPPORTED_CONFIG_LEAF_PATHS, flatten_leaf_paths(parsed))

    def test_example_declares_v05_knowledge_read_contract(self) -> None:
        config_path = REPO_ROOT / "cobsidian.config.example.yml"
        text = config_path.read_text(encoding="utf-8")
        parsed = parse_simple_yaml(text)

        self.assertTrue(
            text.startswith("# Cobsidian v0.5 supported config.\n"),
        )
        self.assertIn(
            "interaction:\n"
            "  # auto expands complex or inferred work; always expands; "
            "off only hides presentation.\n"
            "  knowledge_read: auto\n",
            text,
        )
        self.assertEqual(
            {"knowledge_read": "auto"},
            parsed.get("interaction"),
        )


if __name__ == "__main__":
    unittest.main()
