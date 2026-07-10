from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path

from cobsidian_config import CobsidianConfig, load_config, resolve_vault_path
from knowledge_read import (
    DEPTHS,
    DISPLAY_POLICIES,
    EVIDENCE_LEVELS,
    GRANULARITIES,
    MODES,
    build_knowledge_read,
)
from preflight import CAPABILITY_LEVELS, build_preflight, validated_capability
from retrieval import build_query, build_search_documents, rank_backlinks
from scan_vault import NoteInfo, read_text, scan_vault


@dataclass(frozen=True)
class DuplicateRisk:
    title: str
    path: str
    score: float
    kind: str


def normalize_title(title: str) -> str:
    lowered = title.casefold()
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", lowered)


def safe_filename(title: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", title).strip(" .-")
    return cleaned or "Untitled"


def choose_target_path(topic: str, mode: str | None, config: CobsidianConfig) -> str:
    filename = f"{safe_filename(topic)}.md"
    directory = config.note_directory_for_mode(mode)
    return f"{directory}/{filename}" if directory else filename


def find_duplicate_risks(topic: str, notes: list[NoteInfo], threshold: float) -> list[DuplicateRisk]:
    normalized_topic = normalize_title(topic)
    risks: list[DuplicateRisk] = []
    for note in notes:
        normalized_title = normalize_title(note.title)
        if not normalized_title:
            continue
        if normalized_title == normalized_topic:
            risks.append(DuplicateRisk(title=note.title, path=note.path, score=1.0, kind="exact"))
            continue
        score = SequenceMatcher(None, normalized_topic, normalized_title).ratio()
        if score >= threshold:
            risks.append(DuplicateRisk(title=note.title, path=note.path, score=round(score, 4), kind="similar"))
    return sorted(risks, key=lambda risk: risk.score, reverse=True)


def choose_decision(topic: str, mode: str | None, notes: list[NoteInfo], config: CobsidianConfig) -> dict[str, str]:
    risks = find_duplicate_risks(topic, notes, config.similar_title_threshold)
    exact = next((risk for risk in risks if risk.kind == "exact"), None)
    if exact is not None:
        return {
            "action": "append",
            "target_note": exact.path,
            "reason": "A note with the same title already exists.",
        }

    if risks and config.prefer_append_over_duplicate:
        return {
            "action": "append",
            "target_note": risks[0].path,
            "reason": "A similar note exists and config prefers append over duplicate creation.",
        }

    return {
        "action": "create",
        "target_note": choose_target_path(topic, mode, config),
        "reason": "No exact or similar note exceeded the duplicate threshold.",
    }


def build_payload(
    vault_path: Path,
    config: CobsidianConfig,
    topic: str,
    mode: str | None,
    text: str,
    notes: list[NoteInfo],
    *,
    mode_explicit: bool = False,
    recommended_modes: list[str] | None = None,
    depth: str | None = None,
    granularity: str | None = None,
    evidence: str = "conversation",
    capability_level: str = "filesystem-only",
    knowledge_read_policy: str | None = None,
) -> dict[str, object]:
    normalized_topic = topic.strip()
    if not normalized_topic:
        raise ValueError("Provide a non-empty topic.")

    decision = choose_decision(normalized_topic, mode, notes, config)
    knowledge_read = build_knowledge_read(
        mode=mode,
        mode_explicit=mode_explicit,
        recommended_modes=recommended_modes,
        depth=depth,
        granularity=granularity,
        evidence=evidence,
        display_policy=knowledge_read_policy or config.knowledge_read_policy,
        decision_action=decision["action"],
    )
    capability = validated_capability(capability_level)
    risks = find_duplicate_risks(
        normalized_topic,
        notes,
        config.similar_title_threshold,
    )
    excluded_paths = (
        {decision["target_note"]}
        if decision["action"] == "append"
        else set()
    )
    backlinks = rank_backlinks(
        build_query(topic=normalized_topic, text=text),
        build_search_documents(vault_path, notes),
        limit=config.max_suggested_backlinks,
        excluded_paths=excluded_paths,
    )
    preflight = build_preflight(
        capability_level=capability_level,
        vault_resolved=True,
        existing_notes_scanned=capability.scan,
        duplicate_check_completed=capability.scan,
        backlink_check_completed=capability.scan,
        mode_selected=knowledge_read.mode is not None,
    )
    return {
        "dry_run": True,
        "vault": str(vault_path),
        "config": config.public_summary() if config.config_path else None,
        "mode": mode,
        "topic": normalized_topic,
        "decision": decision,
        "duplicate_risks": [asdict(risk) for risk in risks],
        "suggested_backlinks": [asdict(suggestion) for suggestion in backlinks],
        "validation": {
            "would_run": config.validation_run_after_write,
            "strict": config.validation_strict,
        },
        "knowledge_read": knowledge_read.to_payload(),
        "preflight": preflight.to_payload(),
        "writes": [],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plan a Cobsidian note write without modifying files.")
    parser.add_argument("vault", nargs="?", type=Path)
    parser.add_argument("--config", type=Path, help="Path to cobsidian.config.yml.")
    parser.add_argument("--topic", required=True, help="Target note topic or title.")
    parser.add_argument("--mode", choices=MODES, help="Override mode from config.")
    parser.add_argument(
        "--mode-explicit",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Mark mode selection as explicit or inferred.",
    )
    parser.add_argument(
        "--recommended-mode",
        action="append",
        choices=MODES,
        help="Recommend a mode when the primary mode is unresolved; repeat at most twice.",
    )
    parser.add_argument("--depth", choices=DEPTHS)
    parser.add_argument("--granularity", choices=GRANULARITIES)
    parser.add_argument("--evidence", choices=EVIDENCE_LEVELS, default="conversation")
    parser.add_argument(
        "--capability-level",
        choices=CAPABILITY_LEVELS,
        default="filesystem-only",
    )
    parser.add_argument(
        "--knowledge-read",
        dest="knowledge_read_policy",
        choices=DISPLAY_POLICIES,
        help="Override the configured Knowledge Read display policy for this request.",
    )
    parser.add_argument("--file", type=Path, help="Source text file.")
    parser.add_argument("--text", help="Source text.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    config = load_config(args.config)
    vault_path = resolve_vault_path(args.vault, config)
    if not vault_path.exists() or not vault_path.is_dir():
        raise SystemExit(f"Vault path does not exist or is not a directory: {vault_path}")

    source_text = (
        read_text(args.file.expanduser().resolve())
        if args.file
        else str(args.text or "")
    )
    mode = args.mode if args.mode is not None else config.mode
    mode_explicit = (
        args.mode_explicit
        if args.mode_explicit is not None
        else args.mode is not None
    )
    notes = scan_vault(vault_path)
    try:
        payload = build_payload(
            vault_path=vault_path,
            config=config,
            topic=args.topic,
            mode=mode,
            text=source_text,
            notes=notes,
            mode_explicit=mode_explicit,
            recommended_modes=args.recommended_mode,
            depth=args.depth,
            granularity=args.granularity,
            evidence=args.evidence,
            capability_level=args.capability_level,
            knowledge_read_policy=args.knowledge_read_policy,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Dry run: {args.topic}")
        print(f"Mode: {payload['mode'] or 'infer'}")
        print(f"Decision: {payload['decision']['action']} -> {payload['decision']['target_note']}")
        print("Writes: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
