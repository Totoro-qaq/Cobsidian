# Index Mode

## When to Use

Use `index` for a topic map, learning path, knowledge hub, or navigation layer that connects multiple durable notes. It organizes existing knowledge and explicitly proposed child notes rather than expanding every topic inline.

## Required Inputs

Identify the hub topic, intended reader or path, existing targets found in the vault, missing areas, ordering principle, and the scope boundary that prevents an unbounded map.

## Default Knowledge Read

- Default depth: `deep`
- Default granularity: `multi-note`

Keep the default evidence at `conversation`; enumerating notes does not upgrade evidence unless their relevant content is actually read.

## Recommended Note Shape

Create one named hub note with `Purpose`, `Start Here`, `Core Concepts`, `Projects or Applications`, `Learning Path`, `Open Questions`, and `Related Indexes`. Distinguish confirmed existing targets from proposed notes that do not yet exist.

## Append, Single-Note, and Split Criteria

- **Append** when an existing hub note already owns the same topic boundary and can absorb the new navigation links.
- **Single-note** when the task only improves one hub and no independent child content must be created.
- **Split** when missing topics deserve independently maintainable notes; identify the hub note first and keep all proposed links distinguishable from existing targets.

## Evidence Rules

Start at `conversation`. Upgrade to `source-grounded` only after reading the relevant target notes or source materials. Use `verified` only after link validation and another concrete check confirm the proposed map.

## Mode-Specific Validation

Verify that the hub note has a clear boundary, each emitted wiki link resolves to a confirmed note, proposed notes are not represented as existing, and navigation has no isolated or circular dead ends.

## Completion Report Additions

Report the hub note, existing targets linked, proposed child notes, missing targets, ordering rationale, and the result of backlink and navigation validation.
