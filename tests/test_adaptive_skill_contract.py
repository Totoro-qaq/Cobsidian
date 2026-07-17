from __future__ import annotations

import re
import unittest
from pathlib import Path

from skills.cobsidian.scripts.knowledge_read import MODE_DEFAULTS


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = REPO_ROOT / "skills" / "cobsidian" / "SKILL.md"
REFERENCES_PATH = REPO_ROOT / "skills" / "cobsidian" / "references"
NOTE_TYPES_PATH = REFERENCES_PATH / "note-types.md"
MODE_NAMES = tuple(MODE_DEFAULTS)
HOST_NAMES = (
    "codex",
    "claude-code",
    "kimi-code",
    "opencode",
    "pi",
    "antigravity",
    "github-copilot-cli",
    "cursor",
    "hermes",
    "mcp",
)
MODE_HEADINGS = (
    "When to Use",
    "Required Inputs",
    "Default Knowledge Read",
    "Recommended Note Shape",
    "Append, Single-Note, and Split Criteria",
    "Evidence Rules",
    "Mode-Specific Validation",
    "Completion Report Additions",
)
HOST_HEADINGS = (
    "Detect Capabilities",
    "Capability Mapping",
    "Execution Path",
    "Degradation",
    "Safety",
)
CAPABILITY_LEVELS = (
    "full-local",
    "filesystem-only",
    "mcp-readonly",
    "chat-only",
)
BLOCKED_REASONS = (
    "vault_unresolved",
    "scan_capability_unavailable",
    "existing_notes_not_scanned",
    "duplicate_check_incomplete",
    "backlink_check_incomplete",
    "mode_unresolved",
    "write_capability_unavailable",
    "validation_capability_unavailable",
)


def h2_headings(text: str) -> tuple[str, ...]:
    return tuple(
        line.removeprefix("## ").strip()
        for line in text.splitlines()
        if line.startswith("## ")
    )


def h2_sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"^## (.+)$", text, flags=re.MULTILINE))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[match.group(1)] = text[match.end() : end].strip()
    return sections


