from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Protocol

try:
    from note_identity import normalize_title, note_candidate_titles
except ModuleNotFoundError:
    from .note_identity import normalize_title, note_candidate_titles


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


def find_title_duplicates(
    notes: list[NoteInfoLike],
    threshold: float,
    max_comparisons: int = DEFAULT_MAX_COMPARISONS,
) -> DuplicateReport:
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be between 0 and 1.")
    if max_comparisons < 0:
        raise ValueError("max_comparisons must be non-negative.")

    if not notes:
        return DuplicateReport([], [], 0, False)

    parents = list(range(len(notes)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parents[right_root] = left_root

    note_identities: list[dict[str, str]] = []
    identity_owner: dict[str, int] = {}
    for index, note in enumerate(notes):
        identities = {
            normalize_title(candidate): candidate
            for candidate in note_candidate_titles(note)
            if normalize_title(candidate)
        }
        note_identities.append(identities)
        for normalized in identities:
            previous = identity_owner.get(normalized)
            if previous is None:
                identity_owner[normalized] = index
            else:
                union(previous, index)

    components: dict[int, list[int]] = defaultdict(list)
    for index in range(len(notes)):
        components[find(index)].append(index)

    component_rows: list[tuple[NoteInfoLike, list[NoteInfoLike], set[str]]] = []
    for indexes in components.values():
        group = sorted((notes[index] for index in indexes), key=lambda note: note.path.casefold())
        identities = {
            normalized
            for index in indexes
            for normalized in note_identities[index]
        }
        component_rows.append((group[0], group, identities))
    component_rows.sort(key=lambda row: row[0].path.casefold())

    exact_duplicates = [group for _, group, _ in component_rows if len(group) > 1]

    similar_titles: list[SimilarTitle] = []
    comparisons = 0
    truncated = False
    for index, (left, _, left_titles) in enumerate(component_rows):
        for right_index in range(index + 1, len(component_rows)):
            if comparisons >= max_comparisons:
                truncated = True
                break
            right, _, right_titles = component_rows[right_index]
            comparisons += 1
            score = max(
                (
                    SequenceMatcher(None, left_title, right_title).ratio()
                    for left_title in left_titles
                    for right_title in right_titles
                ),
                default=0.0,
            )
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
