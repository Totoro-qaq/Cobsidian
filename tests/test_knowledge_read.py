from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError, fields

from skills.cobsidian.scripts.knowledge_read import (
    MODE_DEFAULTS,
    MODES,
    KnowledgeRead,
    build_knowledge_read,
)


class KnowledgeReadTests(unittest.TestCase):
    def test_each_mode_uses_approved_defaults(self) -> None:
        expected = {
            "learning": ("standard", "single-note"),
            "project": ("deep", "single-note"),
            "review": ("deep", "single-note"),
            "comparison": ("standard", "single-note"),
            "index": ("deep", "multi-note"),
            "capture": ("capture", "single-note"),
            "dissection": ("deep", "multi-note"),
        }

        self.assertEqual(tuple(expected), MODES)
        self.assertEqual(expected, MODE_DEFAULTS)
        for mode, (depth, granularity) in expected.items():
            with self.subTest(mode=mode):
                knowledge_read = build_knowledge_read(
                    mode=mode,
                    mode_explicit=True,
                )
                self.assertEqual(depth, knowledge_read.depth)
                self.assertEqual(granularity, knowledge_read.granularity)

    def test_unresolved_mode_uses_standard_single_note_defaults(self) -> None:
        knowledge_read = build_knowledge_read(mode=None, mode_explicit=False)

        self.assertEqual("standard", knowledge_read.depth)
        self.assertEqual("single-note", knowledge_read.granularity)

    def test_evidence_defaults_to_conversation(self) -> None:
        knowledge_read = build_knowledge_read(
            mode="learning",
            mode_explicit=True,
        )

        self.assertEqual("conversation", knowledge_read.evidence)

    def test_auto_display_expands_each_complex_condition(self) -> None:
        cases = {
            "inferred": {"mode": "learning", "mode_explicit": False},
            "deep": {"mode": "project", "mode_explicit": True},
            "multi-note": {
                "mode": "learning",
                "mode_explicit": True,
                "granularity": "multi-note",
            },
            "source-grounded": {
                "mode": "learning",
                "mode_explicit": True,
                "evidence": "source-grounded",
                "source_read_completed": True,
            },
            "verified": {
                "mode": "learning",
                "mode_explicit": True,
                "evidence": "verified",
                "source_read_completed": True,
                "verification_completed": True,
            },
        }

        for condition, values in cases.items():
            with self.subTest(condition=condition):
                self.assertEqual(
                    "expanded",
                    build_knowledge_read(**values).display_style,
                )

    def test_auto_display_is_compact_for_simple_explicit_work(self) -> None:
        knowledge_read = build_knowledge_read(
            mode="learning",
            mode_explicit=True,
        )

        self.assertEqual("compact", knowledge_read.display_style)

    def test_evidence_requires_completed_host_actions(self) -> None:
        invalid_cases = (
            {"evidence": "source-grounded"},
            {"evidence": "verified"},
            {"evidence": "verified", "source_read_completed": True},
            {"evidence": "verified", "verification_completed": True},
        )

        for arguments in invalid_cases:
            with self.subTest(arguments=arguments):
                with self.assertRaisesRegex(ValueError, "completed"):
                    build_knowledge_read(
                        mode="learning",
                        mode_explicit=True,
                        **arguments,
                    )

        verified = build_knowledge_read(
            mode="learning",
            mode_explicit=True,
            evidence="verified",
            source_read_completed=True,
            verification_completed=True,
        )
        self.assertEqual("verified", verified.evidence)

    def test_evidence_completion_facts_require_actual_bool_values(self) -> None:
        for field_name in ("source_read_completed", "verification_completed"):
            for invalid_value in (1, "true", None):
                with self.subTest(field_name=field_name, value=invalid_value):
                    with self.assertRaisesRegex(ValueError, field_name):
                        build_knowledge_read(
                            mode="learning",
                            mode_explicit=True,
                            **{field_name: invalid_value},
                        )

    def test_completion_facts_do_not_change_the_eight_field_payload(self) -> None:
        knowledge_read = build_knowledge_read(
            mode="learning",
            mode_explicit=True,
            source_read_completed=True,
            verification_completed=True,
        )

        self.assertEqual("conversation", knowledge_read.evidence)
        self.assertNotIn("source_read_completed", knowledge_read.to_payload())
        self.assertNotIn("verification_completed", knowledge_read.to_payload())

    def test_always_and_off_control_display_only(self) -> None:
        always = build_knowledge_read(
            mode="capture",
            mode_explicit=True,
            display_policy="always",
        )
        hidden = build_knowledge_read(
            mode="dissection",
            mode_explicit=False,
            display_policy="off",
        )

        self.assertEqual("expanded", always.display_style)
        self.assertEqual("hidden", hidden.display_style)
        self.assertEqual(
            {
                "mode": "dissection",
                "mode_explicit": False,
                "recommended_modes": [],
                "depth": "deep",
                "granularity": "multi-note",
                "evidence": "conversation",
                "display_policy": "off",
                "display_style": "hidden",
            },
            hidden.to_payload(),
        )

    def test_append_decision_overrides_granularity(self) -> None:
        knowledge_read = build_knowledge_read(
            mode="index",
            mode_explicit=True,
            granularity="single-note",
            decision_action="append",
        )

        self.assertEqual("append", knowledge_read.granularity)

    def test_append_decision_validates_requested_granularity_first(self) -> None:
        with self.assertRaisesRegex(ValueError, "granularity"):
            build_knowledge_read(
                mode="learning",
                mode_explicit=True,
                granularity="many",
                decision_action="append",
            )

    def test_append_granularity_requires_append_decision(self) -> None:
        for decision_action in (None, "create", "blocked"):
            with self.subTest(decision_action=decision_action):
                with self.assertRaisesRegex(ValueError, "append decision"):
                    build_knowledge_read(
                        mode="learning",
                        mode_explicit=True,
                        granularity="append",
                        decision_action=decision_action,
                    )

    def test_decision_action_accepts_only_domain_actions(self) -> None:
        for decision_action in ("merge", "", 1):
            with self.subTest(decision_action=decision_action):
                with self.assertRaisesRegex(ValueError, "decision_action"):
                    build_knowledge_read(
                        mode="learning",
                        mode_explicit=True,
                        decision_action=decision_action,
                    )

    def test_unresolved_mode_cannot_be_explicit(self) -> None:
        with self.assertRaisesRegex(ValueError, "mode_explicit"):
            build_knowledge_read(mode=None, mode_explicit=True)

    def test_mode_explicit_requires_an_actual_bool(self) -> None:
        for invalid_value in (1, "true", None):
            with self.subTest(value=invalid_value):
                with self.assertRaisesRegex(ValueError, "mode_explicit"):
                    build_knowledge_read(
                        mode="learning",
                        mode_explicit=invalid_value,
                    )

    def test_unresolved_mode_accepts_at_most_two_recommendations(self) -> None:
        knowledge_read = build_knowledge_read(
            mode=None,
            mode_explicit=False,
            recommended_modes=["learning", "dissection"],
        )

        self.assertEqual(
            ["learning", "dissection"],
            knowledge_read.to_payload()["recommended_modes"],
        )
        self.assertIsInstance(
            knowledge_read.to_payload()["recommended_modes"],
            list,
        )
        with self.assertRaisesRegex(ValueError, "at most two"):
            build_knowledge_read(
                mode=None,
                mode_explicit=False,
                recommended_modes=["learning", "project", "review"],
            )

    def test_recommendations_require_unresolved_mode_and_valid_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "unresolved mode"):
            build_knowledge_read(
                mode="learning",
                mode_explicit=False,
                recommended_modes=["project"],
            )
        with self.assertRaisesRegex(ValueError, "recommended mode"):
            build_knowledge_read(
                mode=None,
                mode_explicit=False,
                recommended_modes=["unknown"],
            )

    def test_recommendations_require_an_ordered_sequence(self) -> None:
        invalid_recommendations = (
            {"learning"},
            iter(["learning"]),
        )

        for recommendations in invalid_recommendations:
            with self.subTest(recommendations=recommendations):
                with self.assertRaisesRegex(ValueError, "ordered sequence"):
                    build_knowledge_read(
                        mode=None,
                        mode_explicit=False,
                        recommended_modes=recommendations,
                    )

    def test_recommendations_reject_str_and_bytes(self) -> None:
        for recommendations in ("learning", b"learning"):
            with self.subTest(recommendations=recommendations):
                with self.assertRaisesRegex(ValueError, "ordered sequence"):
                    build_knowledge_read(
                        mode=None,
                        mode_explicit=False,
                        recommended_modes=recommendations,
                    )

    def test_recommendations_reject_duplicates(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate"):
            build_knowledge_read(
                mode=None,
                mode_explicit=False,
                recommended_modes=["learning", "learning"],
            )

    def test_invalid_enums_are_rejected(self) -> None:
        invalid_values = [
            {"mode": "unknown"},
            {"mode": "learning", "depth": "huge"},
            {"mode": "learning", "granularity": "many"},
            {"mode": "learning", "evidence": "trusted"},
            {"mode": "learning", "display_policy": "sometimes"},
        ]

        for values in invalid_values:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    build_knowledge_read(mode_explicit=True, **values)

    def test_knowledge_read_is_frozen_with_the_contract_fields(self) -> None:
        knowledge_read = build_knowledge_read(
            mode="learning",
            mode_explicit=True,
        )

        self.assertEqual(
            (
                "mode",
                "mode_explicit",
                "recommended_modes",
                "depth",
                "granularity",
                "evidence",
                "display_policy",
                "display_style",
            ),
            tuple(field.name for field in fields(KnowledgeRead)),
        )
        with self.assertRaises(FrozenInstanceError):
            setattr(knowledge_read, "mode", "project")


if __name__ == "__main__":
    unittest.main()
