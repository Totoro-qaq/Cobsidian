from __future__ import annotations

import os
import sys
from collections import defaultdict
from dataclasses import asdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from cobsidian_config import CobsidianConfig, load_config, resolve_vault_path  # noqa: E402
from dry_run import build_payload as build_dry_run_payload  # noqa: E402
from dry_run import find_duplicate_risks  # noqa: E402
from retrieval import build_search_documents, rank_backlinks  # noqa: E402
from scan_vault import NoteInfo, read_text, scan_vault  # noqa: E402
from validate_notes import extract_wikilinks  # noqa: E402


SERVER_NAME = "cobsidian"


def resolve_optional_path(path: str | None) -> Path | None:
    return Path(path).expanduser().resolve() if path else None


def resolve_vault_from_inputs(vault: str | None = None, config: str | None = None) -> tuple[Path, CobsidianConfig]:
    loaded_config = load_config(resolve_optional_path(config))
    vault_path = resolve_vault_path(resolve_optional_path(vault), loaded_config)
    if not vault_path.exists() or not vault_path.is_dir():
        raise ValueError(f"Vault path does not exist or is not a directory: {vault_path}")
    return vault_path, loaded_config


def ensure_relative_path_inside_vault(vault_path: Path, relative_path: str) -> Path:
    if Path(relative_path).is_absolute():
        raise ValueError("Note path must be relative to the vault.")

    resolved_vault = vault_path.expanduser().resolve()
    resolved_note = (resolved_vault / relative_path).resolve()
    try:
        resolved_note.relative_to(resolved_vault)
    except ValueError as exc:
        raise ValueError("Note path escapes the vault.") from exc
    return resolved_note


def notes_to_payload(vault_path: Path, notes: list[NoteInfo], config: CobsidianConfig) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "vault": str(vault_path),
        "note_count": len(notes),
        "notes": [asdict(note) for note in notes],
    }
    if config.config_path:
        payload["config"] = config.public_summary()
    return payload


def tool_cobsidian_scan_vault(vault: str | None = None, config: str | None = None) -> dict[str, Any]:
    vault_path, loaded_config = resolve_vault_from_inputs(vault=vault, config=config)
    return notes_to_payload(vault_path, scan_vault(vault_path), loaded_config)


def tool_cobsidian_find_duplicates(
    vault: str | None = None,
    config: str | None = None,
    threshold: float | None = None,
) -> dict[str, Any]:
    vault_path, loaded_config = resolve_vault_from_inputs(vault=vault, config=config)
    notes = scan_vault(vault_path)
    title_to_notes: dict[str, list[NoteInfo]] = defaultdict(list)
    for note in notes:
        title_to_notes[note.title.casefold()].append(note)

    exact_duplicates = [
        [asdict(note) for note in matches]
        for matches in title_to_notes.values()
        if len(matches) > 1
    ]

    similar_threshold = threshold if threshold is not None else loaded_config.similar_title_threshold
    similar: list[dict[str, Any]] = []
    for index, left in enumerate(notes):
        for right in notes[index + 1 :]:
            if left.title.casefold() == right.title.casefold():
                continue
            score = SequenceMatcher(None, left.title.casefold(), right.title.casefold()).ratio()
            if score >= similar_threshold:
                similar.append(
                    {
                        "score": round(score, 4),
                        "left": asdict(left),
                        "right": asdict(right),
                    }
                )

    return {
        "vault": str(vault_path),
        "threshold": similar_threshold,
        "exact_duplicates": exact_duplicates,
        "similar_titles": similar,
    }


