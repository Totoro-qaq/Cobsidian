# Dissection Mode

## When to Use

Use `dissection` when the value comes from internals: source structure, runtime workflow, prompt behavior, framework mechanics, tool architecture, or reusable implementation patterns. An ordinary explanation remains `learning` unless internal mechanisms are central.

## Required Inputs

Identify the object of study, the internal question, accessible source or artifacts, relevant version, entry points, desired depth, and which reusable mechanisms matter to the user.

## Default Knowledge Read

- Default depth: `deep`
- Default granularity: `multi-note`

Keep the default evidence at `conversation`; selecting a source-oriented mode never proves that source material was actually read.

## Recommended Note Shape

Use an overview with `Object of Study`, `Purpose`, `Entry Points`, `Architecture or Flow`, `Core Mechanisms`, `Key Components`, `Reusable Patterns`, `Limits`, `Open Questions`, and `Related Notes`. Child notes should each own one independently reusable mechanism.

## Append, Single-Note, and Split Criteria

- **Append** when an existing teardown owns the same system version and the new finding extends one documented mechanism.
- **Single-note** when the studied system is small and its entry points, flow, and mechanisms remain coherent together.
- **Split** when components, prompts, protocols, or workflows have independent source trails or reuse value; keep an overview that links every child note.

## Evidence Rules

Start at `conversation`. Upgrade to `source-grounded` only after reading relevant source code, prompts, configuration, traces, or documentation. Use `verified` only after tests, execution traces, or equivalent checks confirm the described mechanism.

## Mode-Specific Validation

Verify entry points, call or data flow, component names, version assumptions, source locations, and claimed reusable patterns. Mark inferred behavior clearly and confirm all emitted wiki links against existing notes.

## Completion Report Additions

Report the studied system and version, entry points examined, mechanisms extracted, overview and child-note decisions, evidence level, verification performed, and unresolved internal questions.
