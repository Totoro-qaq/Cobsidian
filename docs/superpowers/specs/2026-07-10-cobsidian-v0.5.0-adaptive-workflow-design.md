# Cobsidian v0.5.0 Adaptive Workflow Design

## Context

Cobsidian v0.4.0 provides a safe, local workflow for turning conversations and source material into linked Obsidian knowledge. Its core strengths are the scan-before-write rule, dry-run-first behavior, duplicate avoidance, backlink validation, bilingual mode handling, and a read-only MCP surface.

The current skill is still less adaptable than mature workflow systems in three ways:

1. The main `SKILL.md` contains routing, mode descriptions, workflow rules, and completion rules in one file.
2. Host behavior is documented mainly as installation guidance instead of an explicit capability and degradation contract.
3. Dry-run reports the proposed write but does not expose a stable, machine-readable explanation of organization depth, note granularity, evidence quality, or host readiness.

v0.5.0 addresses these gaps without turning Cobsidian into a general agent framework.

## Product Boundary

Cobsidian remains a single Agent Skill with one purpose:

> Turn AI conversations and source material into maintainable, linked Obsidian knowledge, safely.

The following rules remain non-negotiable:

- Resolve the target vault before any vault operation.
- Scan existing notes before proposing a write.
- Prefer append or merge over creating near-duplicates.
- Use dry-run by default unless the user explicitly opts out.
- Only create wiki links to notes confirmed to exist.
- Never claim a scan, write, or validation that the active host could not perform.

## Goals

1. Make `SKILL.md` a concise, host-neutral router and safety contract.
2. Move mode-specific execution guidance into seven on-demand references.
3. Define host behavior through capability levels rather than product-name assumptions.
4. Add a structured `knowledge_read` object to dry-run results.
5. Add a structured `preflight` object that reports completed checks and host readiness.
6. Support `auto`, `always`, and `off` presentation policies for Knowledge Read.
7. Preserve all v0.4.0 safety, retrieval, MCP compatibility, and zero-write behavior.

## Non-Goals

v0.5.0 will not add:

- embedding models or vector databases;
- an MCP write tool;
- multi-agent scheduling or delegation;
- automatic web research;
- separate skills for each note mode;
- mandatory vault metadata files;
- automatic inference implemented as a brittle keyword classifier;
- host-specific absolute paths or private user settings.

## Architecture

The skill remains one installable unit. The main skill routes to mode and host references, while deterministic Python modules produce the shared dry-run contract.

```text
skills/cobsidian/
|-- SKILL.md
|-- mcp_server.py
|-- references/
|   |-- modes/
|   |   |-- learning.md
|   |   |-- project.md
|   |   |-- review.md
|   |   |-- comparison.md
|   |   |-- index.md
|   |   |-- capture.md
|   |   `-- dissection.md
|   |-- hosts/
|   |   |-- codex.md
|   |   |-- claude-code.md
|   |   |-- cursor.md
|   |   |-- hermes.md
|   |   `-- mcp.md
|   |-- preflight.md
|   |-- backlink-policy.md
|   |-- markdown-style.md
|   `-- note-types.md
`-- scripts/
    |-- knowledge_read.py
    |-- preflight.py
    |-- dry_run.py
    `-- existing scan, duplicate, retrieval, and validation scripts
