from __future__ import annotations

import argparse
from pathlib import Path

from cobsidian_config import load_config, resolve_vault_path
from duplicates import DEFAULT_MAX_COMPARISONS, find_title_duplicates
from scan_vault import scan_vault


def main() -> int:
    parser = argparse.ArgumentParser(description="Find duplicate or similar Obsidian note titles.")
    parser.add_argument("vault", nargs="?", type=Path)
    parser.add_argument("--config", type=Path, help="Path to cobsidian.config.yml.")
    parser.add_argument("--threshold", type=float, default=None, help="Similarity threshold from 0 to 1.")
    parser.add_argument(
        "--max-comparisons",
        type=int,
        default=DEFAULT_MAX_COMPARISONS,
        help="Maximum similar-title comparisons before reporting truncation.",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    vault_path = resolve_vault_path(args.vault, config)
    threshold = args.threshold if args.threshold is not None else config.similar_title_threshold
    if not vault_path.exists() or not vault_path.is_dir():
        raise SystemExit(f"Vault path does not exist or is not a directory: {vault_path}")

    report = find_title_duplicates(
        scan_vault(vault_path),
        threshold=threshold,
        max_comparisons=args.max_comparisons,
    )

    found = False
    print("Exact duplicate titles:")
    for group in report.exact_duplicates:
        found = True
        print("-")
        for note in group:
            print(f"  {note.title} :: {note.path}")

    print("\nSimilar titles:")
    for match in report.similar_titles:
        found = True
        print(
            f"- {match.score:.2f}: "
            f"{match.left.title} :: {match.left.path} <-> "
            f"{match.right.title} :: {match.right.path}"
        )

    if report.truncated:
        print(
            "\nSimilar-title search truncated after "
            f"{report.comparisons} comparisons."
        )

    if not found:
        suffix = " within the comparison limit" if report.truncated else ""
        print(f"No duplicate or highly similar titles found{suffix}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
