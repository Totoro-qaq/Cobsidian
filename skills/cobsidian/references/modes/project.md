# Project Mode

## When to Use

Use `project` to document the user's project, including its goals, repository structure, architecture, implementation, operations, and current decisions. Use `dissection` when studying another system mainly to extract reusable mechanisms rather than maintain project truth.

## Required Inputs

Identify the project boundary, current objective, available repository or operational evidence, target audience, and whether the note describes current state, intended state, or both.

## Default Knowledge Read

- Default depth: `deep`
- Default granularity: `single-note`

Keep the default evidence at `conversation`; repository access alone does not upgrade evidence until relevant files are actually read.

## Recommended Note Shape

Use `Context`, `Goals`, `Current State`, `Architecture`, `Components`, `Data Flow`, `Implementation Decisions`, `Operational Commands`, `Risks`, `Next Steps`, `Evidence`, and `Related Notes`. Clearly label current behavior separately from proposals.

## Append, Single-Note, and Split Criteria

- **Append** when an existing project note owns the same component, decision, milestone, or operational topic.
- **Single-note** when the project overview and active decisions remain navigable under one stable title.
- **Split** when architecture, operations, decision records, or major components have independent owners and update cycles; retain an overview that links the parts.

## Evidence Rules

Start at `conversation`. Upgrade to `source-grounded` only after reading the relevant code, configuration, logs, or project records. Use `verified` only after tests, builds, commands, or equivalent checks confirm the documented behavior.

## Mode-Specific Validation

Verify that paths and component names exist, commands match the current project, current and target states are distinguishable, and risks are not presented as completed work. Confirm internal links against the vault.

## Completion Report Additions

Report the project scope, current-versus-target distinctions, files or records examined, decisions updated, commands verified, and unresolved operational or architectural risks.