```

### Main Skill Contract

`SKILL.md` retains only information required on every invocation:

- trigger and language behavior;
- the scan-before-write Iron Law;
- vault resolution order;
- concise mode routing;
- Knowledge Read display behavior;
- common workflow and write rules;
- fail-closed behavior;
- completion report requirements;
- direct links to mode, host, and shared policy references.

It does not repeat mode-specific note templates, host-specific tool names, or long examples.

### Mode Reference Contract

Each mode reference contains the same required sections:

1. `When to use`
2. `Required inputs`
3. `Default Knowledge Read`
4. `Recommended note shape`
5. `Append, single-note, and split criteria`
6. `Evidence rules`
7. `Mode-specific validation`
8. `Completion report additions`

The seven canonical modes remain:

| Mode | Default depth | Default granularity | Primary purpose |
|---|---|---|---|
| `learning` | `standard` | `single-note` | Concepts, courses, papers, videos, and explanations |
| `project` | `deep` | `single-note` | Repositories, architecture, implementation, and operations |
| `review` | `deep` | `single-note` | Failures, incidents, experiments, and lessons |
| `comparison` | `standard` | `single-note` | Tool, model, database, framework, and architecture choices |
| `index` | `deep` | `multi-note` | Topic maps, learning paths, and hub notes |
| `capture` | `capture` | `single-note` | Low-friction temporary capture |
| `dissection` | `deep` | `multi-note` | Internals of tools, repos, skills, prompts, and workflows |

Evidence never defaults to `source-grounded` merely because a mode normally benefits from sources. It starts as `conversation` and is upgraded only when the host actually reads source material or completes verification.

## Knowledge Read

Knowledge Read is a structured pre-write explanation. Chinese conversations label it `整理判读`; English conversations label it `Knowledge Read`. It is shown in the agent conversation or dry-run result and is never inserted into note content.

### Schema

```json
{
  "mode": "dissection",
  "mode_explicit": false,
  "recommended_modes": [],
  "depth": "deep",
  "granularity": "multi-note",
  "evidence": "source-grounded",
  "display_policy": "auto",
  "display_style": "expanded"
}
```

Allowed values are:

- `mode`: one of the seven canonical modes, or `null` when unresolved;
- `recommended_modes`: zero to two canonical modes, populated only when `mode` is unresolved;
- `depth`: `capture`, `standard`, or `deep`;
- `granularity`: `append`, `single-note`, or `multi-note`;
- `evidence`: `conversation`, `source-grounded`, or `verified`;
- `display_policy`: `auto`, `always`, or `off`;
- `display_style`: `compact`, `expanded`, or `hidden`.

Mode defaults are applied before duplicate resolution. If the create/append decision resolves to append, the actual granularity becomes `append`. Explicit `single-note` or `multi-note` input is retained for new-note planning.

Evidence levels have concrete meanings:

- `conversation`: only the user-provided conversation or pasted material was used;
- `source-grounded`: the active host actually read referenced files, pages, logs, or source code;
- `verified`: source-grounded material was additionally checked through tests, validation, or an equivalent external result.

### Display Policy

Knowledge Read is always computed. Only its conversational presentation is optional.

- `always` produces `expanded`.
- `off` produces `hidden`, while preserving the complete JSON object.
- `auto` produces `expanded` when any of these conditions is true:
  - the mode was inferred rather than explicitly selected;
  - depth is `deep`;
  - granularity is `multi-note`;
  - evidence is `source-grounded` or `verified`.
- Otherwise, `auto` produces `compact`.

The configuration key is:

```yaml
interaction:
  knowledge_read: auto
```

Invalid values are rejected with a clear error. A conversational instruction such as "always show the organization read" or "hide the organization read" may override the configured policy for one request.

## Host Capability Contract

Host references describe how to detect and use available capabilities. They do not assume a product always exposes a specific tool.

Four capability levels are supported:

| Level | Scan | Dry-run | Agent write | Validate | Expected behavior |
|---|---:|---:|---:|---:|---|
| `full-local` | yes | yes | yes | yes | Complete workflow after approval |
| `filesystem-only` | yes | yes | yes | yes | Use local scripts and filesystem tools without MCP |
| `mcp-readonly` | yes | yes | no | yes | Return an approved change plan; never claim a write |
| `chat-only` | no | no | no | no | Return a portable draft or ask for a usable host/path |

Host references cover Codex, Claude Code, Cursor, Hermes, and generic MCP hosts. Each reference must:

- tell the agent to inspect actual available tools first;
- map those tools to one capability level;
- identify the supported scan, dry-run, write, and validation path;
- describe the correct degradation path;
- avoid hardcoded user paths and unstable product-specific promises.

## Preflight

The dry-run payload adds a preflight object:

```json
{
  "vault_resolved": true,
  "existing_notes_scanned": true,
  "duplicate_check_completed": true,
  "backlink_check_completed": true,
  "mode_selected": true,
  "capability_level": "filesystem-only",
  "write_policy": "dry-run",
  "ready": true,
  "blocked_reasons": []
}
```

`ready` means the active host can proceed to an approved write after dry-run. It does not mean a write already happened.

- `full-local` and `filesystem-only` may be ready after all checks complete.
- `mcp-readonly` is not ready to write and reports `write_capability_unavailable`.
- `chat-only` is not ready and reports missing scan and write capabilities.
- Any missing vault, scan, duplicate check, or backlink check makes readiness false.
- An unresolved mode makes readiness false and reports `mode_unresolved`.

The preflight reference explains these semantics to host adapters and completion reports.

## Data Flow

```text
Receive material
  -> detect host capabilities
  -> resolve vault
  -> scan existing notes
  -> select or infer one mode
  -> load only that mode reference
  -> build Knowledge Read
  -> compute create/append decision, duplicate risks, and backlinks
  -> build preflight
  -> present Knowledge Read according to policy
  -> request or consume write approval
  -> write only when the host supports it
  -> validate and report actual changes
