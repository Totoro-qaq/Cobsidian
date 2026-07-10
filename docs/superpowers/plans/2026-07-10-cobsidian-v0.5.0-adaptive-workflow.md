# Cobsidian v0.5.0 Adaptive Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a host-adaptive Cobsidian workflow with progressive mode references, structured Knowledge Read output, deterministic preflight readiness, optional presentation, and preserved v0.4.0 safety behavior.

**Architecture:** Keep one host-neutral `SKILL.md` as the router. Move mode and host detail into on-demand references. Add two deterministic Python modules for Knowledge Read and preflight, then expose their additive payloads through the existing dry-run CLI and MCP tool.

**Tech Stack:** Python 3.11+, `unittest`, Markdown Agent Skill references, YAML-like local config, FastMCP, GitHub Actions.

---

## File Map

### Create

- `skills/cobsidian/scripts/knowledge_read.py`: canonical modes, defaults, enum validation, display policy, and JSON serialization.
- `skills/cobsidian/scripts/preflight.py`: host capability profiles, readiness evaluation, and blocked reasons.
- `skills/cobsidian/references/modes/*.md`: seven mode-specific execution contracts.
- `skills/cobsidian/references/hosts/*.md`: five capability-first host adapters.
- `skills/cobsidian/references/preflight.md`: shared readiness and fail-closed semantics.
- `tests/test_knowledge_read.py`: Knowledge Read unit contracts.
- `tests/test_preflight.py`: capability/readiness unit contracts.
- `tests/test_adaptive_skill_contract.py`: progressive-reference and routing contracts.

### Modify

- `skills/cobsidian/scripts/cobsidian_config.py`: enforce `interaction.knowledge_read`.
- `skills/cobsidian/scripts/dry_run.py`: additive Knowledge Read and preflight payloads plus CLI options.
- `skills/cobsidian/mcp_server.py`: expose the same optional fields with an MCP read-only default.
- `skills/cobsidian/SKILL.md`: reduce to the common router and safety contract.
- `cobsidian.config.example.yml`: document the enforced display policy.
- Existing config, dry-run, MCP, skill, hygiene, and README tests.
- English and Chinese README, modes, compatibility, integration, and MCP docs.
- `CHANGELOG.md`: document v0.5.0 adaptive behavior.

## Pre-Implementation Baseline

- [ ] Run the v0.4.0 baseline before adding a failing test:

```powershell
python -m pip install -r requirements-mcp.txt -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m compileall -q skills tests
python skills/cobsidian/scripts/validate_skill.py skills/cobsidian
git status --short --branch
```

Expected: `47` tests pass, compile and skill validation exit `0`, and the worktree is clean except for the committed design and plan history.

## Task 1: Add the Knowledge Read Domain Contract

**Files:**
- Create: `tests/test_knowledge_read.py`
- Create: `skills/cobsidian/scripts/knowledge_read.py`

- [ ] **Step 1: Write the failing Knowledge Read tests**

Create `tests/test_knowledge_read.py` with these contracts:

```python
from __future__ import annotations

import unittest

from skills.cobsidian.scripts.knowledge_read import (
    MODE_DEFAULTS,
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
        self.assertEqual(expected, MODE_DEFAULTS)

    def test_auto_display_expands_complex_or_inferred_work(self) -> None:
        inferred = build_knowledge_read(mode="learning", mode_explicit=False)
        deep = build_knowledge_read(mode="project", mode_explicit=True)
        compact = build_knowledge_read(mode="learning", mode_explicit=True)

        self.assertEqual("expanded", inferred.display_style)
        self.assertEqual("expanded", deep.display_style)
        self.assertEqual("compact", compact.display_style)

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
        self.assertEqual("dissection", hidden.to_payload()["mode"])
        self.assertEqual("deep", hidden.to_payload()["depth"])

    def test_append_decision_overrides_default_granularity(self) -> None:
        knowledge_read = build_knowledge_read(
            mode="index",
            mode_explicit=True,
            decision_action="append",
        )
        self.assertEqual("append", knowledge_read.granularity)

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

        with self.assertRaisesRegex(ValueError, "at most two"):
            build_knowledge_read(
                mode=None,
                mode_explicit=False,
                recommended_modes=["learning", "project", "review"],
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and verify the red state**

Run:

```powershell
python -m unittest discover -s tests -p "test_knowledge_read.py" -v
```

Expected: FAIL because `skills.cobsidian.scripts.knowledge_read` does not exist.

- [ ] **Step 3: Implement the minimal typed domain module**

Create `skills/cobsidian/scripts/knowledge_read.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


