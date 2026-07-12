from __future__ import annotations

import unittest
from pathlib import Path

from skills.cobsidian.scripts.cobsidian_config import CobsidianConfig
from skills.cobsidian.scripts.quality_eval import parse_cases, run_quality_eval


REPO_ROOT = Path(__file__).resolve().parents[1]
EVALS_DIR = REPO_ROOT / "evals"


class QualityEvalTests(unittest.TestCase):
    def test_public_dataset_has_unique_valid_cases(self) -> None:
        cases = parse_cases(EVALS_DIR / "public-smoke.jsonl")

        self.assertGreaterEqual(len(cases), 4)
        self.assertEqual(len(cases), len({case.case_id for case in cases}))

    def test_public_smoke_eval_measures_all_quality_metrics(self) -> None:
        payload = run_quality_eval(
            EVALS_DIR / "public-smoke.jsonl",
            EVALS_DIR / "fixtures" / "public-vault",
            CobsidianConfig(config_path=None, raw={}),
            EVALS_DIR / "public-mode-predictions.jsonl",
        )

        metrics = payload["metrics"]
        self.assertEqual(1.0, metrics["duplicate_precision"])
        self.assertEqual(1.0, metrics["duplicate_recall"])
        self.assertEqual(1.0, metrics["append_target_accuracy"])
        self.assertGreater(metrics["backlink_precision_at_3"], 0)
        self.assertEqual(1.0, metrics["mode_accuracy"])

    def test_mode_accuracy_is_not_claimed_without_host_predictions(self) -> None:
        payload = run_quality_eval(
            EVALS_DIR / "public-smoke.jsonl",
            EVALS_DIR / "fixtures" / "public-vault",
            CobsidianConfig(config_path=None, raw={}),
        )

        self.assertIsNone(payload["metrics"]["mode_accuracy"])
        self.assertEqual(0, payload["counts"]["mode_cases_evaluated"])


if __name__ == "__main__":
    unittest.main()