class AdaptiveSkillContractTests(unittest.TestCase):
    def read_reference(self, path: Path) -> str:
        self.assertTrue(
            path.is_file(),
            f"missing reference: {path.relative_to(REPO_ROOT)}",
        )
        return path.read_text(encoding="utf-8")

    def test_all_progressive_reference_files_exist(self) -> None:
        expected_paths = [
            *(REFERENCES_PATH / "modes" / f"{mode}.md" for mode in MODE_NAMES),
            *(REFERENCES_PATH / "hosts" / f"{host}.md" for host in HOST_NAMES),
            REFERENCES_PATH / "preflight.md",
        ]

        missing = [str(path.relative_to(REPO_ROOT)) for path in expected_paths if not path.is_file()]
        self.assertEqual([], missing)

    def test_each_mode_has_exact_headings_defaults_and_concrete_decisions(self) -> None:
        for mode, (depth, granularity) in MODE_DEFAULTS.items():
            path = REFERENCES_PATH / "modes" / f"{mode}.md"
            with self.subTest(mode=mode):
                text = self.read_reference(path)
                self.assertEqual(MODE_HEADINGS, h2_headings(text))
                sections = h2_sections(text)
                for heading in MODE_HEADINGS:
                    self.assertGreaterEqual(len(sections[heading].split()), 8, heading)
                self.assertIn(f"Default depth: `{depth}`", sections["Default Knowledge Read"])
                self.assertIn(
                    f"Default granularity: `{granularity}`",
                    sections["Default Knowledge Read"],
                )
                criteria = sections["Append, Single-Note, and Split Criteria"]
                for decision in ("**Append**", "**Single-note**", "**Split**"):
                    self.assertIn(decision, criteria)
                self.assertIn("`conversation`", sections["Evidence Rules"])
                self.assertIn(
                    "`source_read_completed=true`",
                    sections["Evidence Rules"],
                )
                self.assertIn(
                    "`verification_completed=true`",
                    sections["Evidence Rules"],
                )
                self.assertIn("Verify", sections["Mode-Specific Validation"])

    def test_mode_boundaries_are_explicit(self) -> None:
        required_fragments = {
            "capture": ("low-friction", "never expand it to `deep` by default"),
            "dissection": ("internals", "ordinary explanation", "`learning`"),
            "project": ("user's project", "reusable mechanisms", "`dissection`"),
            "index": ("hub note", "existing targets"),
            "review": ("Evidence", "Root Causes", "Corrective Actions", "Unresolved Questions"),
            "comparison": ("Requirements", "Evaluation Dimensions", "Trade-offs", "Decision"),
        }
        for mode, fragments in required_fragments.items():
            with self.subTest(mode=mode):
                text = self.read_reference(
                    REFERENCES_PATH / "modes" / f"{mode}.md"
                )
                for fragment in fragments:
                    self.assertIn(fragment, text)

    def test_dissection_requires_causal_before_after_and_comparative_analysis(self) -> None:
        text = self.read_reference(
            REFERENCES_PATH / "modes" / "dissection.md"
        )
        sections = h2_sections(text)

        for heading in (
            "Object and Scope",
            "Problem and Prior State",
            "Solution Thesis",
            "Mechanism Chain",
            "Adoption Effects",
            "Horizontal Comparison",
            "Vertical Evolution",
            "Distinctive Advantages",
            "Trade-offs and Limits",
            "Reusable Patterns",
            "Evidence and Open Questions",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, sections["Recommended Note Shape"])

        self.assertIn(
            "problem -> design choice -> mechanism -> outcome -> evidence",
            sections["Recommended Note Shape"],
        )
        self.assertIn(
            "differentiator -> causal mechanism -> conditions -> evidence",
            sections["Recommended Note Shape"],
        )
        for effect_dimension in (
            "capability",
            "quality",
            "cost",
            "latency",
            "user experience",
            "operations",
            "risk",
            "regressions",
        ):
            with self.subTest(effect_dimension=effect_dimension):
                self.assertIn(effect_dimension, sections["Recommended Note Shape"])
        for evidence_status in ("observed", "claimed", "inferred", "unknown"):
            with self.subTest(evidence_status=evidence_status):
                self.assertIn(evidence_status, sections["Evidence Rules"])
        for comparison_guard in (
            "compatible versions",
            "deployment models",
            "Evaluation Dimensions",
            "named versions",
            "prior approaches",
        ):
            with self.subTest(comparison_guard=comparison_guard):
                self.assertIn(comparison_guard, sections["Evidence Rules"])

        self.assertIn("main goal is choosing among options", sections["When to Use"])
        self.assertIn("`comparison`", sections["When to Use"])

    def test_public_guides_and_prompt_expose_the_expanded_dissection_outcome(self) -> None:
        english = (REPO_ROOT / "docs" / "modes.md").read_text(encoding="utf-8")
        chinese = (REPO_ROOT / "docs" / "modes.zh-CN.md").read_text(
            encoding="utf-8"
        )
        prompts = (REPO_ROOT / "examples" / "prompts.md").read_text(
            encoding="utf-8"
        )

        for fragment in (
            "problem and prior state",
            "adoption effects",
            "horizontal peers",
            "vertical evolution",
            "supported advantages",
        ):
            with self.subTest(language="english", fragment=fragment):
                self.assertIn(fragment, english)
        for fragment in (
            "原问题与原状态",
            "采用后的变化",
            "横向竞品",
            "纵向演进",
            "有证据支撑的独特优势",
        ):
            with self.subTest(language="chinese", fragment=fragment):
                self.assertIn(fragment, chinese)
        for fragment in (
            "problem -> design choice -> mechanism -> outcome -> evidence",
            "horizontal comparison",
            "vertical comparison",
            "Do not invent competitors",
        ):
            with self.subTest(source="prompt", fragment=fragment):
                self.assertIn(fragment, prompts)

    def test_review_and_project_note_types_match_the_mode_boundary(self) -> None:
        note_type_sections = h2_sections(
            NOTE_TYPES_PATH.read_text(encoding="utf-8")
        )
        review_mode = self.read_reference(
            REFERENCES_PATH / "modes" / "review.md"
        )
        self.assertIn("Review Note", note_type_sections)
        review_note = note_type_sections["Review Note"]
        project_note = note_type_sections["Project Note"]

        for subject in ("incidents", "failures", "experiments"):
            with self.subTest(subject=subject):
                self.assertIn(subject, review_mode)
                self.assertIn(subject, review_note)
                self.assertNotIn(subject, project_note)
        for section in ("Evidence", "Root Causes", "Corrective Actions"):
            with self.subTest(section=section):
                self.assertIn(section, review_mode)
                self.assertIn(f"- {section}", review_note)
        for project_scope in ("specific project", "implementation", "operations"):
            with self.subTest(project_scope=project_scope):
                self.assertIn(project_scope, project_note)

    def test_mode_references_do_not_repeat_the_common_iron_law(self) -> None:
        forbidden = (
            "Iron Law",
            "NEVER WRITE TO THE VAULT WITHOUT SEARCHING EXISTING NOTES FIRST",
        )
        for mode in MODE_NAMES:
            with self.subTest(mode=mode):
                text = self.read_reference(
                    REFERENCES_PATH / "modes" / f"{mode}.md"
                )
                for fragment in forbidden:
                    self.assertNotIn(fragment, text)

    def test_each_host_detects_tools_before_mapping_capabilities(self) -> None:
        for host in HOST_NAMES:
            path = REFERENCES_PATH / "hosts" / f"{host}.md"
            with self.subTest(host=host):
                text = self.read_reference(path)
                self.assertEqual(HOST_HEADINGS, h2_headings(text))
                self.assertLess(text.index("## Detect Capabilities"), text.index("## Capability Mapping"))
                self.assertIn("actual available tools", text)
                for capability_level in CAPABILITY_LEVELS:
                    self.assertIn(f"`{capability_level}`", text)
                self.assertIn("../preflight.md", text)

    def test_full_local_mapping_requires_mcp_scan_dry_run_and_write(self) -> None:
        required_paths = ("mcp", "scan", "dry-run", "approved write")
        for host in HOST_NAMES:
            with self.subTest(host=host):
                text = self.read_reference(
                    REFERENCES_PATH / "hosts" / f"{host}.md"
                )
                mapping = h2_sections(text)["Capability Mapping"]
                full_local_lines = [
                    line.casefold()
                    for line in mapping.splitlines()
                    if "use `full-local`" in line.casefold()
                ]
                self.assertEqual(1, len(full_local_lines))
                for required_path in required_paths:
                    self.assertIn(required_path, full_local_lines[0])

    def test_write_capable_mappings_require_scan_dry_run_and_write(self) -> None:
        required_paths = ("scan", "dry-run", "approved write")
        for host in HOST_NAMES:
            text = self.read_reference(
                REFERENCES_PATH / "hosts" / f"{host}.md"
            )
            mapping = h2_sections(text)["Capability Mapping"]
            for capability_level in ("full-local", "filesystem-only"):
                with self.subTest(host=host, capability_level=capability_level):
                    mapping_lines = [
                        line.casefold()
                        for line in mapping.splitlines()
                        if f"use `{capability_level}`" in line.casefold()
                    ]
                    self.assertEqual(1, len(mapping_lines))
                    for required_path in required_paths:
                        self.assertIn(required_path, mapping_lines[0])

    def test_mcp_readonly_mapping_is_transport_neutral(self) -> None:
        for host in HOST_NAMES:
            with self.subTest(host=host):
                text = self.read_reference(
                    REFERENCES_PATH / "hosts" / f"{host}.md"
                )
                mapping = h2_sections(text)["Capability Mapping"]
                self.assertIn("transport-neutral effective read-only", text)
                self.assertIn("without MCP", text)
                read_only_lines = [
                    line.casefold()
                    for line in mapping.splitlines()
                    if "use `mcp-readonly`" in line.casefold()
                ]
                self.assertEqual(1, len(read_only_lines))
                for fragment in (
                    "scan",
                    "dry-run",
                    "no approved write",
                ):
                    self.assertIn(fragment, read_only_lines[0])
                self.assertIn("validation_available=false", text)
                self.assertIn(
                    "keep `full-local` or `filesystem-only`",
                    text,
                )

    def test_chat_only_mapping_requires_no_scan_path(self) -> None:
        for host in HOST_NAMES:
            with self.subTest(host=host):
                text = self.read_reference(
                    REFERENCES_PATH / "hosts" / f"{host}.md"
                )
                mapping = h2_sections(text)["Capability Mapping"]
                chat_only_lines = [
                    line.casefold()
                    for line in mapping.splitlines()
                    if "use `chat-only`" in line.casefold()
                ]
                self.assertEqual(1, len(chat_only_lines))
                self.assertIn("no", chat_only_lines[0])
                self.assertIn("scan", chat_only_lines[0])

    def test_host_references_have_no_user_specific_absolute_paths(self) -> None:
        absolute_path_patterns = (
            re.compile(r"[A-Za-z]:[\\/]"),
            re.compile(r"/(?:Users|home)/[^\s`]+"),
        )
        for host in HOST_NAMES:
            with self.subTest(host=host):
                text = self.read_reference(
                    REFERENCES_PATH / "hosts" / f"{host}.md"
                )
                for pattern in absolute_path_patterns:
                    self.assertIsNone(pattern.search(text))

    def test_preflight_documents_every_block_and_write_readiness_semantics(self) -> None:
        text = self.read_reference(REFERENCES_PATH / "preflight.md")

        for reason in BLOCKED_REASONS:
            self.assertIn(f"`{reason}`", text)
        self.assertIn("`validation_available`", text)
        self.assertIn("independently", text)
        self.assertIn("approved write", text)
        self.assertIn("does not mean that a write already happened", text)
        self.assertIn("Never claim", text)
        self.assertIn("unavailable", text)
        self.assertIn("transport-neutral effective read-only", text)
        self.assertIn("historical name", text)

    def test_skill_routes_to_one_mode_one_host_and_shared_preflight(self) -> None:
        text = SKILL_PATH.read_text(encoding="utf-8")

        for mode in MODE_NAMES:
            self.assertIn(f"references/modes/{mode}.md", text)
        for host in HOST_NAMES:
            self.assertIn(f"references/hosts/{host}.md", text)
        self.assertIn("references/preflight.md", text)
        required_rules = (
            "Explicit mode -> load only its mode reference.",
            "Clear inferred mode -> state it and load only its mode reference.",
            "Ambiguous mode -> recommend at most two modes",
            "Detect the host's actual tools before loading only the matching host reference.",
        )
        for rule in required_rules:
            self.assertIn(rule, text)

    def test_skill_always_computes_knowledge_read_and_only_varies_display(self) -> None:
        text = SKILL_PATH.read_text(encoding="utf-8")

        for fragment in ("Knowledge Read", "整理判读", "`auto`", "`always`", "`off`"):
            self.assertIn(fragment, text)
        self.assertIn("always computed", text)
        self.assertIn("presentation only", text)
        self.assertIn("`source_read_completed=true`", text)
        self.assertIn("`verification_completed=true`", text)
        self.assertIn("host-completed facts", text)
        self.assertIn("granularity=append", text)
        self.assertIn("`validation_available`", text)
        self.assertIn("validation capability independently", text)


if __name__ == "__main__":
    unittest.main()