MODES = (
    "learning",
    "project",
    "review",
    "comparison",
    "index",
    "capture",
    "dissection",
)
DEPTHS = ("capture", "standard", "deep")
GRANULARITIES = ("append", "single-note", "multi-note")
EVIDENCE_LEVELS = ("conversation", "source-grounded", "verified")
DISPLAY_POLICIES = ("auto", "always", "off")
MODE_DEFAULTS = {
    "learning": ("standard", "single-note"),
    "project": ("deep", "single-note"),
    "review": ("deep", "single-note"),
    "comparison": ("standard", "single-note"),
    "index": ("deep", "multi-note"),
    "capture": ("capture", "single-note"),
    "dissection": ("deep", "multi-note"),
}


@dataclass(frozen=True)
class KnowledgeRead:
    mode: str | None
    mode_explicit: bool
    recommended_modes: tuple[str, ...]
    depth: str
    granularity: str
    evidence: str
    display_policy: str
    display_style: str

    def to_payload(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "mode_explicit": self.mode_explicit,
            "recommended_modes": list(self.recommended_modes),
            "depth": self.depth,
            "granularity": self.granularity,
            "evidence": self.evidence,
            "display_policy": self.display_policy,
            "display_style": self.display_style,
        }


def validated_choice(name: str, value: str, allowed: tuple[str, ...]) -> str:
    if value not in allowed:
        raise ValueError(f"{name} must be one of: {', '.join(allowed)}.")
    return value


def validated_recommendations(
    mode: str | None,
    recommended_modes: Iterable[str] | None,
) -> tuple[str, ...]:
    recommendations = tuple(recommended_modes or ())
    if len(recommendations) > 2:
        raise ValueError("recommended_modes accepts at most two modes.")
    if mode is not None and recommendations:
        raise ValueError("recommended_modes requires an unresolved mode.")
    for recommendation in recommendations:
        validated_choice("recommended mode", recommendation, MODES)
    return recommendations


def resolve_display_style(
    policy: str,
    mode_explicit: bool,
    depth: str,
    granularity: str,
    evidence: str,
) -> str:
    if policy == "always":
        return "expanded"
    if policy == "off":
        return "hidden"
    if (
        not mode_explicit
        or depth == "deep"
        or granularity == "multi-note"
        or evidence in {"source-grounded", "verified"}
    ):
        return "expanded"
    return "compact"


def build_knowledge_read(
    mode: str | None,
    mode_explicit: bool,
    recommended_modes: Iterable[str] | None = None,
    depth: str | None = None,
    granularity: str | None = None,
    evidence: str = "conversation",
    display_policy: str = "auto",
    decision_action: str | None = None,
) -> KnowledgeRead:
    if mode is not None:
        validated_choice("mode", mode, MODES)
    recommendations = validated_recommendations(mode, recommended_modes)
    default_depth, default_granularity = MODE_DEFAULTS.get(
        mode,
        ("standard", "single-note"),
    )
    resolved_depth = validated_choice("depth", depth or default_depth, DEPTHS)
    resolved_granularity = validated_choice(
        "granularity",
        "append" if decision_action == "append" else granularity or default_granularity,
        GRANULARITIES,
    )
    resolved_evidence = validated_choice("evidence", evidence, EVIDENCE_LEVELS)
    resolved_policy = validated_choice(
        "display_policy",
        display_policy,
        DISPLAY_POLICIES,
    )
    return KnowledgeRead(
        mode=mode,
        mode_explicit=mode_explicit,
        recommended_modes=recommendations,
        depth=resolved_depth,
        granularity=resolved_granularity,
        evidence=resolved_evidence,
        display_policy=resolved_policy,
        display_style=resolve_display_style(
            resolved_policy,
            mode_explicit,
            resolved_depth,
            resolved_granularity,
            resolved_evidence,
        ),
    )
