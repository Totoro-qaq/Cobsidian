from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def iter_markdown_files(vault_path: Path) -> list[Path]:
    ignored_dirs = {".obsidian", ".git", "__pycache__", ".trash"}
    return sorted(
        path
        for path in vault_path.rglob("*.md")
        if path.is_file() and not any(part in ignored_dirs for part in path.parts)
    )


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
    links: list[str] = []
    for raw_link in WIKILINK_RE.findall(text):
        target = raw_link.split("|", 1)[0].split("#", 1)[0].split("^", 1)[0].strip()
        if target:
            links.append(target)
    return links


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate basic Obsidian Markdown note hygiene.")
    parser.add_argument("vault", type=Path)
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when warnings are found.")
    args = parser.parse_args()

    vault_path = args.vault.expanduser().resolve()
    if not vault_path.exists() or not vault_path.is_dir():
        raise SystemExit(f"Vault path does not exist or is not a directory: {vault_path}")

    files = iter_markdown_files(vault_path)
    title_to_paths: dict[str, list[str]] = defaultdict(list)
    known_targets: set[str] = set()
    texts: dict[Path, str] = {}

    for path in files:
        text = read_text(path)
        texts[path] = text
        title = extract_title(path, text)
        relative_path = path.relative_to(vault_path).as_posix()
        title_to_paths[title].append(relative_path)
        known_targets.add(title)
        known_targets.add(path.stem)
        known_targets.add(relative_path.removesuffix(".md"))

    warnings: list[str] = []
    for title, paths in sorted(title_to_paths.items()):
        if len(paths) > 1:
            warnings.append(f"Duplicate title '{title}': {', '.join(paths)}")

    for path, text in texts.items():
        relative_path = path.relative_to(vault_path).as_posix()
        if not text.strip():
            warnings.append(f"Empty note: {relative_path}")
        for target in extract_wikilinks(text):
            if target not in known_targets:
                warnings.append(f"Missing wikilink target in {relative_path}: [[{target}]]")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("No basic note hygiene issues found.")

    return 1 if warnings and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())

