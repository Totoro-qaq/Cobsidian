---
name: cobsidian
description: >-
  Use when a user asks to organize, save, compare, review, map, or dissect
  conversations and source material into an Obsidian vault or Markdown
  knowledge base, including Chinese requests about 知识库, 笔记, 双链,
  学习模式, 项目模式, 复盘模式, 对比模式, 索引模式, 捕获模式, or 拆解模式.
---

# Cobsidian

## Core Principle

Maintain the vault as a linked knowledge system. Do not just generate a standalone Markdown file.

## Iron Law

```text
NEVER WRITE TO THE VAULT WITHOUT SEARCHING EXISTING NOTES FIRST.
```

Dry-run is the default safe path. Skip it only when the user explicitly says to write immediately; the scan and duplicate checks still apply.

## Response Language

Match the user's language for mode selection, clarification questions, Knowledge Read, and completion reports.

- Chinese request -> Chinese mode names and `整理判读`.
- English request -> English mode names and `Knowledge Read`.
- Mixed-language request -> use the dominant user language and include canonical IDs when useful.

## Vault Resolution

Resolve the target vault in this order:

1. Explicit vault path in the user's request.
2. `cobsidian.config.yml` with `vault.path`.
3. MCP host configuration through `COBSIDIAN_CONFIG`.
4. MCP host configuration through `COBSIDIAN_VAULT`.

Do not guess a private vault path. If no valid vault path is available, ask for one concise input: the vault path or the config path. If a supplied path is invalid, report it and request a corrected vault or config path before writing.

## Mode Routing

| Canonical mode | Use for | Load |
|---|---|---|
| `learning` / 学习 | Concepts, courses, papers, videos, explanations | [learning](references/modes/learning.md) |
| `project` / 项目 | The user's repository, architecture, implementation, operations | [project](references/modes/project.md) |
| `review` / 复盘 | Incidents, failures, experiments, lessons, corrective actions | [review](references/modes/review.md) |
| `comparison` / 对比 | Requirements-based evaluation and decisions | [comparison](references/modes/comparison.md) |
| `index` / 索引 | Topic maps, learning paths, hub notes | [index](references/modes/index.md) |
| `capture` / 捕获 | Low-friction temporary capture | [capture](references/modes/capture.md) |
| `dissection` / 拆解 | Internals of tools, repos, frameworks, prompts, workflows | [dissection](references/modes/dissection.md) |

- Explicit mode -> load only its mode reference.
- Clear inferred mode -> state it and load only its mode reference.
- Ambiguous mode -> recommend at most two modes with contextual reasons, then ask one concise question; do not dump all seven.
- Do not combine mode references unless the user explicitly requests separate outputs with separate mode decisions.

## Host Routing

Detect the host's actual tools before loading only the matching host reference. Product names select invocation mappings, never capability levels.

- [Codex](references/hosts/codex.md)
- [Claude Code](references/hosts/claude-code.md)
- [Cursor](references/hosts/cursor.md)
- [Hermes](references/hosts/hermes.md)
- [Generic MCP host](references/hosts/mcp.md)

Map observed tools to `full-local`, `filesystem-only`, `mcp-readonly`, or `chat-only`. Use [preflight](references/preflight.md) for readiness and degradation. Never load multiple host references speculatively.

## Knowledge Read

Knowledge Read (`整理判读`) is always computed and remains in structured dry-run output. `auto`, `always`, and `off` change conversational presentation only:

- `auto`: compact for simple explicit work; expanded for inferred, deep, multi-note, or source-grounded work.
- `always`: expanded.
- `off`: hidden in conversation while the complete object remains in JSON.

Mode defaults apply before duplicate resolution; an append decision changes granularity to `append`. Evidence starts at `conversation`, becomes `source-grounded` only after source material is actually read, and becomes `verified` only after an additional concrete check.

## Common Workflow

1. Detect host tools, map the capability level, and load one host reference.
2. Resolve the vault and target topic.
3. Scan existing notes and complete duplicate and backlink checks.
4. Select or infer one mode and load one mode reference.
5. Compute Knowledge Read and decide create, append, split, or report-only.
6. Produce dry-run output and evaluate preflight.
7. Request or consume approval; write only through an available approved path.
8. Validate actual changes and report only completed actions.

## Write Rules

- Preserve the vault's existing naming and organization style.
- Prefer append or merge over creating a near-duplicate.
- Prefer durable concepts over chat transcript summaries.
- Keep private paths, tokens, account names, and raw logs out of generic notes unless explicitly requested for local operational records.
- Add `[[wiki links]]` only to notes confirmed to exist; report missing targets instead of creating broken links.
- Do not fabricate sources, filenames, scans, writes, or validation results.
- Use stable headings and keep each note responsible for one maintainable knowledge boundary.

## Red Flags

Stop and reconsider when any of these thoughts appear:

- "This topic is obviously new, so scanning is unnecessary." Scan anyway.
- "The user said write, so dry-run is implicitly waived." Only an explicit opt-out waives dry-run.
- "The mode is unclear, so list every mode." Recommend no more than two contextual options.
- "This product usually has filesystem access." Detect actual tools and permissions first.
- "`off` means Knowledge Read need not be computed." It hides presentation only.
- "The host cannot perform the action, but the report can describe it as done." Report the blocked reason and degradation path instead.

## Helper Scripts

- `scripts/scan_vault.py`: summarize notes, titles, tags, and wiki links.
- `scripts/find_duplicates.py`: detect duplicate or similar note titles.
- `scripts/suggest_backlinks.py`: suggest related existing notes.
- `scripts/validate_notes.py`: report missing wiki links and hygiene issues.
- `scripts/dry_run.py`: return the zero-write plan, Knowledge Read, and preflight.
- `scripts/knowledge_read.py`: validate mode defaults, evidence, granularity, and display policy.
- `scripts/preflight.py`: derive readiness and deterministic blocked reasons.

Use `--config cobsidian.config.yml` when project configuration supplies vault, threshold, backlink, validation, or interaction settings.

Read [note types](references/note-types.md) for shared note-shape guidance, [backlink policy](references/backlink-policy.md) for links, and [Markdown style](references/markdown-style.md) for formatting.

## Completion Report

End with:

- files created or modified, or an explicit no-write result
- create, append, split, or report-only decision
- selected mode, depth, granularity, and evidence level
- capability level, preflight readiness, and every blocked reason
- duplicate checks and backlink decisions
- validation result, or the exact reason validation was unavailable