```

- [ ] **Step 4: Run the focused tests and compile the module**

Run:

```powershell
python -m unittest discover -s tests -p "test_knowledge_read.py" -v
python -m compileall -q skills/cobsidian/scripts/knowledge_read.py
```

Expected: all Knowledge Read tests pass; compile exits `0`.

- [ ] **Step 5: Commit Task 1**

```powershell
git add tests/test_knowledge_read.py skills/cobsidian/scripts/knowledge_read.py
git commit -m "feat: add Knowledge Read contract"
```

## Task 2: Add Capability-Aware Preflight

**Files:**
- Create: `tests/test_preflight.py`
- Create: `skills/cobsidian/scripts/preflight.py`

- [ ] **Step 1: Write failing capability/readiness tests**

Create tests that assert:

```python
from __future__ import annotations

import unittest

from skills.cobsidian.scripts.preflight import build_preflight


class PreflightTests(unittest.TestCase):
    def test_local_capabilities_are_ready_after_all_checks(self) -> None:
        for capability in ("full-local", "filesystem-only"):
            with self.subTest(capability=capability):
                result = build_preflight(capability_level=capability)
                self.assertTrue(result.ready)
                self.assertEqual([], result.to_payload()["blocked_reasons"])

    def test_read_only_and_chat_hosts_are_not_write_ready(self) -> None:
        mcp = build_preflight(capability_level="mcp-readonly")
        chat = build_preflight(
            capability_level="chat-only",
            existing_notes_scanned=False,
            duplicate_check_completed=False,
            backlink_check_completed=False,
        )

        self.assertFalse(mcp.ready)
        self.assertIn("write_capability_unavailable", mcp.blocked_reasons)
        self.assertFalse(chat.ready)
        self.assertIn("scan_capability_unavailable", chat.blocked_reasons)
        self.assertIn("write_capability_unavailable", chat.blocked_reasons)

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

    def test_invalid_capability_level_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "capability_level"):
            build_preflight(capability_level="browser-only")
```

- [ ] **Step 2: Verify the tests fail because the module is missing**

Run:

```powershell
python -m unittest discover -s tests -p "test_preflight.py" -v
```

- [ ] **Step 3: Implement `preflight.py`**

Create `skills/cobsidian/scripts/preflight.py` with:

```python
from __future__ import annotations

from dataclasses import dataclass


CAPABILITY_FLAGS = {
    "full-local": {"scan": True, "write": True},
    "filesystem-only": {"scan": True, "write": True},
    "mcp-readonly": {"scan": True, "write": False},
    "chat-only": {"scan": False, "write": False},
}
CAPABILITY_LEVELS = tuple(CAPABILITY_FLAGS)


@dataclass(frozen=True)
class Preflight:
    vault_resolved: bool
    existing_notes_scanned: bool
    duplicate_check_completed: bool
    backlink_check_completed: bool
    mode_selected: bool
    capability_level: str
    write_policy: str
    ready: bool
    blocked_reasons: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "vault_resolved": self.vault_resolved,
            "existing_notes_scanned": self.existing_notes_scanned,
            "duplicate_check_completed": self.duplicate_check_completed,
            "backlink_check_completed": self.backlink_check_completed,
            "mode_selected": self.mode_selected,
            "capability_level": self.capability_level,
            "write_policy": self.write_policy,
            "ready": self.ready,
            "blocked_reasons": list(self.blocked_reasons),
        }


