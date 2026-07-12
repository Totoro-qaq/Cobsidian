from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


HOSTS = (
    "kimi-code",
    "opencode",
    "pi",
    "antigravity",
    "github-copilot-cli",
    "codex-cli",
    "claude-code-cli",
)
@dataclass(frozen=True)
class InstallResult:
    destination: str
    hosts: tuple[str, ...]
    operation: str
    scope: str


def host_destination(host: str, scope: str, home: Path, project: Path) -> Path:
    if host not in HOSTS:
        raise ValueError(f"Unsupported host: {host}")
    if scope not in {"user", "project"}:
        raise ValueError(f"Unsupported scope: {scope}")

    if scope == "project":
        base = project / (".claude/skills" if host == "claude-code-cli" else ".agents/skills")
    elif host == "antigravity":
        base = home / ".gemini/config/skills"
    elif host == "claude-code-cli":
        base = home / ".claude/skills"
    else:
        base = home / ".agents/skills"
    return base / "cobsidian"


def grouped_destinations(
    hosts: Iterable[str],
    scope: str,
    home: Path,
    project: Path,
) -> dict[Path, tuple[str, ...]]:
    grouped: dict[Path, list[str]] = {}
    for host in hosts:
        destination = host_destination(host, scope, home, project)
        grouped.setdefault(destination, []).append(host)
    return {
        destination: tuple(sorted(names))
        for destination, names in grouped.items()
    }


def replace_with_copy(source: Path, destination: Path, force: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        if not force:
            raise FileExistsError(
                f"Destination already exists: {destination}. Re-run with --force to replace it."
            )
        if destination.is_dir() and not destination.is_symlink():
            shutil.rmtree(destination)
        else:
            destination.unlink()

    staging_root = Path(
        tempfile.mkdtemp(prefix=".cobsidian-install-", dir=destination.parent)
    )
    staging_skill = staging_root / "cobsidian"
    try:
        shutil.copytree(source, staging_skill)
        os.replace(staging_skill, destination)
    finally:
        if staging_root.exists():
            shutil.rmtree(staging_root)


def replace_with_symlink(source: Path, destination: Path, force: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        if not force:
            raise FileExistsError(
                f"Destination already exists: {destination}. Re-run with --force to replace it."
            )
        if destination.is_dir() and not destination.is_symlink():
            shutil.rmtree(destination)
        else:
            destination.unlink()
    destination.symlink_to(source, target_is_directory=True)


def install(
    source: Path,
    hosts: Iterable[str],
    scope: str,
    home: Path,
    project: Path,
    *,
    force: bool = False,
    symlink: bool = False,
    dry_run: bool = False,
) -> list[InstallResult]:
    source = source.expanduser().resolve()
    if not (source / "SKILL.md").is_file():
        raise ValueError(f"Cobsidian skill source is invalid: {source}")

    results: list[InstallResult] = []
    for destination, destination_hosts in grouped_destinations(
        hosts, scope, home.expanduser(), project.expanduser().resolve()
    ).items():
        operation = "preview"
        if not dry_run:
            if symlink:
                replace_with_symlink(source, destination, force)
                operation = "symlinked"
            else:
                replace_with_copy(source, destination, force)
                operation = "copied"
        results.append(
            InstallResult(
                destination=str(destination),
                hosts=destination_hosts,
                operation=operation,
                scope=scope,
            )
        )
    return sorted(results, key=lambda item: item.destination)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Install Cobsidian into the official skill discovery paths of supported CLIs."
    )
    parser.add_argument(
        "--host",
        action="append",
        choices=(*HOSTS, "all"),
        required=True,
        help="Repeat for multiple hosts, or pass all.",
    )
    parser.add_argument("--scope", choices=("user", "project"), default="user")
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--home", type=Path, default=Path.home(), help=argparse.SUPPRESS)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--symlink", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    requested = list(HOSTS) if "all" in args.host else list(dict.fromkeys(args.host))
    source = Path(__file__).resolve().parent / "skills" / "cobsidian"
    results = install(
        source,
        requested,
        args.scope,
        args.home,
        args.project,
        force=args.force,
        symlink=args.symlink,
        dry_run=args.dry_run,
    )
    if args.json:
        print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))
        return
    for result in results:
        print(f"{result.operation}: {result.destination} ({', '.join(result.hosts)})")


if __name__ == "__main__":
    main()
