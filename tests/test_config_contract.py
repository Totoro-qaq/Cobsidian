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
    def test_example_contains_only_supported_keys(self) -> None:
        config_path = REPO_ROOT / "cobsidian.config.example.yml"
        parsed = parse_simple_yaml(config_path.read_text(encoding="utf-8"))

        self.assertEqual(SUPPORTED_CONFIG_LEAF_PATHS, flatten_leaf_paths(parsed))


if __name__ == "__main__":
    unittest.main()