def build_preflight(
    capability_level: str,
    vault_resolved: bool = True,
    existing_notes_scanned: bool = True,
    duplicate_check_completed: bool = True,
    backlink_check_completed: bool = True,
    mode_selected: bool = True,
    write_policy: str = "dry-run",
) -> Preflight:
    if capability_level not in CAPABILITY_FLAGS:
        allowed = ", ".join(CAPABILITY_LEVELS)
        raise ValueError(f"capability_level must be one of: {allowed}.")

    capabilities = CAPABILITY_FLAGS[capability_level]
    blocked_reasons: list[str] = []
    if not vault_resolved:
        blocked_reasons.append("vault_unresolved")
    if not capabilities["scan"]:
        blocked_reasons.append("scan_capability_unavailable")
    if not existing_notes_scanned:
        blocked_reasons.append("existing_notes_not_scanned")
    if not duplicate_check_completed:
        blocked_reasons.append("duplicate_check_incomplete")
    if not backlink_check_completed:
        blocked_reasons.append("backlink_check_incomplete")
    if not mode_selected:
        blocked_reasons.append("mode_unresolved")
    if not capabilities["write"]:
        blocked_reasons.append("write_capability_unavailable")

    reasons = tuple(blocked_reasons)
    return Preflight(
        vault_resolved=vault_resolved,
        existing_notes_scanned=existing_notes_scanned,
        duplicate_check_completed=duplicate_check_completed,
        backlink_check_completed=backlink_check_completed,
        mode_selected=mode_selected,
        capability_level=capability_level,
        write_policy=write_policy,
        ready=not reasons,
        blocked_reasons=reasons,
    )
```

- [ ] **Step 4: Run focused tests and compile**

```powershell
python -m unittest discover -s tests -p "test_preflight.py" -v
python -m compileall -q skills/cobsidian/scripts/preflight.py
```

- [ ] **Step 5: Commit Task 2**

```powershell
git add tests/test_preflight.py skills/cobsidian/scripts/preflight.py
git commit -m "feat: add host capability preflight"
```

## Task 3: Enforce the Knowledge Read Configuration Surface

**Files:**
- Modify: `tests/test_config_contract.py`
- Modify: `tests/test_config_and_dry_run.py`
- Modify: `skills/cobsidian/scripts/cobsidian_config.py`
- Modify: `cobsidian.config.example.yml`

- [ ] **Step 1: Add failing config tests**

Extend config tests to require:

```python
self.assertIn("interaction.knowledge_read", SUPPORTED_CONFIG_LEAF_PATHS)
```

Add property tests:

```python
configured = CobsidianConfig(
    config_path=None,
    raw={"interaction": {"knowledge_read": "off"}},
)
self.assertEqual("off", configured.knowledge_read_policy)
self.assertEqual("auto", CobsidianConfig(None, {}).knowledge_read_policy)

invalid = CobsidianConfig(
    config_path=None,
    raw={"interaction": {"knowledge_read": "sometimes"}},
)
with self.assertRaisesRegex(ValueError, "knowledge_read"):
    _ = invalid.knowledge_read_policy
```

- [ ] **Step 2: Run config tests and confirm failure**

```powershell
python -m unittest discover -s tests -p "test_config*.py" -v
```

- [ ] **Step 3: Implement the config property and summary**

Add `interaction.knowledge_read` to `SUPPORTED_CONFIG_LEAF_PATHS` and add:

```python
KNOWLEDGE_READ_POLICIES = {"auto", "always", "off"}

@property
def knowledge_read_policy(self) -> str:
    policy = str(
        self.get("interaction", "knowledge_read", default="auto")
    ).casefold()
    if policy not in KNOWLEDGE_READ_POLICIES:
        allowed = ", ".join(sorted(KNOWLEDGE_READ_POLICIES))
        raise ValueError(f"interaction.knowledge_read must be one of: {allowed}.")
    return policy
