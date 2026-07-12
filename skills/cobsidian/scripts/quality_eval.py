from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from cobsidian_config import load_config, resolve_vault_path
    from dry_run import choose_decision
    from retrieval import build_query, build_search_documents, rank_backlinks
    from scan_vault import scan_vault
except ModuleNotFoundError:
    from .cobsidian_config import load_config, resolve_vault_path
    from .dry_run import choose_decision
    from .retrieval import build_query, build_search_documents, rank_backlinks
    from .scan_vault import scan_vault


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    query: str
    material: str
    expected_action: str
    expected_target: str | None
    expected_backlinks: tuple[str, ...]
    expected_mode: str | None


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        try:
            row = json.loads(raw_line)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSONL at {path}:{line_number}: {error}") from error
        if not isinstance(row, dict):
            raise ValueError(f"Expected an object at {path}:{line_number}.")
        rows.append(row)
    return rows


def parse_cases(path: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    seen_ids: set[str] = set()
    for row in load_jsonl(path):
        case_id = str(row.get("id", "")).strip()
        query = str(row.get("query", "")).strip()
        expected_action = str(row.get("expected_action", "")).strip()
        if not case_id or case_id in seen_ids:
            raise ValueError(f"Eval case IDs must be non-empty and unique: {case_id!r}.")
        if not query:
            raise ValueError(f"Eval case {case_id!r} requires a query.")
        if expected_action not in {"create", "append"}:
            raise ValueError(
                f"Eval case {case_id!r} expected_action must be create or append."
            )
        expected_target = row.get("expected_target")
        if expected_target is not None:
            expected_target = str(expected_target).strip() or None
        raw_backlinks = row.get("expected_backlinks", [])
        if not isinstance(raw_backlinks, list):
            raise ValueError(f"Eval case {case_id!r} expected_backlinks must be a list.")
        cases.append(
            EvalCase(
                case_id=case_id,
                query=query,
                material=str(row.get("material", "")),
                expected_action=expected_action,
                expected_target=expected_target,
                expected_backlinks=tuple(str(item) for item in raw_backlinks),
                expected_mode=(
                    str(row["expected_mode"]).strip()
                    if row.get("expected_mode") is not None
                    else None
                ),
            )
        )
        seen_ids.add(case_id)
    if not cases:
        raise ValueError("The eval dataset contains no cases.")
    return cases


def load_mode_predictions(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    predictions: dict[str, str] = {}
    for row in load_jsonl(path):
        case_id = str(row.get("id", "")).strip()
        mode = str(row.get("mode", "")).strip()
        if not case_id or not mode:
            raise ValueError("Mode predictions require non-empty id and mode fields.")
        predictions[case_id] = mode
    return predictions


def safe_ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 4) if denominator else None


def run_quality_eval(
    dataset_path: Path,
    vault_path: Path,
    config: Any,
    mode_predictions_path: Path | None = None,
    backlink_k: int = 3,
) -> dict[str, Any]:
    if backlink_k < 1:
        raise ValueError("backlink_k must be positive.")
    cases = parse_cases(dataset_path)
    mode_predictions = load_mode_predictions(mode_predictions_path)
    notes = scan_vault(vault_path)

    true_positive = false_positive = false_negative = 0
    append_target_correct = append_target_total = 0
    backlink_precision_values: list[float] = []
    mode_correct = mode_total = 0
    results: list[dict[str, Any]] = []

    for case in cases:
        decision = choose_decision(case.query, None, notes, config)
        expected_duplicate = case.expected_action == "append"
        predicted_duplicate = decision["action"] == "append"
        if expected_duplicate and predicted_duplicate:
            true_positive += 1
        elif not expected_duplicate and predicted_duplicate:
            false_positive += 1
        elif expected_duplicate and not predicted_duplicate:
            false_negative += 1

        if expected_duplicate and case.expected_target:
            append_target_total += 1
            if decision["target_note"] == case.expected_target:
                append_target_correct += 1

        excluded_paths = (
            {decision["target_note"]}
            if decision["action"] == "append"
            else set()
        )
        backlinks = rank_backlinks(
            build_query(case.query, case.material),
            build_search_documents(vault_path, notes),
            limit=backlink_k,
            excluded_paths=excluded_paths,
        )
        predicted_backlinks = [item.path for item in backlinks]
        backlink_precision: float | None = None
        if case.expected_backlinks:
            expected_backlinks = set(case.expected_backlinks)
            backlink_precision = round(
                len(set(predicted_backlinks[:backlink_k]) & expected_backlinks) / backlink_k,
                4,
            )
            backlink_precision_values.append(backlink_precision)

        predicted_mode = mode_predictions.get(case.case_id)
        mode_match: bool | None = None
        if case.expected_mode is not None and predicted_mode is not None:
            mode_total += 1
            mode_match = predicted_mode == case.expected_mode
            mode_correct += int(mode_match)

        results.append(
            {
                "id": case.case_id,
                "query": case.query,
                "expected_action": case.expected_action,
                "predicted_action": decision["action"],
                "expected_target": case.expected_target,
                "predicted_target": decision["target_note"],
                "predicted_backlinks": predicted_backlinks,
                "backlink_precision_at_k": backlink_precision,
                "expected_mode": case.expected_mode,
                "predicted_mode": predicted_mode,
                "mode_match": mode_match,
            }
        )

    duplicate_precision = safe_ratio(true_positive, true_positive + false_positive)
    duplicate_recall = safe_ratio(true_positive, true_positive + false_negative)
    return {
        "dataset": str(dataset_path),
        "vault": str(vault_path),
        "case_count": len(cases),
        "metrics": {
            "duplicate_precision": duplicate_precision,
            "duplicate_recall": duplicate_recall,
            "append_target_accuracy": safe_ratio(
                append_target_correct,
                append_target_total,
            ),
            f"backlink_precision_at_{backlink_k}": (
                round(sum(backlink_precision_values) / len(backlink_precision_values), 4)
                if backlink_precision_values
                else None
            ),
            "mode_accuracy": safe_ratio(mode_correct, mode_total),
        },
        "counts": {
            "duplicate_true_positive": true_positive,
            "duplicate_false_positive": false_positive,
            "duplicate_false_negative": false_negative,
            "append_target_evaluated": append_target_total,
            "backlink_cases_evaluated": len(backlink_precision_values),
            "mode_cases_evaluated": mode_total,
        },
        "results": results,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate Cobsidian duplicate, backlink, and mode quality."
    )
    parser.add_argument("dataset", type=Path, help="JSONL eval dataset.")
    parser.add_argument("vault", nargs="?", type=Path)
    parser.add_argument("--config", type=Path, help="Path to cobsidian.config.yml.")
    parser.add_argument(
        "--mode-predictions",
        type=Path,
        help="Optional JSONL predictions with id and mode fields.",
    )
    parser.add_argument("--backlink-k", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_config(args.config)
    vault_path = resolve_vault_path(args.vault, config)
    if not vault_path.is_dir():
        raise SystemExit(f"Vault path does not exist or is not a directory: {vault_path}")
    try:
        payload = run_quality_eval(
            args.dataset.expanduser().resolve(),
            vault_path,
            config,
            mode_predictions_path=(
                args.mode_predictions.expanduser().resolve()
                if args.mode_predictions
                else None
            ),
            backlink_k=args.backlink_k,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Cases: {payload['case_count']}")
        for name, value in payload["metrics"].items():
            print(f"{name}: {value if value is not None else 'not evaluated'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
