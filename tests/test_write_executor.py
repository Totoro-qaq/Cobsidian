from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from skills.cobsidian.scripts.scan_vault import scan_vault
from skills.cobsidian.scripts.write_executor import (
    apply_write_plan,
    build_write_plan,
    ensure_relative_path_inside_vault,
    rollback_transaction,
)


class WriteExecutorTests(unittest.TestCase):
    def test_prepare_returns_diff_and_does_not_write_note(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)

            plan = build_write_plan(vault, "create", "RAG.md", "# RAG\n")

            self.assertFalse((vault / "RAG.md").exists())
            self.assertIn("+++ b/RAG.md", plan["diff"])
            self.assertEqual("create", plan["action"])

    def test_apply_requires_exact_plan_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            plan = build_write_plan(vault, "create", "RAG.md", "# RAG\n")

            with self.assertRaisesRegex(ValueError, "confirmation"):
                apply_write_plan(vault, plan, "wrong-id")

            self.assertFalse((vault / "RAG.md").exists())

    def test_create_apply_and_rollback_are_verified(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            plan = build_write_plan(vault, "create", "RAG.md", "# RAG\n\nRetrieval.\n")

            applied = apply_write_plan(vault, plan, plan["plan_id"])
            rolled_back = rollback_transaction(vault, plan["plan_id"], plan["plan_id"])

            self.assertEqual("applied", applied["status"])
            self.assertEqual("rolled-back", rolled_back["status"])
            self.assertFalse((vault / "RAG.md").exists())

    def test_append_apply_and_rollback_restore_exact_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            target = vault / "RAG.md"
            original = "# RAG\n\nExisting text.\n"
            target.write_text(original, encoding="utf-8")
            plan = build_write_plan(vault, "append", "RAG.md", "## New\n\nMore text.")

            apply_write_plan(vault, plan, plan["plan_id"])
            self.assertIn("## New", target.read_text(encoding="utf-8"))
            rollback_transaction(vault, plan["plan_id"], plan["plan_id"])

            self.assertEqual(original, target.read_text(encoding="utf-8"))

    def test_stale_plan_is_rejected_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            target = vault / "RAG.md"
            target.write_text("# RAG\n", encoding="utf-8")
            plan = build_write_plan(vault, "append", "RAG.md", "More")
            target.write_text("# RAG\n\nConcurrent change.\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "changed after preview"):
                apply_write_plan(vault, plan, plan["plan_id"])

            self.assertNotIn("More", target.read_text(encoding="utf-8"))

    def test_new_validation_warning_triggers_automatic_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            plan = build_write_plan(
                vault,
                "create",
                "Broken.md",
                "# Broken\n\n[[Missing Target]]\n",
            )

            result = apply_write_plan(vault, plan, plan["plan_id"])

            self.assertEqual("rolled-back-validation", result["status"])
            self.assertFalse((vault / "Broken.md").exists())
            self.assertTrue(result["new_warnings"])

    def test_existing_warning_is_baselined_and_does_not_block_clean_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            (vault / "Old.md").write_text("# Old\n\n[[Already Missing]]\n", encoding="utf-8")
            plan = build_write_plan(vault, "create", "Good.md", "# Good\n\nClean.\n")

            result = apply_write_plan(vault, plan, plan["plan_id"])

            self.assertEqual("applied", result["status"])
            self.assertTrue((vault / "Good.md").exists())

    def test_transaction_state_is_not_scanned_as_vault_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            plan = build_write_plan(vault, "create", "Good.md", "# Good\n")
            apply_write_plan(vault, plan, plan["plan_id"])

            self.assertEqual(["Good.md"], [note.path for note in scan_vault(vault)])

    def test_target_must_stay_inside_vault(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError, "escapes"):
                ensure_relative_path_inside_vault(Path(temp_dir), "../outside.md")


if __name__ == "__main__":
    unittest.main()
