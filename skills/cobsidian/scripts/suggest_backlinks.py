from __future__ import annotations

import argparse
from pathlib import Path

from cobsidian_config import load_config, resolve_vault_path
from retrieval import build_query, build_search_documents, rank_backlinks, read_utf8
from scan_vault import scan_vault


def main() -> int:
    parser = argparse.ArgumentParser(description="Suggest related Obsidian notes for a draft or note.")
    parser.add_argument("vault", nargs="?", type=Path)
    parser.add_argument("--config", type=Path, help="Path to cobsidian.config.yml.")
    parser.add_argument("--topic", help="Optional topic/title signal for ranking.")
    parser.add_argument("--file", type=Path, help="Draft or note file to compare against the vault.")
    parser.add_argument("--text", type=str, help="Raw text to compare against the vault.")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    if not args.topic and not args.file and not args.text:
        raise SystemExit("Provide --topic, --file, or --text.")

    config = load_config(args.config)
    vault_path = resolve_vault_path(args.vault, config)
    limit = args.limit if args.limit is not None else config.max_suggested_backlinks
    if not vault_path.exists() or not vault_path.is_dir():
        raise SystemExit(f"Vault path does not exist or is not a directory: {vault_path}")

    compared_file = args.file.expanduser().resolve() if args.file else None
    query_text = read_utf8(compared_file) if compared_file else str(args.text or "")
    query = build_query(topic=args.topic, text=query_text)
    if not query:
        print("No usable tokens found for backlink suggestions.")
        return 0

    excluded_paths: set[str] = set()
    if compared_file is not None:
        try:
            excluded_paths.add(compared_file.relative_to(vault_path.resolve()).as_posix())
        except ValueError:
            pass

    suggestions = rank_backlinks(
        query,
        build_search_documents(vault_path, scan_vault(vault_path)),
        limit=limit,
        excluded_paths=excluded_paths,
    )

    for suggestion in suggestions:
        print(
            f"- [[{suggestion.title}]] "
            f"score={suggestion.score} path={suggestion.path}"
        )
    if not suggestions:
        print("No backlink suggestions found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