```

Include `interaction` in `public_summary()` with the same defensive dictionary handling used by existing sections.

Update the example:

```yaml
# Cobsidian v0.5 supported config.
interaction:
  # auto expands complex/inferred work, always expands, off hides presentation only.
  knowledge_read: auto
```

- [ ] **Step 4: Run config and contract tests**

```powershell
python -m unittest discover -s tests -p "test_config*.py" -v
```

- [ ] **Step 5: Commit Task 3**

```powershell
git add tests/test_config_contract.py tests/test_config_and_dry_run.py skills/cobsidian/scripts/cobsidian_config.py cobsidian.config.example.yml
git commit -m "feat: configure Knowledge Read display"
```

## Task 4: Extend Dry-Run Without Breaking v0.4 Callers

**Files:**
- Modify: `tests/test_config_and_dry_run.py`
- Modify: `tests/test_retrieval_entrypoints.py`
- Modify: `skills/cobsidian/scripts/dry_run.py`

- [ ] **Step 1: Add failing additive-payload tests**

Cover these cases:

1. Existing six-argument `build_payload(...)` calls still succeed.
2. Explicit `learning` produces compact Knowledge Read and ready `filesystem-only` preflight.
3. Existing append decisions produce `granularity="append"`.
4. Config `off` produces `display_style="hidden"` while retaining all fields.
5. Unresolved mode with two recommendations produces expanded output and `mode_unresolved` readiness.
6. CLI JSON defaults to `filesystem-only` and accepts enum options.

Use assertions such as:

```python
self.assertEqual("compact", payload["knowledge_read"]["display_style"])
self.assertEqual("filesystem-only", payload["preflight"]["capability_level"])
self.assertTrue(payload["preflight"]["ready"])
self.assertEqual([], payload["writes"])
```

- [ ] **Step 2: Run focused tests and verify missing fields fail**

```powershell
python -m unittest discover -s tests -p "test_config_and_dry_run.py" -v
python -m unittest discover -s tests -p "test_retrieval_entrypoints.py" -v
```

- [ ] **Step 3: Extend `build_payload()` with keyword-only options**

Append these keyword-only parameters after `notes`:

```python
*,
mode_explicit: bool = False,
recommended_modes: list[str] | None = None,
depth: str | None = None,
granularity: str | None = None,
evidence: str = "conversation",
capability_level: str = "filesystem-only",
knowledge_read_policy: str | None = None,
```

Build the existing decision first. Then call:

```python
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
preflight = build_preflight(
    capability_level=capability_level,
    mode_selected=knowledge_read.mode is not None,
)
```

Add `knowledge_read.to_payload()` and `preflight.to_payload()` to the returned dictionary. Keep all existing keys unchanged.

- [ ] **Step 4: Add CLI options with runtime choices**

Add:

```python
--mode-explicit / --no-mode-explicit
--recommended-mode (repeatable, maximum enforced by the domain module)
--depth
--granularity
--evidence
--capability-level
--knowledge-read
```

Use `argparse.BooleanOptionalAction` for mode explicitness. If it is omitted, treat a direct `--mode` as explicit and a config default as inferred. Local CLI capability defaults to `filesystem-only`.

- [ ] **Step 5: Run focused tests, the full suite, and compile**

```powershell
python -m unittest discover -s tests -p "test_config_and_dry_run.py" -v
python -m unittest discover -s tests -p "test_retrieval_entrypoints.py" -v
python -m unittest discover -s tests -v
python -m compileall -q skills tests
```

- [ ] **Step 6: Commit Task 4**

```powershell
git add tests/test_config_and_dry_run.py tests/test_retrieval_entrypoints.py skills/cobsidian/scripts/dry_run.py
git commit -m "feat: expose adaptive dry-run context"
```

## Task 5: Add MCP Parity and Preserve Read-Only Safety

**Files:**
- Modify: `tests/test_mcp_server.py`
- Modify: `skills/cobsidian/mcp_server.py`

- [ ] **Step 1: Add failing MCP parity tests**

Test that:

- MCP dry-run defaults to `mcp-readonly` and `ready=false`;
- `write_capability_unavailable` appears in blocked reasons;
- optional mode/depth/granularity/evidence/display arguments match shared dry-run output;
- `writes` remains empty;
- registered tool names contain no write tool;
- invalid enum values propagate as `ValueError`.

Expected key assertions:

```python
self.assertEqual("mcp-readonly", payload["preflight"]["capability_level"])
self.assertFalse(payload["preflight"]["ready"])
self.assertIn(
    "write_capability_unavailable",
    payload["preflight"]["blocked_reasons"],
)
self.assertEqual([], payload["writes"])
```

- [ ] **Step 2: Verify the new MCP tests fail**

```powershell
python -m unittest discover -s tests -p "test_mcp_server.py" -v
```

- [ ] **Step 3: Extend `tool_cobsidian_dry_run()`**

Add optional fields matching `build_payload()`. Resolve mode as today, infer `mode_explicit` from direct MCP input when the caller omits it, and default `capability_level` to `mcp-readonly`.

Do not add or register any write tool. Update the MCP server instructions and dry-run prompt to mention `knowledge_read`, `preflight`, and read-only readiness.

- [ ] **Step 4: Run MCP, full-suite, and compile gates**

```powershell
python -m unittest discover -s tests -p "test_mcp_server.py" -v
python -m unittest discover -s tests -v
python -m compileall -q skills tests
```

- [ ] **Step 5: Commit Task 5**

```powershell
git add tests/test_mcp_server.py skills/cobsidian/mcp_server.py
git commit -m "feat: add adaptive MCP dry-run parity"
```

## Task 6: Convert the Skill to Progressive Disclosure

**Files:**
- Create: `tests/test_adaptive_skill_contract.py`
- Modify: `tests/test_cobsidian_skill_contract.py`
- Modify: `skills/cobsidian/SKILL.md`
- Create: `skills/cobsidian/references/modes/learning.md`
- Create: `skills/cobsidian/references/modes/project.md`
- Create: `skills/cobsidian/references/modes/review.md`
- Create: `skills/cobsidian/references/modes/comparison.md`
- Create: `skills/cobsidian/references/modes/index.md`
- Create: `skills/cobsidian/references/modes/capture.md`
- Create: `skills/cobsidian/references/modes/dissection.md`
- Create: `skills/cobsidian/references/hosts/codex.md`
- Create: `skills/cobsidian/references/hosts/claude-code.md`
- Create: `skills/cobsidian/references/hosts/cursor.md`
- Create: `skills/cobsidian/references/hosts/hermes.md`
- Create: `skills/cobsidian/references/hosts/mcp.md`
- Create: `skills/cobsidian/references/preflight.md`

- [ ] **Step 1: Write failing structural contract tests**

`test_adaptive_skill_contract.py` must verify:

- all seven mode files and all five host files exist;
- every mode file contains all eight headings from the design;
- every host file contains `Detect Capabilities`, `Capability Mapping`, `Execution Path`, `Degradation`, and `Safety`;
- `SKILL.md` links to all mode references, the matching host reference rule, and `references/preflight.md`;
- `SKILL.md` contains `auto`, `always`, `off`, `Knowledge Read`, and `整理判读`;
- ambiguous mode routing says to recommend at most two modes;
- no host reference contains local user paths;
- no mode reference repeats the common scan-before-write Iron Law.

Update the existing mode-picker test: remove requirements for the full seven-item English and Chinese menus, and require context-aware recommendations plus canonical bilingual labels instead.

- [ ] **Step 2: Run structural tests and verify the missing references fail**

```powershell
python -m unittest discover -s tests -p "test_*skill_contract.py" -v
```

- [ ] **Step 3: Create the seven mode references**

Every file uses these headings exactly:

```markdown
# <Mode> Mode
## When to Use
## Required Inputs
## Default Knowledge Read
## Recommended Note Shape
## Append, Single-Note, and Split Criteria
## Evidence Rules
## Mode-Specific Validation
## Completion Report Additions
```

Use the mode defaults from `MODE_DEFAULTS`. Each file must contain concrete note sections and split criteria. Important boundaries:

- `capture` stays low-friction and never defaults to deep expansion.
- `dissection` requires internals, source, workflow, prompt, or framework mechanics; a normal explanation remains `learning`.
- `project` documents the user's project; `dissection` extracts reusable mechanisms from a studied system.
- `index` may propose multiple notes but must identify the hub note and existing targets.
- `review` separates evidence, root causes, corrective actions, and unresolved questions.
- `comparison` separates requirements, evaluation dimensions, evidence, trade-offs, and decision.

- [ ] **Step 4: Create capability-first host references**

Every host file uses:

```markdown
# <Host> Adapter
## Detect Capabilities
## Capability Mapping
## Execution Path
## Degradation
## Safety
```

The references must tell the agent to inspect actual tools instead of assuming capabilities. Product-specific text is limited to invocation/tool mapping; all behavior points back to the canonical capability levels and `references/preflight.md`.

Required defaults:

- generic MCP uses `mcp-readonly`;
- a host with local filesystem and shell but no MCP uses `filesystem-only`;
- a host without vault access uses `chat-only`;
- a host with MCP plus approved filesystem writes may use `full-local`.

- [ ] **Step 5: Create `references/preflight.md`**

Document exact blocked reasons, readiness semantics, the fact that `ready` means ready for an approved write rather than already written, and the prohibition on claiming unavailable actions.

- [ ] **Step 6: Refactor `SKILL.md` into the concise router**

Preserve frontmatter, Core Principle, Iron Law, Response Language, Vault Resolution, common write rules, red flags, helper scripts, and completion reporting. Replace the full mode picker with a concise routing table and these rules:

```text
Explicit mode -> load only its mode reference.
Clear inferred mode -> state it and load only its reference.
Ambiguous mode -> recommend at most two modes; do not dump all seven.
Detect host tools -> load only the matching host reference.
Knowledge Read is always computed; auto/always/off changes presentation only.
```

- [ ] **Step 7: Run contract, validation, and full tests**

```powershell
python -m unittest discover -s tests -p "test_*skill_contract.py" -v
python skills/cobsidian/scripts/validate_skill.py skills/cobsidian
python -m unittest discover -s tests -v
git diff --check
```

- [ ] **Step 8: Commit Task 6**

```powershell
git add tests/test_adaptive_skill_contract.py tests/test_cobsidian_skill_contract.py skills/cobsidian/SKILL.md skills/cobsidian/references
git commit -m "feat: add progressive mode and host adapters"
```

## Task 7: Document v0.5.0 in English and Chinese

**Files:**
- Modify: `README.md`
- Modify: `docs/README.zh-CN.md`
- Modify: `docs/modes.md`
- Modify: `docs/modes.zh-CN.md`
- Modify: `docs/agent-compatibility.md`
- Modify: `docs/agent-compatibility.zh-CN.md`
- Modify: `docs/integrations.md`
- Modify: `docs/integrations.zh-CN.md`
- Modify: `docs/mcp-server.md`
- Modify: `docs/mcp-server.zh-CN.md`
- Modify: `CHANGELOG.md`
- Modify: `tests/test_documentation_hygiene.py`
- Modify: `tests/test_readme_landing_contract.py`

- [ ] **Step 1: Add failing documentation contract assertions**

Require both READMEs to mention:

- `Knowledge Read` and `整理判读`;
- `auto | always | off`;
- capability-based degradation;
- dry-run JSON retaining hidden Knowledge Read;
- v0.5.0 as the supported config surface.

Require public docs to remain free of machine-specific paths and unsupported claims.

- [ ] **Step 2: Run documentation tests and confirm failure**

```powershell
python -m unittest discover -s tests -p "test_*documentation*.py" -v
python -m unittest discover -s tests -p "test_readme_landing_contract.py" -v
```

- [ ] **Step 3: Update user-facing documentation**

Add one compact and one expanded Knowledge Read example. Explain that display can be hidden but computation and JSON remain. Add the capability table and clarify that MCP remains read-only.

Keep detailed mode execution rules in skill references; user docs explain outcomes rather than duplicating operational prompts.

Move `Unreleased` entries into a `v0.5.0` section in `CHANGELOG.md` only when the implementation is otherwise complete. List adaptive routing, references, Knowledge Read, preflight, config, parity, and compatibility.

- [ ] **Step 4: Run documentation, skill, and full tests**

```powershell
python -m unittest discover -s tests -p "test_*documentation*.py" -v
python -m unittest discover -s tests -p "test_readme_landing_contract.py" -v
python skills/cobsidian/scripts/validate_skill.py skills/cobsidian
python -m unittest discover -s tests -v
git diff --check
```

- [ ] **Step 5: Commit Task 7**

```powershell
git add README.md docs CHANGELOG.md tests/test_documentation_hygiene.py tests/test_readme_landing_contract.py
git commit -m "docs: prepare Cobsidian v0.5.0"
```

## Task 8: Verify, Forward-Test, Review, and Re-Evaluate

**Files:**
- No production files unless verification identifies a defect.

- [ ] **Step 1: Run the complete local gate from a fresh process**

```powershell
python -m pip install -r requirements-mcp.txt -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m compileall -q skills tests
python skills/cobsidian/scripts/validate_skill.py skills/cobsidian
python skills/cobsidian/scripts/scan_vault.py examples --json
python skills/cobsidian/scripts/find_duplicates.py examples
python skills/cobsidian/scripts/validate_notes.py examples
git diff --check main...HEAD
git status --short --branch
```

Expected: all commands exit `0`; worktree is clean; all v0.4.0 and v0.5.0 tests pass.

- [ ] **Step 2: Run four fresh-agent forward tests**

Use `examples/demo-vault` and verify file hashes before and after each dry-run.

1. Chinese ambiguous teardown request: expanded `整理判读`, no more than two recommended modes, no writes.
2. English explicit capture request: compact Knowledge Read, no writes.
3. Explicit `off`: no conversational Knowledge Read block, complete JSON retained, no writes.
4. MCP-only request: `mcp-readonly`, `ready=false`, write-capability blocked reason, no write claim.

- [ ] **Step 3: Request independent code review**

Review `main...HEAD` for behavior regressions, trigger overreach, reference duplication, enum/config drift, MCP write exposure, and missing tests. Fix every Critical or Important issue with a failing regression test before proceeding.

- [ ] **Step 4: Re-run the complete gate after review fixes**

Repeat Step 1 against the final commit.

- [ ] **Step 5: Re-score Cobsidian using the agreed rubric**

Score each category from 0 to 10 with evidence:

| Category | Evidence required |
|---|---|
| Trigger accuracy | metadata and bilingual routing tests |
| Adaptability | mode references, host capability degradation, entry-point parity |
| Safety | scan-before-write, dry-run zero writes, no MCP write tool, preflight blocked reasons |
| Engineering quality | tests, compile, CI-ready validation, deterministic contracts |
| Product maturity | installation, documentation, compatibility, real-user and long-term evidence still missing |

Report both the weighted score and remaining deductions. Do not award points for unverified behavior.

- [ ] **Step 6: Commit verification-driven fixes only if needed**

Use focused commit messages that identify the repaired contract. If no files change, do not create an empty commit.

## Completion Boundary

This plan ends with a clean, reviewed, PR-ready `feat/v0.5.0-adaptive-workflow` branch and an evidence-backed reassessment. Publishing a GitHub release, tagging `v0.5.0`, and replacing the locally installed skill require the normal branch-completion choice after implementation.
