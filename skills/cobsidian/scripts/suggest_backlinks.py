from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path


TOKEN_RE = re.compile(r"[A-Za-z0-9_+\-.#]{2,}|[\u4e00-\u9fff]{2,}")
STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "this",
    "that",
    "into",
    "note",
    "notes",
    "学习",
    "项目",
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def iter_markdown_files(vault_path: Path) -> list[Path]:
    ignored_dirs = {".obsidian", ".git", "__pycache__", ".trash"}
    return sorted(
        path
        for path in vault_path.rglob("*.md")
        if path.is_file() and not any(part in ignored_dirs for part in path.parts)
    )


def extract_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            if title:
                return title
    return path.stem


def tokenize(text: str) -> Counter[str]:
    tokens = [token.casefold() for token in TOKEN_RE.findall(text)]
    return Counter(token for token in tokens if token not in STOPWORDS)


def score_note(query_tokens: Counter[str], note_tokens: Counter[str]) -> int:
    return sum(min(count, note_tokens[token]) for token, count in query_tokens.items())


def main() -> int:
    parser = argparse.ArgumentParser(description="Suggest related Obsidian notes for a draft or note.")
    parser.add_argument("vault", type=Path)
    parser.add_argument("--file", type=Path, help="Draft or note file to compare against the vault.")
    parser.add_argument("--text", type=str, help="Raw text to compare against the vault.")
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    if not args.file and not args.text:
        raise SystemExit("Provide --file or --text.")

    vault_path = args.vault.expanduser().resolve()
    if not vault_path.exists() or not vault_path.is_dir():
        raise SystemExit(f"Vault path does not exist or is not a directory: {vault_path}")

    query_text = read_text(args.file.expanduser().resolve()) if args.file else args.text
    query_tokens = tokenize(query_text or "")
    if not query_tokens:
        print("No usable tokens found for backlink suggestions.")
        return 0

    suggestions: list[tuple[int, str, str]] = []
    compared_file = args.file.expanduser().resolve() if args.file else None
    for path in iter_markdown_files(vault_path):
        if compared_file and path.resolve() == compared_file:
            continue
        text = read_text(path)
        title = extract_title(path, text)
        score = score_note(query_tokens, tokenize(f"{title}\n{text}"))
        if score > 0:
            suggestions.append((score, title, path.relative_to(vault_path).as_posix()))

    for score, title, relative_path in sorted(suggestions, reverse=True)[: args.limit]:
        print(f"- [[{title}]] score={score} path={relative_path}")
    if not suggestions:
        print("No backlink suggestions found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

