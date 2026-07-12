from __future__ import annotations

import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import Field, StrictBool


SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from cobsidian_config import CobsidianConfig, load_config, resolve_vault_path  # noqa: E402
from duplicates import (  # noqa: E402
    DEFAULT_MAX_COMPARISONS,
    find_title_duplicates,
)
from dry_run import build_payload as build_dry_run_payload  # noqa: E402
from dry_run import find_duplicate_risks  # noqa: E402
from preflight import validated_capability  # noqa: E402
from retrieval import build_query, build_search_documents, rank_backlinks  # noqa: E402
from scan_vault import NoteInfo, read_text, scan_vault  # noqa: E402
from validate_notes import validate_vault  # noqa: E402


SERVER_NAME = "cobsidian"
DEFAULT_SCAN_LIMIT = 100
MAX_SCAN_LIMIT = 500
Mode = Literal[
    "learning",
    "project",
    "review",
    "comparison",
    "index",
    "capture",
    "dissection",
]
Depth = Literal["capture", "standard", "deep"]
Granularity = Literal["append", "single-note", "multi-note"]
Evidence = Literal["conversation", "source-grounded", "verified"]
DisplayPolicy = Literal["auto", "always", "off"]
CapabilityLevel = Literal[
    "full-local",
    "filesystem-only",
    "mcp-readonly",
    "chat-only",
]
RecommendedModes = Annotated[
    list[Mode],
    Field(max_length=2, json_schema_extra={"uniqueItems": True}),
]


def resolve_optional_path(path: str | None) -> Path | None:
    return Path(path).expanduser().resolve() if path else None


def resolve_vault_from_inputs(
    vault: str | None = None,
    config: str | None = None,
) -> tuple[Path, CobsidianConfig]:
    try:
        loaded_config = load_config(resolve_optional_path(config))
        vault_path = resolve_vault_path(resolve_optional_path(vault), loaded_config)
    except SystemExit as error:
        message = str(error).strip() or "Unable to resolve the vault or config path."
        raise ValueError(message) from error
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


def paginate_notes(
    notes: list[NoteInfo],
    offset: int,
    limit: int,
) -> list[NoteInfo]:
    if offset < 0:
        raise ValueError("offset must be non-negative.")
    if not 1 <= limit <= MAX_SCAN_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_SCAN_LIMIT}.")
    return notes[offset : offset + limit]


def notes_to_payload(
    vault_path: Path,
    notes: list[NoteInfo],
    config: CobsidianConfig,
    offset: int = 0,
    limit: int = DEFAULT_SCAN_LIMIT,
) -> dict[str, Any]:
    page = paginate_notes(notes, offset=offset, limit=limit)
    payload: dict[str, Any] = {
        "vault": str(vault_path),
        "note_count": len(notes),
        "total_note_count": len(notes),
        "page": {
            "offset": offset,
            "limit": limit,
            "returned": len(page),
        },
        "notes": [asdict(note) for note in page],
    }
    if config.config_path:
        payload["config"] = config.public_summary()
    return payload


def complete_notes_payload(
    vault_path: Path,
    notes: list[NoteInfo],
    config: CobsidianConfig,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "vault": str(vault_path),
        "note_count": len(notes),
        "total_note_count": len(notes),
        "notes": [asdict(note) for note in notes],
    }
    if config.config_path:
        payload["config"] = config.public_summary()
    return payload


def tool_cobsidian_scan_vault(
    vault: str | None = None,
    config: str | None = None,
    offset: int = 0,
    limit: int = DEFAULT_SCAN_LIMIT,
) -> dict[str, Any]:
    vault_path, loaded_config = resolve_vault_from_inputs(vault=vault, config=config)
    return notes_to_payload(
        vault_path,
        scan_vault(vault_path),
        loaded_config,
        offset=offset,
        limit=limit,
    )


def tool_cobsidian_find_duplicates(
    vault: str | None = None,
    config: str | None = None,
    threshold: float | None = None,
    max_comparisons: int = DEFAULT_MAX_COMPARISONS,
) -> dict[str, Any]:
    vault_path, loaded_config = resolve_vault_from_inputs(vault=vault, config=config)
    notes = scan_vault(vault_path)
    similar_threshold = threshold if threshold is not None else loaded_config.similar_title_threshold
    report = find_title_duplicates(
        notes,
        threshold=similar_threshold,
        max_comparisons=max_comparisons,
    )

    return {
        "vault": str(vault_path),
        "threshold": similar_threshold,
        "max_comparisons": max_comparisons,
        "comparisons": report.comparisons,
        "truncated": report.truncated,
        "exact_duplicates": [
            [asdict(note) for note in group]
            for group in report.exact_duplicates
        ],
        "similar_titles": [
            {
                "score": match.score,
                "left": asdict(match.left),
                "right": asdict(match.right),
            }
            for match in report.similar_titles
        ],
    }


