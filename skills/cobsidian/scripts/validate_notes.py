from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

try:
    from cobsidian_config import load_config, resolve_vault_path
    from note_identity import build_note_identity
    from scan_vault import iter_markdown_files, read_text
except ModuleNotFoundError:
    from .cobsidian_config import load_config, resolve_vault_path
    from .note_identity import build_note_identity
    from .scan_vault import iter_markdown_files, read_text


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def extract_title(path: Path, text: str) -> str:
    return build_note_identity(path, text).display_title


def extract_wikilinks(text: str) -> list[str]:
    links: list[str] = []
    for raw_link in WIKILINK_RE.findall(text):
        target = raw_link.split("|", 1)[0].split("#", 1)[0].split("^", 1)[0].strip()
        if target:
            links.append(target)
    return links


def validate_vault(vault_path: Path) -> list[str]:
    files = sorted(iter_markdown_files(vault_path))
    title_to_paths: dict[str, list[str]] = defaultdict(list)
    known_targets: set[str] = set()
    texts: dict[Path, str] = {}

    for path in files:
        text = read_text(path)
        texts[path] = text
        identity = build_note_identity(path, text)
        title = identity.display_title
        relative_path = path.relative_to(vault_path).as_posix()
        title_to_paths[title].append(relative_path)
        known_targets.update(identity.candidate_titles)
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

    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate basic Obsidian Markdown note hygiene.")
    parser.add_argument("vault", nargs="?", type=Path)
    parser.add_argument("--config", type=Path, help="Path to cobsidian.config.yml.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when warnings are found.")
    args = parser.parse_args()

    config = load_config(args.config)
    vault_path = resolve_vault_path(args.vault, config)
    strict = args.strict or config.validation_strict
    if not vault_path.exists() or not vault_path.is_dir():
        raise SystemExit(f"Vault path does not exist or is not a directory: {vault_path}")

    warnings = validate_vault(vault_path)

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("No basic note hygiene issues found.")

    return 1 if warnings and strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
