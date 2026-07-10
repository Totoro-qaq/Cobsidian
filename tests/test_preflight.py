from __future__ import annotations

import inspect
import operator
import unittest
from dataclasses import FrozenInstanceError, fields
from types import MappingProxyType

from skills.cobsidian.scripts.preflight import (
    CAPABILITY_FLAGS,
    Preflight,
    build_preflight,
)


def build_completed_preflight(capability_level: str) -> Preflight:
    return build_preflight(
        capability_level=capability_level,
        vault_resolved=True,
        existing_notes_scanned=True,
        duplicate_check_completed=True,
        backlink_check_completed=True,
        mode_selected=True,
    )


class PreflightTests(unittest.TestCase):
    def test_capability_flags_match_the_host_contract(self) -> None:
        expected = {
            "full-local": (True, True, True),
            "filesystem-only": (True, True, True),
            "mcp-readonly": (True, False, True),
            "chat-only": (False, False, False),
        }

        self.assertEqual(tuple(expected), tuple(CAPABILITY_FLAGS))
        for capability_level, (scan, write, validation) in expected.items():
            with self.subTest(capability_level=capability_level):
                capability = CAPABILITY_FLAGS[capability_level]
                self.assertIs(scan, capability.scan)
                self.assertIs(write, capability.write)
                self.assertIs(validation, capability.validation)

    def test_capability_flags_are_immutable_at_both_levels(self) -> None:
        self.assertIsInstance(CAPABILITY_FLAGS, MappingProxyType)
        full_local = CAPABILITY_FLAGS["full-local"]

        with self.assertRaises(TypeError):
            operator.setitem(CAPABILITY_FLAGS, "full-local", full_local)
        with self.assertRaises(FrozenInstanceError):
            setattr(full_local, "scan", False)

    def test_build_preflight_signature_is_fail_closed(self) -> None:
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
                self.assertIs(False, parameters[name].default)
        self.assertIsNone(parameters["validation_available"].default)
        self.assertEqual("dry-run", parameters["write_policy"].default)

    def test_defaults_report_uncompleted_evidence_and_are_not_ready(self) -> None:
        result = build_preflight(capability_level="full-local")

        self.assertFalse(result.vault_resolved)
        self.assertFalse(result.existing_notes_scanned)
        self.assertFalse(result.duplicate_check_completed)
        self.assertFalse(result.backlink_check_completed)
        self.assertFalse(result.mode_selected)
        self.assertTrue(result.validation_available)
        self.assertFalse(result.ready)
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

    def test_local_capabilities_require_explicit_completed_checks(self) -> None:
        for capability_level in ("full-local", "filesystem-only"):
            with self.subTest(capability_level=capability_level):
                result = build_completed_preflight(capability_level)

                self.assertTrue(result.ready)
                self.assertTrue(result.validation_available)
                self.assertEqual((), result.blocked_reasons)
                self.assertEqual([], result.to_payload()["blocked_reasons"])

    def test_read_only_and_chat_hosts_are_not_write_ready(self) -> None:
        mcp = build_completed_preflight("mcp-readonly")
        chat = build_preflight(capability_level="chat-only")

        self.assertFalse(mcp.ready)
        self.assertTrue(mcp.validation_available)
        self.assertEqual(
            ("write_capability_unavailable",),
            mcp.blocked_reasons,
        )
        self.assertFalse(chat.ready)
        self.assertIn("scan_capability_unavailable", chat.blocked_reasons)
        self.assertIn("write_capability_unavailable", chat.blocked_reasons)
        self.assertFalse(chat.validation_available)
        self.assertIn(
            "validation_capability_unavailable",
            chat.blocked_reasons,
        )

    def test_validation_unavailable_blocks_write_capable_host(self) -> None:
        result = build_preflight(
            capability_level="filesystem-only",
            vault_resolved=True,
            existing_notes_scanned=True,
            duplicate_check_completed=True,
            backlink_check_completed=True,
            mode_selected=True,
            validation_available=False,
        )

        self.assertFalse(result.ready)
        self.assertFalse(result.validation_available)
        self.assertEqual(
            ("validation_capability_unavailable",),
            result.blocked_reasons,
        )
        self.assertNotIn("write_capability_unavailable", result.blocked_reasons)

    def test_validation_override_requires_bool_and_scan_capability(self) -> None:
        for invalid_value in (1, "true", [], object()):
            with self.subTest(invalid_value=invalid_value):
                with self.assertRaisesRegex(
                    ValueError,
                    "validation_available must be a bool",
                ):
                    build_preflight(
                        capability_level="filesystem-only",
                        validation_available=invalid_value,
                    )

        with self.assertRaisesRegex(ValueError, "validation capability"):
            build_preflight(
                capability_level="chat-only",
                validation_available=True,
            )

    def test_all_block_reasons_follow_the_contract_order(self) -> None:
        result = build_preflight(capability_level="chat-only")

        self.assertEqual(
            (
                "vault_unresolved",
                "scan_capability_unavailable",
                "existing_notes_not_scanned",
                "duplicate_check_incomplete",
                "backlink_check_incomplete",
                "mode_unresolved",
                "write_capability_unavailable",
                "validation_capability_unavailable",
            ),
            result.blocked_reasons,
        )

    def test_ready_exactly_matches_absence_of_blocked_reasons(self) -> None:
        results = (
            build_completed_preflight("full-local"),
            build_preflight(capability_level="filesystem-only"),
            build_completed_preflight("mcp-readonly"),
            build_preflight(capability_level="chat-only"),
        )

        for result in results:
            with self.subTest(capability=result.capability_level):
                self.assertEqual(not result.blocked_reasons, result.ready)

    def test_invalid_capability_level_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "capability_level"):
            build_preflight(capability_level="browser-only")

    def test_invalid_write_policy_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "write_policy"):
            build_preflight(
                capability_level="full-local",
                write_policy="write-now",
            )
        with self.assertRaisesRegex(ValueError, "write_policy"):
            Preflight(
                vault_resolved=False,
                existing_notes_scanned=False,
                duplicate_check_completed=False,
                backlink_check_completed=False,
                mode_selected=False,
                validation_available=True,
                capability_level="full-local",
                write_policy="write-now",
            )

    def test_evidence_fields_require_actual_bool_values(self) -> None:
        evidence_fields = (
            "vault_resolved",
            "existing_notes_scanned",
            "duplicate_check_completed",
            "backlink_check_completed",
            "mode_selected",
        )
        invalid_values = (
            "true",
            "",
            1,
            0,
            None,
            [],
            [1],
            object(),
        )
        valid_evidence: dict[str, object] = {
            field_name: True for field_name in evidence_fields
        }

        for field_name in evidence_fields:
            for invalid_value in invalid_values:
                evidence = {**valid_evidence, field_name: invalid_value}
                with self.subTest(
                    constructor="builder",
                    field_name=field_name,
                    invalid_value=invalid_value,
                ):
                    with self.assertRaisesRegex(
                        ValueError,
                        f"{field_name} must be a bool",
                    ):
                        build_preflight(
                            capability_level="full-local",
                            **evidence,
                        )
                with self.subTest(
                    constructor="direct",
                    field_name=field_name,
                    invalid_value=invalid_value,
                ):
                    with self.assertRaisesRegex(
                        ValueError,
                        f"{field_name} must be a bool",
                    ):
                        Preflight(
                            capability_level="full-local",
                            write_policy="dry-run",
                            validation_available=True,
                            **evidence,
                        )

    def test_existing_note_scan_requires_a_resolved_vault(self) -> None:
        evidence = {
            "vault_resolved": False,
            "existing_notes_scanned": True,
            "duplicate_check_completed": False,
            "backlink_check_completed": False,
            "mode_selected": False,
        }

        with self.assertRaisesRegex(ValueError, "vault_resolved"):
            build_preflight(
                capability_level="full-local",
                **evidence,
            )
        with self.assertRaisesRegex(ValueError, "vault_resolved"):
            Preflight(
                capability_level="full-local",
                write_policy="dry-run",
                validation_available=True,
                **evidence,
            )

    def test_scanless_capability_cannot_claim_scan_dependent_checks(self) -> None:
        for completed_check in (
            "existing_notes_scanned",
            "duplicate_check_completed",
            "backlink_check_completed",
        ):
            values = {
                "existing_notes_scanned": False,
                "duplicate_check_completed": False,
                "backlink_check_completed": False,
                completed_check: True,
            }
            with self.subTest(completed_check=completed_check):
                with self.assertRaisesRegex(ValueError, "scan capability"):
                    build_preflight(
                        capability_level="chat-only",
                        **values,
                    )

    def test_duplicate_and_backlink_checks_require_an_existing_note_scan(self) -> None:
        for completed_check in (
            "duplicate_check_completed",
            "backlink_check_completed",
        ):
            values = {
                "duplicate_check_completed": False,
                "backlink_check_completed": False,
                completed_check: True,
            }
            with self.subTest(completed_check=completed_check):
                with self.assertRaisesRegex(ValueError, "existing_notes_scanned"):
                    build_preflight(
                        capability_level="full-local",
                        existing_notes_scanned=False,
                        **values,
                    )

    def test_direct_construction_enforces_evidence_dependencies(self) -> None:
        with self.assertRaisesRegex(ValueError, "existing_notes_scanned"):
            Preflight(
                vault_resolved=True,
                existing_notes_scanned=False,
                duplicate_check_completed=True,
                backlink_check_completed=False,
                mode_selected=True,
                validation_available=True,
                capability_level="full-local",
                write_policy="dry-run",
            )

    def test_direct_constructor_derives_and_cannot_forge_readiness(self) -> None:
        constructor_values = {
            "vault_resolved": True,
            "existing_notes_scanned": True,
            "duplicate_check_completed": True,
            "backlink_check_completed": True,
            "mode_selected": True,
            "validation_available": True,
            "capability_level": "full-local",
            "write_policy": "dry-run",
        }
        preflight = Preflight(**constructor_values)

        self.assertTrue(preflight.ready)
        self.assertEqual((), preflight.blocked_reasons)
        with self.assertRaises(TypeError):
            Preflight(
                **constructor_values,
                ready=True,
                blocked_reasons=(),
            )

    def test_preflight_is_frozen_with_derived_contract_fields(self) -> None:
        preflight = build_completed_preflight("mcp-readonly")
        contract_fields = fields(Preflight)

        self.assertEqual(
            (
                "vault_resolved",
                "existing_notes_scanned",
                "duplicate_check_completed",
                "backlink_check_completed",
                "mode_selected",
                "validation_available",
                "capability_level",
                "write_policy",
                "ready",
                "blocked_reasons",
            ),
            tuple(field.name for field in contract_fields),
        )
        field_by_name = {field.name: field for field in contract_fields}
        self.assertFalse(field_by_name["ready"].init)
        self.assertFalse(field_by_name["blocked_reasons"].init)
        self.assertIsInstance(preflight.blocked_reasons, tuple)
        with self.assertRaises(FrozenInstanceError):
            setattr(preflight, "ready", True)

    def test_payload_uses_a_defensive_blocked_reasons_list(self) -> None:
        preflight = build_completed_preflight("mcp-readonly")
        payload = preflight.to_payload()

        self.assertEqual(
            {
                "vault_resolved": True,
                "existing_notes_scanned": True,
                "duplicate_check_completed": True,
                "backlink_check_completed": True,
                "mode_selected": True,
                "validation_available": True,
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
