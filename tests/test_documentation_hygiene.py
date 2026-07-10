from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_PATTERNS = ("*.md", "*.yml", "*.yaml", "*.json")
FORBIDDEN_CURRENT_STATUS_PHRASES = ("Early MVP", "早期 MVP")
FORBIDDEN_LOCAL_PATHS = (
    "D:/python/Cobsidian",
    "D:\\python\\Cobsidian",
    "D:/path/to",
    "C:/Users/62683",
    "C:\\Users\\62683",
)


def iter_documentation_files() -> list[Path]:
    paths: list[Path] = []
    for pattern in DOCUMENTATION_PATTERNS:
        paths.extend(REPO_ROOT.rglob(pattern))
    return [
        path
        for path in sorted(set(paths))
        if ".git" not in path.parts and "__pycache__" not in path.parts
    ]


class DocumentationHygieneTests(unittest.TestCase):
    def test_current_docs_do_not_describe_project_as_early_mvp(self) -> None:
        violations: list[str] = []
        for path in iter_documentation_files():
            text = path.read_text(encoding="utf-8")
            for phrase in FORBIDDEN_CURRENT_STATUS_PHRASES:
                if phrase in text:
                    violations.append(f"{path.relative_to(REPO_ROOT)} contains {phrase!r}")

        self.assertEqual([], violations)

    def test_public_docs_do_not_include_local_machine_paths(self) -> None:
        violations: list[str] = []
        for path in iter_documentation_files():
            text = path.read_text(encoding="utf-8")
            for local_path in FORBIDDEN_LOCAL_PATHS:
                if local_path in text:
                    violations.append(f"{path.relative_to(REPO_ROOT)} contains {local_path!r}")

        self.assertEqual([], violations)

    def test_public_adapter_has_no_owner_specific_workflow_rules(self) -> None:
        adapter = (
            REPO_ROOT / "skills" / "cobsidian" / "agents" / "claude.md"
        ).read_text(encoding="utf-8")

        self.assertNotIn("做后端就用superpowers", adapter)
        self.assertNotIn("做知识整理就用cobsidian skill", adapter)


if __name__ == "__main__":
    unittest.main()