def tool_cobsidian_suggest_backlinks(
    vault: str | None = None,
    config: str | None = None,
    text: str | None = None,
    note_path: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    if not text and not note_path:
        raise ValueError("Provide text or note_path.")

    vault_path, loaded_config = resolve_vault_from_inputs(vault=vault, config=config)
    compared_file = ensure_relative_path_inside_vault(vault_path, note_path) if note_path else None
    source_text = read_text(compared_file) if compared_file else str(text)
    max_results = limit if limit is not None else loaded_config.max_suggested_backlinks

    notes = scan_vault(vault_path)
    suggestions = rank_backlinks(
        source_text,
        build_search_documents(vault_path, notes),
        limit=max_results,
        excluded_paths={note_path} if note_path else set(),
    )

    return {
        "vault": str(vault_path),
        "suggestions": [asdict(suggestion) for suggestion in suggestions],
    }


def tool_cobsidian_validate_notes(vault: str | None = None, config: str | None = None) -> dict[str, Any]:
    vault_path, loaded_config = resolve_vault_from_inputs(vault=vault, config=config)
    notes = scan_vault(vault_path)
    title_to_paths: dict[str, list[str]] = defaultdict(list)
    known_targets: set[str] = set()
    warnings: list[str] = []

    for note in notes:
        title_to_paths[note.title].append(note.path)
        known_targets.add(note.title)
        known_targets.add(Path(note.path).stem)
        known_targets.add(note.path.removesuffix(".md"))

    for title, paths in sorted(title_to_paths.items()):
        if len(paths) > 1:
            warnings.append(f"Duplicate title '{title}': {', '.join(paths)}")

    for note in notes:
        text = read_text(vault_path / note.path)
        if not text.strip():
            warnings.append(f"Empty note: {note.path}")
        for target in extract_wikilinks(text):
            if target not in known_targets:
                warnings.append(f"Missing wikilink target in {note.path}: [[{target}]]")

    return {
        "vault": str(vault_path),
        "strict": loaded_config.validation_strict,
        "warning_count": len(warnings),
        "warnings": warnings,
    }


def tool_cobsidian_dry_run(
    topic: str,
    text: str,
    vault: str | None = None,
    config: str | None = None,
    mode: str | None = None,
) -> dict[str, Any]:
    vault_path, loaded_config = resolve_vault_from_inputs(vault=vault, config=config)
    notes = scan_vault(vault_path)
    return build_dry_run_payload(
        vault_path=vault_path,
        config=loaded_config,
        topic=topic,
        mode=mode or loaded_config.mode,
        text=text,
        notes=notes,
    )


def create_mcp_server() -> FastMCP:
    server = FastMCP(
        SERVER_NAME,
        instructions=(
            "Cobsidian exposes local Obsidian/Markdown vault planning tools. "
            "Use dry-run before write workflows; this server does not provide a write tool."
        ),
    )

    server.tool(name="cobsidian_scan_vault")(tool_cobsidian_scan_vault)
    server.tool(name="cobsidian_find_duplicates")(tool_cobsidian_find_duplicates)
    server.tool(name="cobsidian_suggest_backlinks")(tool_cobsidian_suggest_backlinks)
    server.tool(name="cobsidian_validate_notes")(tool_cobsidian_validate_notes)
    server.tool(name="cobsidian_dry_run")(tool_cobsidian_dry_run)

    @server.resource("cobsidian://config", mime_type="application/json")
    def read_config_resource() -> dict[str, Any]:
        config_path = resolve_optional_path(os.environ.get("COBSIDIAN_CONFIG"))
        return load_config(config_path).public_summary()

    @server.resource("cobsidian://vault-summary", mime_type="application/json")
    def read_vault_summary_resource() -> dict[str, Any]:
        vault_path, loaded_config = resolve_vault_from_inputs(
            vault=os.environ.get("COBSIDIAN_VAULT"),
            config=os.environ.get("COBSIDIAN_CONFIG"),
        )
        return notes_to_payload(vault_path, scan_vault(vault_path), loaded_config)

    @server.resource("cobsidian://note/{note_path}", mime_type="text/markdown")
    def read_note_resource(note_path: str) -> str:
        vault_path, _ = resolve_vault_from_inputs(
            vault=os.environ.get("COBSIDIAN_VAULT"),
            config=os.environ.get("COBSIDIAN_CONFIG"),
        )
        return read_text(ensure_relative_path_inside_vault(vault_path, note_path))

    @server.prompt(name="cobsidian-dry-run")
    def dry_run_prompt(vault: str, topic: str, material: str) -> str:
        return (
            "Use Cobsidian dry-run first. "
            f"Vault: {vault}\n"
            f"Topic: {topic}\n\n"
            f"Material:\n{material}\n\n"
            "Return the target note, create/append decision, duplicate risks, backlink suggestions, "
            "validation intent, and writes as an empty list."
        )

    @server.prompt(name="cobsidian-organize-after-confirmation")
    def organize_after_confirmation_prompt(vault: str, topic: str, material: str) -> str:
        return (
            "Use Cobsidian to organize this material after the user confirms the dry-run plan. "
            f"Vault: {vault}\n"
            f"Topic: {topic}\n\n"
            f"Material:\n{material}\n\n"
            "Search existing notes first, avoid duplicates, add useful wiki links, run validation, "
            "and report files changed."
        )

    return server


def main() -> None:
    create_mcp_server().run(transport="stdio")


if __name__ == "__main__":
    main()
