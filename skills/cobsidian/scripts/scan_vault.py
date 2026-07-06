from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from cobsidian_config import CobsidianConfig, load_config, resolve_vault_path


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
TAG_RE = re.compile(r"(?<!\w)#([A-Za-z0-9_/\-]+)")


@dataclass(frozen=True)
class NoteInfo:
    path: str
    title: str
    tags: list[str]
    wikilinks: list[str]
    bytes: int


def iter_markdown_files(vault_path: Path) -> Iterable[Path]:
    ignored_dirs = {".obsidian", ".git", "__pycache__", ".trash"}
    for path in vault_path.rglob("*.md"):
        if any(part in ignored_dirs for part in path.parts):
            continue
        if path.is_file():
            yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def extract_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            if title:
                return title
    return path.stem


def extract_wikilinks(text: str) -> list[str]:
    links: set[str] = set()
    for raw_link in WIKILINK_RE.findall(text):
        target = raw_link.split("|", 1)[0].split("#", 1)[0].split("^", 1)[0].strip()
        if target:
            links.add(target)
    return sorted(links)


def extract_tags(text: str) -> list[str]:
    return sorted(set(TAG_RE.findall(text)))


def scan_vault(vault_path: Path) -> list[NoteInfo]:
    notes: list[NoteInfo] = []
    for path in sorted(iter_markdown_files(vault_path)):
        text = read_text(path)
        notes.append(
            NoteInfo(
                path=path.relative_to(vault_path).as_posix(),
                title=extract_title(path, text),
                tags=extract_tags(text),
                wikilinks=extract_wikilinks(text),
                bytes=path.stat().st_size,
            )
        )
    return notes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scan an Obsidian vault and summarize Markdown notes.")
    parser.add_argument("vault", nargs="?", type=Path, help="Path to the Obsidian vault or note folder.")
    parser.add_argument("--config", type=Path, help="Path to cobsidian.config.yml.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def build_payload(vault_path: Path, notes: list[NoteInfo], config: CobsidianConfig) -> dict[str, object]:
    payload: dict[str, object] = {
        "vault": str(vault_path),
        "note_count": len(notes),
        "notes": [asdict(note) for note in notes],
    }
    if config.config_path:
        payload["config"] = config.public_summary()
    return payload


def main() -> int:
    args = build_parser().parse_args()
    config = load_config(args.config)
    vault_path = resolve_vault_path(args.vault, config)
    if not vault_path.exists() or not vault_path.is_dir():
        raise SystemExit(f"Vault path does not exist or is not a directory: {vault_path}")

    notes = scan_vault(vault_path)
    payload = build_payload(vault_path, notes, config)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Vault: {vault_path}")
        print(f"Notes: {len(notes)}")
        for note in notes:
            print(f"- {note.path}: {note.title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
