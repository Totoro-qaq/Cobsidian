# Review Mode

## When to Use

Use `review` for incidents, failures, experiments, missed goals, or completed work where the durable value is evidence-based learning and corrective action, not a generic project status summary.

## Required Inputs

Identify the reviewed event, expected outcome, actual outcome, available timeline and evidence, affected scope, known constraints, and the owner or status of follow-up actions.

## Default Knowledge Read

- Default depth: `deep`
- Default granularity: `single-note`

Keep the default evidence at `conversation` until logs, results, records, or validation output have actually been examined.

## Recommended Note Shape

Use `Context`, `Expected Outcome`, `Actual Outcome`, `Timeline`, `Evidence`, `Root Causes`, `Contributing Factors`, `Corrective Actions`, `Unresolved Questions`, and `Related Notes`. Separate observed facts from interpretations and future commitments.

## Append, Single-Note, and Split Criteria

- **Append** when the same review already exists and new evidence, action status, or corrected analysis belongs to it.
- **Single-note** when one event or experiment has one connected timeline, cause analysis, and action set.
- **Split** when independent incidents or experiments need separate evidence trails; link them from a shared review index instead of blending causes.

## Evidence Rules

Start at `conversation`. Upgrade to `source-grounded` only after reading logs, metrics, experiment output, tickets, or records. Use `verified` only when reproduction, tests, monitoring, or follow-up checks confirm the relevant conclusion. These are host-completed facts: submit `source_read_completed=true` for source grounding and both `source_read_completed=true` and `verification_completed=true` for verified evidence; mode choice or a user claim cannot set them.

## Mode-Specific Validation

Verify that Evidence, Root Causes, Corrective Actions, and Unresolved Questions remain distinct. Check chronology, action ownership, unsupported causal claims, known counterevidence, and links to confirmed project or incident notes.

## Completion Report Additions

Report the reviewed scope, evidence examined, root-cause confidence, corrective-action changes, unresolved questions, and every validation or reproduction step actually completed.
