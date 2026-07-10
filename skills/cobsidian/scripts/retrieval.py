from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol


LATIN_TOKEN_RE = re.compile(r"[A-Za-z0-9_+\-.#]{2,}")
CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]{2,}")
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
}


@dataclass(frozen=True)
class SearchDocument:
    title: str
    path: str
    text: str


@dataclass(frozen=True)
class RankedBacklink:
    title: str
    path: str
    score: int


class NoteLike(Protocol):
    path: str
    title: str
    tags: list[str]
    wikilinks: list[str]


def cjk_ngrams(run: str) -> list[str]:
    grams: list[str] = []
    for size in (2, 3):
        if len(run) < size:
            continue
        grams.extend(run[index : index + size] for index in range(len(run) - size + 1))
    return grams


def tokenize(text: str) -> Counter[str]:
    tokens = [
        token.casefold()
        for token in LATIN_TOKEN_RE.findall(text)
        if token.casefold() not in STOPWORDS
    ]
    for run in CJK_RUN_RE.findall(text):
        tokens.extend(cjk_ngrams(run))
    return Counter(tokens)


def score_tokens(query_tokens: Counter[str], document_tokens: Counter[str]) -> int:
    return sum(
        min(query_count, document_tokens[token])
        for token, query_count in query_tokens.items()
    )


def read_utf8(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def build_search_documents(
    vault_path: Path,
    notes: Iterable[NoteLike],
) -> list[SearchDocument]:
    documents: list[SearchDocument] = []
    for note in notes:
        body = read_utf8(vault_path / note.path)
        metadata = " ".join([*note.tags, *note.wikilinks])
        documents.append(
            SearchDocument(
                title=note.title,
                path=note.path,
                text=f"{metadata}\n{body}",
            )
        )
    return documents


def rank_backlinks(
    query: str,
    documents: list[SearchDocument],
    limit: int,
    excluded_paths: set[str] | None = None,
) -> list[RankedBacklink]:
    query_tokens = tokenize(query)
    excluded = excluded_paths or set()
    ranked: list[RankedBacklink] = []
    for document in documents:
        if document.path in excluded:
            continue
        document_tokens = tokenize(f"{document.title}\n{document.text}")
        score = score_tokens(query_tokens, document_tokens)
        if score > 0:
            ranked.append(
                RankedBacklink(
                    title=document.title,
                    path=document.path,
                    score=score,
                )
            )
    return sorted(
        ranked,
        key=lambda item: (-item.score, item.path.casefold()),
    )[:limit]