def tool_cobsidian_suggest_backlinks(
    vault: str | None = None,
    config: str | None = None,
    topic: str | None = None,
    text: str | None = None,
    note_path: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    vault_path, loaded_config = resolve_vault_from_inputs(vault=vault, config=config)
    compared_file = ensure_relative_path_inside_vault(vault_path, note_path) if note_path else None
    source_text = read_text(compared_file) if compared_file else str(text or "")
    max_results = limit if limit is not None else loaded_config.max_suggested_backlinks
    query = build_query(topic=topic, text=source_text)

    notes = scan_vault(vault_path)
    suggestions = rank_backlinks(
        query,
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
    warnings = validate_vault(vault_path)

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
    mode: Mode | None = None,
    *,
    mode_explicit: StrictBool | None = None,
    recommended_modes: RecommendedModes | None = None,
    depth: Depth | None = None,
    granularity: Granularity | None = None,
    evidence: Evidence = "conversation",
    source_read_completed: StrictBool = False,
    verification_completed: StrictBool = False,
    validation_available: StrictBool | None = None,
    knowledge_read_policy: DisplayPolicy | None = None,
    capability_level: CapabilityLevel = "mcp-readonly",
) -> dict[str, Any]:
    vault_path, loaded_config = resolve_vault_from_inputs(vault=vault, config=config)
    resolved_mode = loaded_config.mode if mode is None else mode
    resolved_mode_explicit = (
        mode is not None if mode_explicit is None else mode_explicit
    )
    capability = validated_capability(capability_level)
    notes = scan_vault(vault_path) if capability.scan else []
    return build_dry_run_payload(
        vault_path=vault_path,
        config=loaded_config,
        topic=topic,
        mode=resolved_mode,
        text=text,
        notes=notes,
        mode_explicit=resolved_mode_explicit,
        recommended_modes=recommended_modes,
        depth=depth,
        granularity=granularity,
        evidence=evidence,
        source_read_completed=source_read_completed,
        verification_completed=verification_completed,
        validation_available=validation_available,
        capability_level=capability_level,
        knowledge_read_policy=knowledge_read_policy,
    )


def create_mcp_server() -> FastMCP:
    server = FastMCP(
        SERVER_NAME,
        instructions=(
            "Cobsidian is a read-only MCP server for local Obsidian/Markdown vault planning. "
            "Dry-run returns knowledge_read, preflight read-only readiness, and writes=[]. "
            "capability_level describes the active host's scan/write transport while "
            "validation_available reports validation independently; neither grants this MCP "
            "server write access."
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
        return complete_notes_payload(
            vault_path,
            scan_vault(vault_path),
            loaded_config,
        )

    @server.resource(
        "cobsidian://vault-page/{offset}/{limit}",
        mime_type="application/json",
    )
    def read_vault_page_resource(offset: int, limit: int) -> dict[str, Any]:
        vault_path, loaded_config = resolve_vault_from_inputs(
            vault=os.environ.get("COBSIDIAN_VAULT"),
            config=os.environ.get("COBSIDIAN_CONFIG"),
        )
        return notes_to_payload(
            vault_path,
            scan_vault(vault_path),
            loaded_config,
            offset=offset,
            limit=limit,
        )

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
            "Use Cobsidian dry-run first; this MCP server is read-only. "
            f"Vault: {vault}\n"
            f"Topic: {topic}\n\n"
            f"Material:\n{material}\n\n"
            "Return the target note, create/append decision, duplicate risks, backlink suggestions, "
            "knowledge_read, preflight with read-only readiness, validation_available, blocked "
            "reasons, validation intent, and writes=[]. capability_level describes scan/write "
            "transport only."
        )

    @server.prompt(name="cobsidian-organize-after-confirmation")
    def organize_after_confirmation_prompt(vault: str, topic: str, material: str) -> str:
        return (
            "Use the confirmed Cobsidian dry-run plan through an active host with separately "
            "approved filesystem write capability. This MCP server remains read-only and cannot "
            "perform the write. "
            f"Vault: {vault}\n"
            f"Topic: {topic}\n\n"
            f"Material:\n{material}\n\n"
            "The active host must search existing notes first, avoid duplicates, add useful wiki "
            "links, validate external changes, and report the files it actually changed."
        )

    return server


def main() -> None:
    create_mcp_server().run(transport="stdio")


if __name__ == "__main__":
    main()