```

Mode inference remains an agent responsibility guided by the routing table. Python validates canonical values and applies defaults; it does not implement a keyword classifier.

## CLI and MCP Changes

`dry_run.py` gains optional arguments for:

- mode explicitness;
- depth;
- granularity;
- evidence;
- up to two recommended modes when the primary mode is unresolved;
- capability level;
- one-request Knowledge Read policy override.

Programmatic callers may omit these fields. The module applies mode defaults, preserves v0.4.0 call compatibility, and rejects invalid enum values.

`cobsidian_dry_run` exposes the same optional fields. MCP defaults to `mcp-readonly`; local CLI defaults to `filesystem-only`.

The MCP server remains read-only. No registered tool writes to the vault.

## Error Handling

The workflow fails closed:

- Missing or invalid vault: report the path/config issue and request one corrected input.
- Unresolved mode: return an expanded Knowledge Read and recommend at most two relevant modes.
- Invalid mode or enum: reject the request; do not silently substitute another value.
- Missing scan capability: do not produce a create/append claim.
- Unresolved mode: keep the write decision provisional, set readiness false, and return no more than two canonical recommendations.
- Missing write capability: return a plan with `ready=false` and an explicit blocked reason.
- Validation failure after an external write: report the actual files changed and the validation failure.
- Missing mode or host reference: stop with a packaging error rather than falling back to invented behavior.

## Compatibility

- Existing v0.4.0 dry-run callers continue to work without new arguments.
- Existing response fields remain unchanged; `knowledge_read` and `preflight` are additive.
- Existing configuration files remain valid because `interaction.knowledge_read` defaults to `auto`.
- Existing static and paginated MCP resources remain unchanged.
- Existing backlink, duplicate, scan, and validation semantics remain unchanged.
- English and Chinese interactions use the same canonical mode and enum values.

## Documentation

Update English and Chinese documentation with:

- the adaptive workflow model;
- Knowledge Read examples and display settings;
- capability-level degradation behavior;
- the distinction between internal computation and optional conversational display;
- v0.5.0 configuration and compatibility notes.

The README remains concise and links to detailed mode, host, and preflight references.

## Testing Strategy

### Structural Contracts

- All seven mode references exist and contain the required sections.
- All five host references exist and contain capability detection and degradation sections.
- `SKILL.md` links to the mode, host, and preflight references.
- The main skill does not duplicate full mode templates or host-specific setup instructions.

### Knowledge Read Contracts

- Each canonical mode receives the approved default depth and granularity.
- Evidence defaults to `conversation` unless explicitly upgraded.
- `auto`, `always`, and `off` produce the approved display styles.
- `off` preserves the full JSON object.
- Invalid enum values fail clearly.
- Unresolved mode accepts no more than two canonical recommendations and sets preflight readiness false.
- Chinese and English presentation labels map to the same canonical values.

### Preflight Contracts

- All four capability levels produce the approved readiness result.
- `mcp-readonly` and `chat-only` never report write readiness.
- Missing checks add deterministic blocked reasons.
- Dry-run continues to return `writes: []`.

### Entry-Point Parity

- CLI, shared Python functions, and MCP return equivalent Knowledge Read fields for equivalent inputs.
- MCP defaults to `mcp-readonly`.
- Local CLI defaults to `filesystem-only`.
- Existing v0.4.0 entry-point tests remain green.

### Forward Tests

Use fresh agents to verify:

1. Chinese ambiguous source-dissection request recommends no more than two modes and uses an expanded `整理判读`.
2. English explicit capture request uses a compact Knowledge Read.
3. An `off` request hides the conversational block while retaining JSON.
4. An MCP-only scenario reports the read-only degradation path and never claims a write.
5. All forward tests leave the example vault unchanged when dry-run is requested.

## Acceptance Criteria

v0.5.0 is implementation-complete when:

- the approved file architecture exists;
- the main skill acts as a concise router;
- seven mode and five host references satisfy their contracts;
- dry-run and MCP expose additive `knowledge_read` and `preflight` objects;
- `interaction.knowledge_read` is enforced as `auto`, `always`, or `off`;
- all v0.4.0 tests and new v0.5.0 tests pass;
- fresh-agent forward tests confirm bilingual presentation and zero writes;
- an independent review finds no unresolved Critical or Important issue;
- Cobsidian is rescored against trigger accuracy, adaptability, safety, engineering quality, and product maturity.
