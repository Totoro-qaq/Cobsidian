from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class DemoAssetContractTests(unittest.TestCase):
    def test_demo_html_is_self_contained_and_recorder_ready(self) -> None:
        demo_path = REPO_ROOT / "docs" / "assets" / "cobsidian-demo.html"
        demo = demo_path.read_text(encoding="utf-8")

        required_fragments = [
            "<title>Cobsidian</title>",
            'id="terminal-panel"',
            'id="note-panel"',
            'id="graph-panel"',
            'id="link-panel"',
            'class="linked-note-mark"',
            "--accent-violet:",
            "--neutral-surface:",
            'pathLength="1"',
            "Apply reviewed patch",
            "Saved · Validated",
            "[[Agent Workflows]]",
            "prefers-reduced-motion: reduce",
        ]

        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, demo)

        forbidden_fragments = [
            "http://",
            "https://",
            "C:\\Users\\62683",
            "D:\\python",
            "E:\\",
            "obsidian-icon",
            "obsidian-logo",
            "crystal-mark",
            '"plan_id"',
            "confirmation code",
        ]

        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, demo)


if __name__ == "__main__":
    unittest.main()
