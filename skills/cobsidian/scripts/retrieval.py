from __future__ import annotations

import re
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Protocol


LATIN_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:"
    r"[A-Za-z][A-Za-z0-9_]*(?:\+\+|#)[A-Za-z0-9_]*"
    r"|[A-Za-z0-9_]+(?:[.-][A-Za-z0-9_]+)*"
    r"|(?<!\.)\.[A-Za-z0-9_]+"
    r")(?![A-Za-z0-9_])"
)
CJK_RUN_RE = re.compile(r"[\u4e00-\u9fff]{2,}")
MAX_BACKLINK_LIMIT = 100
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
CJK_STOPWORDS = {
    "一个",
    "什么",
    "内容",
    "如何",
    "学习",
    "整理",
    "相关",
    "知识",
    "笔记",
    "这个",
}


@dataclass(frozen=True)
class SearchDocument:
    title: str
    path: str
    text: str
    aliases: tuple[str, ...] = ()
    identity_titles: tuple[str, ...] = ()
    metadata: str = ""


@dataclass(frozen=True)
class RankedBacklink:
    title: str
    path: str
    score: float


class NoteLike(Protocol):
    path: str
    title: str
    tags: list[str]
    wikilinks: list[str]


def build_query(topic: str | None, text: str) -> str:
    parts = [part.strip() for part in (topic, text) if part and part.strip()]
    if not parts:
        raise ValueError("Provide at least one non-empty query source.")
    return "\n".join(parts)


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
        tokens.extend(
            token for token in cjk_ngrams(run) if token not in CJK_STOPWORDS
        )
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
) -> Iterator[SearchDocument]:
    for note in notes:
        body = read_utf8(vault_path / note.path)
        metadata = " ".join([*note.tags, *note.wikilinks])
        yield SearchDocument(
            title=note.title,
            path=note.path,
            text=body,
            aliases=tuple(getattr(note, "aliases", ())),
            identity_titles=tuple(getattr(note, "identity_titles", ())),
            metadata=metadata,
        )


def rank_backlinks(
    query: str,
    documents: Iterable[SearchDocument],
    limit: int,
    excluded_paths: set[str] | None = None,
) -> list[RankedBacklink]:
    if not 1 <= limit <= MAX_BACKLINK_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_BACKLINK_LIMIT}.")
    query_tokens = tokenize(query)
    query_terms = set(query_tokens)
    excluded = excluded_paths or set()
    candidates: list[
        tuple[
            SearchDocument,
            Counter[str],
            Counter[str],
            Counter[str],
            Counter[str],
        ]
    ] = []
    document_frequency: Counter[str] = Counter()
    document_count = 0
    for document in documents:
        if document.path in excluded:
            continue
        document_count += 1
        title_tokens = tokenize(
            "\n".join((document.title, *document.identity_titles))
        )
        alias_tokens = tokenize("\n".join(document.aliases))
        metadata_tokens = tokenize(document.metadata)
        body_tokens = tokenize(document.text)
        present_terms = {
            term
            for term in query_terms
            if title_tokens[term]
            or alias_tokens[term]
            or metadata_tokens[term]
            or body_tokens[term]
        }
        if not present_terms:
            continue
        document_frequency.update(present_terms)
        candidates.append(
            (
                document,
                title_tokens,
                alias_tokens,
                metadata_tokens,
                body_tokens,
            )
        )

    ranked: list[RankedBacklink] = []
    for document, title_tokens, alias_tokens, metadata_tokens, body_tokens in candidates:
        score = 0.0
        for term, query_count in query_tokens.items():
            if not (
                title_tokens[term]
                or alias_tokens[term]
                or metadata_tokens[term]
                or body_tokens[term]
            ):
                continue
            inverse_document_frequency = math.log(
                (document_count + 1) / (document_frequency[term] + 0.5)
            ) + 1.0
            query_weight = 1.0 + math.log1p(query_count)
            field_weight = (
                6.0 * min(1, title_tokens[term])
                + 5.0 * min(1, alias_tokens[term])
                + 2.5 * min(1, metadata_tokens[term])
                + 1.0 * min(2, body_tokens[term])
            )
            score += inverse_document_frequency * query_weight * field_weight
        ranked.append(
            RankedBacklink(
                title=document.title,
                path=document.path,
                score=round(score, 4),
            )
        )
        ranked.sort(key=lambda item: (-item.score, item.path.casefold()))
        if len(ranked) > limit:
            ranked.pop()
    return ranked
