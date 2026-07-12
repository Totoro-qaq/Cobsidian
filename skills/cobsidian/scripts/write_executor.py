from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

try:
    from cobsidian_config import load_config, resolve_vault_path
    from scan_vault import read_text
    from validate_notes import validate_vault
except ModuleNotFoundError:
    from .cobsidian_config import load_config, resolve_vault_path
    from .scan_vault import read_text
    from .validate_notes import validate_vault


SCHEMA_VERSION = 1
TRANSACTION_DIR = ".cobsidian/transactions"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def ensure_relative_path_inside_vault(vault_path: Path, relative_path: str) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute():
        raise ValueError("Target note path must be relative to the vault.")
    resolved_vault = vault_path.expanduser().resolve()
    resolved_target = (resolved_vault / candidate).resolve()
    try:
        resolved_target.relative_to(resolved_vault)
    except ValueError as error:
        raise ValueError("Target note path escapes the vault.") from error
    if resolved_target.suffix.casefold() != ".md":
        raise ValueError("Target note must use the .md extension.")
    relative_parts = resolved_target.relative_to(resolved_vault).parts
    if relative_parts[:2] == (".cobsidian", "transactions"):
        raise ValueError("Target note cannot be inside Cobsidian transaction state.")
    return resolved_target


def vault_fingerprint(vault_path: Path) -> str:
    return hashlib.sha256(str(vault_path.resolve()).encode("utf-8")).hexdigest()[:16]


def append_content(before_text: str, content: str) -> str:
    fragment = content.strip()
    if not fragment:
        raise ValueError("Write content must be non-empty.")
    prefix = before_text
    if prefix and not prefix.endswith("\n"):
        prefix += "\n"
    if prefix and not prefix.endswith("\n\n"):
        prefix += "\n"
    return f"{prefix}{fragment}\n"


def build_diff(relative_path: str, before_text: str, after_text: str) -> str:
    return "".join(
        difflib.unified_diff(
            before_text.splitlines(keepends=True),
            after_text.splitlines(keepends=True),
            fromfile=f"a/{relative_path}",
            tofile=f"b/{relative_path}",
        )
    )


def build_write_plan(
    vault_path: Path,
    action: str,
    target_note: str,
    content: str,
) -> dict[str, Any]:
    if action not in {"create", "append"}:
        raise ValueError("Write action must be create or append.")
    target_path = ensure_relative_path_inside_vault(vault_path, target_note)
    before_exists = target_path.exists()
    if action == "create" and before_exists:
        raise ValueError("Create target already exists; use append or choose another note.")
    if action == "append" and not before_exists:
        raise ValueError("Append target does not exist; use create or correct the target.")

    before_text = read_text(target_path) if before_exists else ""
    after_text = append_content(before_text, content) if action == "append" else append_content("", content)
    plan_core: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "vault_fingerprint": vault_fingerprint(vault_path),
        "action": action,
        "target_note": target_path.relative_to(vault_path.resolve()).as_posix(),
        "before_exists": before_exists,
        "before_sha256": sha256_text(before_text),
        "after_sha256": sha256_text(after_text),
        "after_text": after_text,
        "diff": build_diff(target_note, before_text, after_text),
    }
    plan_id = hashlib.sha256(canonical_json(plan_core).encode("utf-8")).hexdigest()[:20]
    return {"plan_id": plan_id, **plan_core}


def validate_plan(plan: dict[str, Any]) -> None:
    plan_id = str(plan.get("plan_id", ""))
    plan_core = {key: value for key, value in plan.items() if key != "plan_id"}
    expected_id = hashlib.sha256(canonical_json(plan_core).encode("utf-8")).hexdigest()[:20]
    if plan_id != expected_id:
        raise ValueError("Write plan integrity check failed.")
    if plan.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported write plan schema: {plan.get('schema_version')!r}.")
    if plan.get("action") not in {"create", "append"}:
        raise ValueError("Write plan action must be create or append.")
    if not isinstance(plan.get("after_text"), str) or not plan["after_text"].strip():
        raise ValueError("Write plan after_text must be non-empty.")
    if sha256_text(plan["after_text"]) != plan.get("after_sha256"):
        raise ValueError("Write plan after_text hash does not match after_sha256.")


