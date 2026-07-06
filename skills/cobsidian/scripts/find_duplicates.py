from __future__ import annotations

import argparse
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path


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


def normalize_title(title: str) -> str:
    lowered = title.casefold()
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", lowered)


def main() -> int:
    parser = argparse.ArgumentParser(description="Find duplicate or similar Obsidian note titles.")
    parser.add_argument("vault", type=Path)
    parser.add_argument("--threshold", type=float, default=0.86, help="Similarity threshold from 0 to 1.")
    args = parser.parse_args()

    vault_path = args.vault.expanduser().resolve()
    if not vault_path.exists() or not vault_path.is_dir():
        raise SystemExit(f"Vault path does not exist or is not a directory: {vault_path}")

    notes: list[tuple[str, str, str]] = []
    for path in iter_markdown_files(vault_path):
        title = extract_title(path, read_text(path))
        notes.append((path.relative_to(vault_path).as_posix(), title, normalize_title(title)))

    exact: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for relative_path, title, normalized in notes:
        if normalized:
            exact[normalized].append((relative_path, title))

    found = False
    print("Exact duplicate titles:")
    for matches in exact.values():
        if len(matches) > 1:
            found = True
            print("-")
            for relative_path, title in matches:
                print(f"  {title} :: {relative_path}")

    print("\nSimilar titles:")
    for index, left in enumerate(notes):
        for right in notes[index + 1 :]:
            if not left[2] or not right[2] or left[2] == right[2]:
                continue
            score = SequenceMatcher(None, left[2], right[2]).ratio()
            if score >= args.threshold:
                found = True
                print(f"- {score:.2f}: {left[1]} :: {left[0]} <-> {right[1]} :: {right[0]}")

    if not found:
        print("No duplicate or highly similar titles found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

