# Cobsidian Modes

[简体中文](modes.zh-CN.md)

Modes describe the user outcome Cobsidian should produce. They affect organization depth and the mode-level note plan, while the dry-run decision separately records whether a machine may create, append, or must stop.

## Natural-language Routing

Cobsidian uses natural-language routing; users do not need to memorize mode IDs.

- Explicit mode: use that canonical mode and report it.
- Clear request: infer one mode from the user's goal and state the choice.
- Ambiguous request: leave the mode unresolved and recommend at most two relevant modes.
- Do not show all seven modes as a generic picker when one or two contextual choices are enough.

`recommended_modes` is only used while `mode` is unresolved. It contains zero, one, or two canonical mode IDs and never substitutes an unsupported value.

## Outcome Guide

| User outcome | Canonical mode | Default depth | Default granularity | Detailed contract |
|---|---|---|---|---|
| Understand a concept, course, paper, video, or technical explanation | `learning` | `standard` | `single-note` | [Learning](../skills/cobsidian/references/modes/learning.md) |
| Maintain context, architecture, implementation, or operations for your project | `project` | `deep` | `single-note` | [Project](../skills/cobsidian/references/modes/project.md) |
| Explain an incident, failed experiment, decision, or lesson | `review` | `deep` | `single-note` | [Review](../skills/cobsidian/references/modes/review.md) |
| Compare options and make tradeoffs visible | `comparison` | `standard` | `single-note` | [Comparison](../skills/cobsidian/references/modes/comparison.md) |
| Build a topic hub, knowledge map, learning path, or navigation page | `index` | `deep` | `multi-note` | [Index](../skills/cobsidian/references/modes/index.md) |
| Save useful rough material with minimal interruption | `capture` | `capture` | `single-note` | [Capture](../skills/cobsidian/references/modes/capture.md) |
| Extract internals and reusable patterns from a tool, repo, skill, prompt, or workflow | `dissection` | `deep` | `multi-note` | [Dissection](../skills/cobsidian/references/modes/dissection.md) |

These defaults feed Knowledge Read. Evidence still begins at `conversation`. Evidence upgrades use host-completed facts: `source-grounded` requires `source_read_completed=true`, while `verified` requires both `source_read_completed=true` and `verification_completed=true`. A mode or user claim never upgrades evidence by itself.

## Machine Action And Note Plan

The dry-run machine action and the mode-level note plan are different contracts:

- `decision.action`: `create | append | blocked`
- mode-level note plan: `single-note | multi-note | report-only`

A split request is reported as a `multi-note` plan, not as a fourth machine action. Requested `granularity=append` is valid only with `decision.action=append`; when duplicate resolution selects an existing note, Knowledge Read always forces append granularity. `report-only` describes a no-write user outcome; it is not a Knowledge Read `granularity` enum.

## What Users Receive

- `learning`: a durable explanation organized for later recall.
- `project`: current project context, implementation evidence, risks, and next steps.
- `review`: causes, decisions, lessons, and follow-up actions.
- `comparison`: a concise conclusion backed by explicit tradeoffs.
- `index`: navigable links and a useful path through existing notes.
- `capture`: a short retrievable record with deferred cleanup made clear.
- `dissection`: entry points, internal flow, evidence, reusable patterns, and limits.

The detailed headings, evidence rules, split criteria, and validation additions live only in [`skills/cobsidian/references/modes/`](../skills/cobsidian/references/modes/). This page describes user-visible outcomes and routing rather than duplicating operational prompts.
