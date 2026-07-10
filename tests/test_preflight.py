from __future__ import annotations

import inspect
import unittest
from dataclasses import FrozenInstanceError, fields

from skills.cobsidian.scripts.preflight import (
    CAPABILITY_FLAGS,
    Preflight,
    build_preflight,
)


class PreflightTests(unittest.TestCase):
    def test_capability_flags_match_the_host_contract(self) -> None:
        self.assertEqual(
            {
                "full-local": {"scan": True, "write": True},
                "filesystem-only": {"scan": True, "write": True},
                "mcp-readonly": {"scan": True, "write": False},
                "chat-only": {"scan": False, "write": False},
            },
            CAPABILITY_FLAGS,
        )

    def test_build_preflight_signature_uses_safe_defaults(self) -> None:
        parameters = inspect.signature(build_preflight).parameters

        self.assertIs(inspect.Parameter.empty, parameters["capability_level"].default)
        for name in (
            "vault_resolved",
            "existing_notes_scanned",
            "duplicate_check_completed",
            "backlink_check_completed",
            "mode_selected",
        ):
            with self.subTest(name=name):
                self.assertIs(True, parameters[name].default)
        self.assertEqual("dry-run", parameters["write_policy"].default)

    def test_local_capabilities_are_ready_after_all_checks(self) -> None:
        for capability in ("full-local", "filesystem-only"):
            with self.subTest(capability=capability):
                result = build_preflight(capability_level=capability)

                self.assertTrue(result.ready)
                self.assertEqual((), result.blocked_reasons)
                self.assertEqual([], result.to_payload()["blocked_reasons"])

    def test_read_only_and_chat_hosts_are_not_write_ready(self) -> None:
        mcp = build_preflight(capability_level="mcp-readonly")
        chat = build_preflight(capability_level="chat-only")

        self.assertFalse(mcp.ready)
        self.assertEqual(
            ("write_capability_unavailable",),
            mcp.blocked_reasons,
        )
        self.assertFalse(chat.ready)
        self.assertEqual(
            (
                "scan_capability_unavailable",
                "write_capability_unavailable",
            ),
            chat.blocked_reasons,
        )

    def test_missing_checks_and_mode_are_reported_deterministically(self) -> None:
        result = build_preflight(
            capability_level="filesystem-only",
            vault_resolved=False,
            existing_notes_scanned=False,
            duplicate_check_completed=False,
            backlink_check_completed=False,
            mode_selected=False,
        )

        self.assertEqual(
            (
                "vault_unresolved",
                "existing_notes_not_scanned",
                "duplicate_check_incomplete",
                "backlink_check_incomplete",
                "mode_unresolved",
            ),
            result.blocked_reasons,
        )

    def test_all_block_reasons_follow_the_contract_order(self) -> None:
        result = build_preflight(
            capability_level="chat-only",
            vault_resolved=False,
            existing_notes_scanned=False,
            duplicate_check_completed=False,
            backlink_check_completed=False,
            mode_selected=False,
        )

        self.assertEqual(
            (
                "vault_unresolved",
                "scan_capability_unavailable",
                "existing_notes_not_scanned",
                "duplicate_check_incomplete",
                "backlink_check_incomplete",
                "mode_unresolved",
                "write_capability_unavailable",
            ),
            result.blocked_reasons,
        )

    def test_ready_exactly_matches_absence_of_blocked_reasons(self) -> None:
        results = (
            build_preflight(capability_level="full-local"),
            build_preflight(
                capability_level="filesystem-only",
                vault_resolved=False,
            ),
            build_preflight(capability_level="mcp-readonly"),
            build_preflight(capability_level="chat-only"),
        )

        for result in results:
            with self.subTest(capability=result.capability_level):
                self.assertEqual(not result.blocked_reasons, result.ready)

    def test_invalid_capability_level_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "capability_level"):
            build_preflight(capability_level="browser-only")

    def test_preflight_is_frozen_with_the_contract_fields(self) -> None:
        preflight = build_preflight(capability_level="mcp-readonly")

        self.assertEqual(
            (
                "vault_resolved",
                "existing_notes_scanned",
                "duplicate_check_completed",
                "backlink_check_completed",
                "mode_selected",
                "capability_level",
                "write_policy",
                "ready",
                "blocked_reasons",
            ),
            tuple(field.name for field in fields(Preflight)),
        )
        self.assertIsInstance(preflight.blocked_reasons, tuple)
        with self.assertRaises(FrozenInstanceError):
            setattr(preflight, "ready", True)

    def test_payload_uses_a_defensive_blocked_reasons_list(self) -> None:
        preflight = build_preflight(capability_level="mcp-readonly")
        payload = preflight.to_payload()

        self.assertEqual(
            {
                "vault_resolved": True,
                "existing_notes_scanned": True,
                "duplicate_check_completed": True,
                "backlink_check_completed": True,
                "mode_selected": True,
                "capability_level": "mcp-readonly",
                "write_policy": "dry-run",
                "ready": False,
                "blocked_reasons": ["write_capability_unavailable"],
            },
            payload,
        )
        blocked_reasons = payload["blocked_reasons"]
        self.assertIsInstance(blocked_reasons, list)
        assert isinstance(blocked_reasons, list)
        blocked_reasons.append("tampered")

        self.assertEqual(
            ("write_capability_unavailable",),
            preflight.blocked_reasons,
        )
        self.assertEqual(
            ["write_capability_unavailable"],
            preflight.to_payload()["blocked_reasons"],
        )


if __name__ == "__main__":
    unittest.main()
