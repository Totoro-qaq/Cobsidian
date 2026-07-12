from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from install_cobsidian import HOSTS, grouped_destinations, host_destination, install


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_SOURCE = REPO_ROOT / "skills" / "cobsidian"


class HostAdapterInstallerTests(unittest.TestCase):
    def test_user_discovery_paths_match_supported_hosts(self) -> None:
        home = Path("/tmp/cobsidian-home")
        project = Path("/tmp/cobsidian-project")
        expected = {
            "kimi-code": home / ".agents/skills/cobsidian",
            "opencode": home / ".agents/skills/cobsidian",
            "pi": home / ".agents/skills/cobsidian",
            "github-copilot-cli": home / ".agents/skills/cobsidian",
            "codex-cli": home / ".agents/skills/cobsidian",
            "antigravity": home / ".gemini/config/skills/cobsidian",
            "claude-code-cli": home / ".claude/skills/cobsidian",
        }
        self.assertEqual(set(HOSTS), set(expected))
        for host, destination in expected.items():
            with self.subTest(host=host):
                self.assertEqual(destination, host_destination(host, "user", home, project))

    def test_project_install_uses_shared_agents_path_except_claude(self) -> None:
        home = Path("/tmp/cobsidian-home")
        project = Path("/tmp/cobsidian-project")
        for host in HOSTS:
            with self.subTest(host=host):
                expected_base = ".claude/skills" if host == "claude-code-cli" else ".agents/skills"
                self.assertEqual(
                    project / expected_base / "cobsidian",
                    host_destination(host, "project", home, project),
                )

    def test_shared_hosts_collapse_to_one_install_destination(self) -> None:
        grouped = grouped_destinations(
            HOSTS,
            "user",
            Path("/tmp/cobsidian-home"),
            Path("/tmp/cobsidian-project"),
        )
        self.assertEqual(3, len(grouped))

    def test_copy_install_is_functional_and_refuses_implicit_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            results = install(
                SKILL_SOURCE,
                ["codex-cli", "opencode"],
                "user",
                root / "home",
                root / "project",
            )
            self.assertEqual(1, len(results))
            destination = Path(results[0].destination)
            self.assertTrue((destination / "SKILL.md").is_file())
            self.assertTrue((destination / "scripts/write_executor.py").is_file())
            with self.assertRaises(FileExistsError):
                install(
                    SKILL_SOURCE,
                    ["codex-cli"],
                    "user",
                    root / "home",
                    root / "project",
                )

    def test_dry_run_does_not_create_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            results = install(
                SKILL_SOURCE,
                ["antigravity"],
                "user",
                root / "home",
                root / "project",
                dry_run=True,
            )
            self.assertEqual("preview", results[0].operation)
            self.assertFalse(Path(results[0].destination).exists())


if __name__ == "__main__":
    unittest.main()