def load_plan(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Unable to read write plan: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError("Write plan must be a JSON object.")
    validate_plan(payload)
    return payload


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def current_text_and_hash(target_path: Path) -> tuple[bool, str, str]:
    exists = target_path.exists()
    text = read_text(target_path) if exists else ""
    return exists, text, sha256_text(text)


def restore_before_state(
    target_path: Path,
    before_exists: bool,
    backup_path: Path,
) -> None:
    if before_exists:
        if not backup_path.is_file():
            raise ValueError("Transaction backup is missing; refusing partial rollback.")
        atomic_write_text(target_path, read_text(backup_path))
    elif target_path.exists():
        target_path.unlink()


def apply_write_plan(
    vault_path: Path,
    plan: dict[str, Any],
    confirmation: str,
    auto_rollback: bool = True,
) -> dict[str, Any]:
    validate_plan(plan)
    plan_id = plan["plan_id"]
    if confirmation != plan_id:
        raise ValueError("Explicit confirmation must exactly match the write plan ID.")
    if plan["vault_fingerprint"] != vault_fingerprint(vault_path):
        raise ValueError("Write plan was prepared for a different vault.")

    target_path = ensure_relative_path_inside_vault(vault_path, plan["target_note"])
    exists, before_text, before_sha256 = current_text_and_hash(target_path)
    if exists != plan["before_exists"] or before_sha256 != plan["before_sha256"]:
        raise ValueError("Target changed after preview; prepare a new write plan.")

    transaction_path = vault_path / TRANSACTION_DIR / plan_id
    manifest_path = transaction_path / "manifest.json"
    backup_path = transaction_path / "before.md"
    if manifest_path.exists():
        raise ValueError("This write plan already has a transaction record.")

    baseline_warnings = validate_vault(vault_path)
    transaction_path.mkdir(parents=True, exist_ok=False)
    atomic_write_json(transaction_path / "plan.json", plan)
    if exists:
        atomic_write_text(backup_path, before_text)

    atomic_write_text(target_path, plan["after_text"])
    written_text = read_text(target_path)
    if sha256_text(written_text) != plan["after_sha256"]:
        restore_before_state(target_path, exists, backup_path)
        raise ValueError("Atomic write verification failed and the previous state was restored.")

    after_warnings = validate_vault(vault_path)
    new_warnings = sorted(set(after_warnings) - set(baseline_warnings))
    status = "applied"
    if new_warnings and auto_rollback:
        restore_before_state(target_path, exists, backup_path)
        status = "rolled-back-validation"

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "plan_id": plan_id,
        "status": status,
        "target_note": plan["target_note"],
        "before_exists": exists,
        "before_sha256": plan["before_sha256"],
        "after_sha256": plan["after_sha256"],
        "backup": "before.md" if exists else None,
        "baseline_warning_count": len(baseline_warnings),
        "after_warning_count": len(after_warnings),
        "new_warnings": new_warnings,
    }
    atomic_write_json(manifest_path, manifest)
    return {
        "plan_id": plan_id,
        "status": status,
        "target_note": plan["target_note"],
        "transaction_manifest": str(manifest_path),
        "new_warnings": new_warnings,
        "writes": [plan["target_note"]] if status == "applied" else [],
    }


def rollback_transaction(
    vault_path: Path,
    transaction: str,
    confirmation: str,
) -> dict[str, Any]:
    plan_id = Path(transaction).name
    if confirmation != plan_id:
        raise ValueError("Explicit rollback confirmation must match the transaction ID.")
    transaction_path = vault_path / TRANSACTION_DIR / plan_id
    manifest_path = transaction_path / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("Transaction manifest does not exist.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "applied":
        raise ValueError(f"Transaction is not rollbackable from status {manifest.get('status')!r}.")

    target_path = ensure_relative_path_inside_vault(vault_path, manifest["target_note"])
    exists, _, current_sha256 = current_text_and_hash(target_path)
    if not exists or current_sha256 != manifest["after_sha256"]:
        raise ValueError("Target changed after apply; refusing to overwrite later edits.")

    backup_path = transaction_path / "before.md"
    restore_before_state(target_path, bool(manifest["before_exists"]), backup_path)
    restored_exists, _, restored_sha256 = current_text_and_hash(target_path)
    if restored_exists != bool(manifest["before_exists"]) or restored_sha256 != manifest["before_sha256"]:
        raise ValueError("Rollback verification failed.")

    manifest["status"] = "rolled-back"
    atomic_write_json(manifest_path, manifest)
    return {
        "plan_id": plan_id,
        "status": "rolled-back",
        "target_note": manifest["target_note"],
        "writes": [manifest["target_note"]],
    }


def add_vault_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("vault", nargs="?", type=Path)
    parser.add_argument("--config", type=Path, help="Path to cobsidian.config.yml.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare, confirm, atomically apply, validate, and roll back Cobsidian writes."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare")
    add_vault_arguments(prepare_parser)
    prepare_parser.add_argument("--action", choices=("create", "append"), required=True)
    prepare_parser.add_argument("--target-note", required=True)
    content_group = prepare_parser.add_mutually_exclusive_group(required=True)
    content_group.add_argument("--content")
    content_group.add_argument("--content-file", type=Path)
    prepare_parser.add_argument("--plan-out", type=Path, required=True)
    prepare_parser.add_argument("--json", action="store_true")

    apply_parser = subparsers.add_parser("apply")
    add_vault_arguments(apply_parser)
    apply_parser.add_argument("--plan", type=Path, required=True)
    apply_parser.add_argument("--confirm", required=True)
    apply_parser.add_argument("--no-auto-rollback", action="store_true")
    apply_parser.add_argument("--json", action="store_true")

    rollback_parser = subparsers.add_parser("rollback")
    add_vault_arguments(rollback_parser)
    rollback_parser.add_argument("--transaction", required=True)
    rollback_parser.add_argument("--confirm", required=True)
    rollback_parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_config(args.config)
    vault_path = resolve_vault_path(args.vault, config)
    if not vault_path.is_dir():
        raise SystemExit(f"Vault path does not exist or is not a directory: {vault_path}")

    try:
        if args.command == "prepare":
            content = (
                read_text(args.content_file.expanduser().resolve())
                if args.content_file
                else str(args.content)
            )
            payload = build_write_plan(
                vault_path,
                args.action,
                args.target_note,
                content,
            )
            atomic_write_json(args.plan_out.expanduser().resolve(), payload)
        elif args.command == "apply":
            payload = apply_write_plan(
                vault_path,
                load_plan(args.plan.expanduser().resolve()),
                args.confirm,
                auto_rollback=not args.no_auto_rollback,
            )
        else:
            payload = rollback_transaction(
                vault_path,
                args.transaction,
                args.confirm,
            )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(str(error)) from error

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.command == "prepare":
        print(payload["diff"], end="")
        print(f"\nConfirm with plan ID: {payload['plan_id']}")
    else:
        print(f"{payload['status']}: {payload['target_note']}")
    return 1 if payload.get("status") == "rolled-back-validation" else 0


if __name__ == "__main__":
    raise SystemExit(main())
