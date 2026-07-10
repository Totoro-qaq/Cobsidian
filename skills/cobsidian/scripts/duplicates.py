from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Protocol


DEFAULT_MAX_COMPARISONS = 100_000


class NoteInfoLike(Protocol):
    path: str
    title: str
    tags: list[str]
    wikilinks: list[str]
    bytes: int


@dataclass(frozen=True)
class SimilarTitle:
    score: float
    left: NoteInfoLike
    right: NoteInfoLike


@dataclass(frozen=True)
class DuplicateReport:
    exact_duplicates: list[list[NoteInfoLike]]
    similar_titles: list[SimilarTitle]
    comparisons: int
    truncated: bool


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", title.casefold())


def find_title_duplicates(
    notes: list[NoteInfoLike],
    threshold: float,
    max_comparisons: int = DEFAULT_MAX_COMPARISONS,
) -> DuplicateReport:
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1.")
    if max_comparisons < 0:
        raise ValueError("max_comparisons must be non-negative.")

    exact_by_title: dict[str, list[NoteInfoLike]] = defaultdict(list)
    normalized_notes: list[tuple[NoteInfoLike, str]] = []
    for note in notes:
        normalized = normalize_title(note.title)
        if normalized:
            exact_by_title[normalized].append(note)
            normalized_notes.append((note, normalized))

    exact_duplicates = [
        sorted(group, key=lambda note: note.path.casefold())
        for group in exact_by_title.values()
        if len(group) > 1
    ]
    exact_duplicates.sort(key=lambda group: group[0].path.casefold())

    similar_titles: list[SimilarTitle] = []
    comparisons = 0
    truncated = False
    for index, (left, left_title) in enumerate(normalized_notes):
        for right, right_title in normalized_notes[index + 1 :]:
            if left_title == right_title:
                continue
            if comparisons >= max_comparisons:
                truncated = True
                break
            comparisons += 1
            score = SequenceMatcher(None, left_title, right_title).ratio()
            if score >= threshold:
                similar_titles.append(
                    SimilarTitle(
                        score=round(score, 4),
                        left=left,
                        right=right,
                    )
                )
        if truncated:
            break

    similar_titles.sort(
        key=lambda item: (
            -item.score,
            item.left.path.casefold(),
            item.right.path.casefold(),
        )
    )
    return DuplicateReport(
        exact_duplicates=exact_duplicates,
        similar_titles=similar_titles,
        comparisons=comparisons,
        truncated=truncated,
    )
