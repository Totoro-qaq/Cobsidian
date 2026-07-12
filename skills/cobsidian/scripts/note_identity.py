from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Protocol


WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^\)]+\)")
HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")
NON_IDENTITY_RE = re.compile(r"[^a-z0-9\u4e00-\u9fff]+")
PREFIX_SEPARATOR_RE = re.compile(r"^[\s\-_:：—–/\\]+")

# These are workflow/type prefixes, not arbitrary first words. Keeping the list
# explicit prevents a legitimate topic such as "Agent-Architecture" from being
# shortened just because it contains a separator.
DEFAULT_MODE_PREFIXES = (
    "learning",
    "project",
    "review",
    "comparison",
    "index",
    "capture",
    "dissection",
    "学习记录",
    "学习经历",
    "学习",
    "项目",
    "复盘",
    "对比",
    "索引",
    "捕获",
    "拆解",
    "面试官问",
    "面试题库",
    "竞赛论文",
    "论文资产",
)


class IdentityNoteLike(Protocol):
    path: str
    title: str


@dataclass(frozen=True)
class NoteIdentity:
    filename_title: str
    heading_title: str | None
    frontmatter_title: str | None
    aliases: tuple[str, ...]
    core_titles: tuple[str, ...]
    candidate_titles: tuple[str, ...]

    @property
    def display_title(self) -> str:
        return self.frontmatter_title or self.heading_title or self.filename_title


def normalize_title(title: str) -> str:
    return NON_IDENTITY_RE.sub("", title.casefold())


def clean_markdown_title(value: str) -> str:
    def replace_wikilink(match: re.Match[str]) -> str:
        raw = match.group(1)
        target, separator, alias = raw.partition("|")
        selected = alias if separator and alias.strip() else target
        selected = selected.split("#", 1)[0].split("^", 1)[0]
        return Path(selected.strip()).stem

    cleaned = WIKILINK_RE.sub(replace_wikilink, value)
    cleaned = MARKDOWN_LINK_RE.sub(r"\1", cleaned)
    cleaned = HTML_TAG_RE.sub(" ", cleaned)
    cleaned = cleaned.replace("`", "")
    cleaned = re.sub(r"(?<!\\)[*_~]+", "", cleaned)
    cleaned = cleaned.replace("\\", "")
    return WHITESPACE_RE.sub(" ", cleaned).strip(" #\t")


def strip_mode_prefix(
    title: str,
    prefixes: Iterable[str] = DEFAULT_MODE_PREFIXES,
) -> str:
    cleaned = clean_markdown_title(title).strip()
    ordered_prefixes = sorted(
        {prefix.strip() for prefix in prefixes if prefix and prefix.strip()},
        key=len,
        reverse=True,
    )
    folded = cleaned.casefold()
    for prefix in ordered_prefixes:
        folded_prefix = prefix.casefold()
        if not folded.startswith(folded_prefix):
            continue
        remainder = cleaned[len(prefix) :]
        if not remainder:
            continue
        if not PREFIX_SEPARATOR_RE.match(remainder):
            continue
        stripped = PREFIX_SEPARATOR_RE.sub("", remainder, count=1).strip()
        if stripped:
            return stripped
    return cleaned


def _parse_scalar(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {'"', "'"}:
        return stripped[1:-1].strip()
    return stripped


def _parse_inline_aliases(value: str) -> list[str]:
    stripped = value.strip()
    if not stripped:
        return []
    if stripped.startswith("[") and stripped.endswith("]"):
        try:
            parsed = ast.literal_eval(stripped)
        except (SyntaxError, ValueError):
            parsed = [part.strip() for part in stripped[1:-1].split(",")]
        if isinstance(parsed, (list, tuple)):
            return [str(item).strip() for item in parsed if str(item).strip()]
    scalar = _parse_scalar(stripped)
    return [scalar] if scalar else []


def parse_frontmatter_identity(text: str) -> tuple[str | None, tuple[str, ...]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, ()

    closing_index = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if closing_index is None:
        return None, ()

    title: str | None = None
    aliases: list[str] = []
    collecting_aliases = False
    alias_indent = 0
    for raw_line in lines[1:closing_index]:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()
        if collecting_aliases and stripped.startswith("-") and indent > alias_indent:
            alias = _parse_scalar(stripped[1:].strip())
            if alias:
                aliases.append(alias)
            continue
        collecting_aliases = False
        if ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        normalized_key = key.strip().casefold()
        if normalized_key == "title":
            parsed_title = clean_markdown_title(_parse_scalar(raw_value))
            title = parsed_title or None
        elif normalized_key in {"alias", "aliases"}:
            collecting_aliases = not raw_value.strip()
            alias_indent = indent
            aliases.extend(_parse_inline_aliases(raw_value))

    cleaned_aliases = tuple(
        _dedupe_preserving_order(
            clean_markdown_title(alias) for alias in aliases if clean_markdown_title(alias)
        )
    )
    return title, cleaned_aliases


def extract_heading_title(text: str) -> str | None:
    lines = text.splitlines()
    start_index = 0
    if lines and lines[0].strip() == "---":
        closing_index = next(
            (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
            None,
        )
        if closing_index is not None:
            start_index = closing_index + 1
    for line in lines[start_index:]:
        heading_match = re.match(r"^ {0,3}#\s+(.+)$", line)
        if heading_match:
            cleaned = clean_markdown_title(heading_match.group(1))
            if cleaned:
                return cleaned
    return None


def _dedupe_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = normalize_title(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(value)
    return result


def build_note_identity(path: Path, text: str) -> NoteIdentity:
    filename_title = clean_markdown_title(path.stem)
    heading_title = extract_heading_title(text)
    frontmatter_title, aliases = parse_frontmatter_identity(text)
    primary_titles = _dedupe_preserving_order(
        value
        for value in (frontmatter_title, heading_title, filename_title, *aliases)
        if value
    )
    core_titles = _dedupe_preserving_order(
        stripped
        for title in primary_titles
        if (stripped := strip_mode_prefix(title)) and normalize_title(stripped) != normalize_title(title)
    )
    candidate_titles = tuple(_dedupe_preserving_order([*primary_titles, *core_titles]))
    return NoteIdentity(
        filename_title=filename_title,
        heading_title=heading_title,
        frontmatter_title=frontmatter_title,
        aliases=aliases,
        core_titles=tuple(core_titles),
        candidate_titles=candidate_titles,
    )


def note_candidate_titles(note: IdentityNoteLike) -> tuple[str, ...]:
    explicit = getattr(note, "identity_titles", ())
    if explicit:
        return tuple(explicit)
    filename_title = clean_markdown_title(Path(note.path).stem)
    values = _dedupe_preserving_order(
        [
            clean_markdown_title(note.title),
            filename_title,
            strip_mode_prefix(note.title),
            strip_mode_prefix(filename_title),
        ]
    )
    return tuple(values)


def query_candidate_titles(topic: str) -> tuple[str, ...]:
    cleaned = clean_markdown_title(topic)
    return tuple(_dedupe_preserving_order([cleaned, strip_mode_prefix(cleaned)]))
