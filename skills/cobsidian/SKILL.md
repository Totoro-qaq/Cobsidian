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

| Canonical mode | Representative cues | Use for | Load |
|---|---|---|---|
| `learning` / 学习 | teach me about / 这个概念讲一下 | Concepts and explanations | [learning](references/modes/learning.md) |
| `project` / 项目 | document this repo / 这个仓库帮我分析一下 | Project implementation and operations | [project](references/modes/project.md) |
| `review` / 复盘 | what went wrong / 失败复盘 | Evidence, causes, and corrective actions | [review](references/modes/review.md) |
| `comparison` / 对比 | which should I choose / 哪个更好 | Requirements-based decisions | [comparison](references/modes/comparison.md) |
| `index` / 索引 | learning path / 学习路线 | Maps, paths, and hub notes | [index](references/modes/index.md) |
| `capture` / 捕获 | just save this / 先记下来 | Low-friction temporary capture | [capture](references/modes/capture.md) |
| `dissection` / 拆解 | how does X work internally / 拆解这个产品为什么有效 / 这个怎么实现的 | Problem-to-outcome causal analysis, internal mechanics, horizontal peers, vertical evolution, and reusable advantages | [dissection](references/modes/dissection.md) |

- Explicit mode -> load only its mode reference.
- Clear inferred mode -> state it and load only its mode reference.
- Ambiguous mode -> recommend at most two modes with contextual reasons, then ask one concise question; do not dump all seven.
- Do not combine mode references unless the user explicitly requests separate outputs with separate mode decisions.

## Host Routing

Detect the host's actual tools before loading only the matching host reference. Product names select invocation mappings, never capability levels.

- [Codex](references/hosts/codex.md)
- [Claude Code](references/hosts/claude-code.md)
- [Kimi Code](references/hosts/kimi-code.md)
- [OpenCode](references/hosts/opencode.md)
- [Pi](references/hosts/pi.md)
- [Antigravity](references/hosts/antigravity.md)
- [GitHub Copilot CLI](references/hosts/github-copilot-cli.md)
- [Cursor](references/hosts/cursor.md)
- [Hermes](references/hosts/hermes.md)
- [Generic MCP host](references/hosts/mcp.md)

Map observed scan/write transport to `full-local`, `filesystem-only`, `mcp-readonly`, or `chat-only`. The historical `mcp-readonly` name means the transport-neutral effective read-only level, including local read-only operation without MCP. Report validation capability independently through `validation_available`; a write-capable host with no validation keeps its `full-local` or `filesystem-only` level and becomes not ready. Use [preflight](references/preflight.md) for readiness and degradation. Never load multiple host references speculatively.

## Knowledge Read

Knowledge Read (`整理判读`) is always computed and remains in structured dry-run output. `auto`, `always`, and `off` change conversational presentation only:

- `auto`: compact for simple explicit work; expanded for inferred, deep, multi-note, or source-grounded work.
- `always`: expanded.
- `off`: hidden in conversation while the complete object remains in JSON.

Mode defaults apply before duplicate resolution. A requested `granularity=append` is valid only when `decision.action=append`; an actual append decision always forces append granularity. Evidence starts at `conversation`. Evidence upgrades require host-completed facts: `source-grounded` requires `source_read_completed=true`, while `verified` requires both `source_read_completed=true` and `verification_completed=true`. Mode choice and user claims never set these facts automatically.

## Common Workflow

1. Detect host tools, map the scan/write capability level, report validation capability independently, and load one host reference.
2. Resolve the vault and target topic.
3. Scan existing notes, build note identities from filename, cleaned H1, frontmatter `title` and `aliases`, and prefix-free core titles, then complete duplicate and backlink checks across all identity candidates.
4. Select or infer one mode and load one mode reference.
5. Compute Knowledge Read and the mode-level note plan: `single-note | multi-note | report-only`; split means `multi-note`.
6. Produce dry-run output with `decision.action`: `create | append | blocked`, then evaluate preflight.
7. For local writes, prepare a deterministic patch preview with `write_executor.py prepare`, show the plan ID and diff, and require explicit confirmation of that exact plan ID.
8. Apply the confirmed plan atomically with `write_executor.py apply`; validate the result, retain the transaction record, and auto-roll back when the write introduces new validation warnings.
9. Report only completed actions. Use `write_executor.py rollback` with the exact transaction ID when the user requests a safe rollback.

## Write Rules

- Preserve the vault's existing naming and organization style.
- Use vault-relative paths in note content; never embed user-specific absolute paths.
- Prefer append or merge over creating a near-duplicate.
- Prefer durable concepts over chat transcript summaries.
- Local operational records still use minimum necessary disclosure; redact credentials, tokens, private identifiers, and unnecessary raw log content.
- Add `[[wiki links]]` only to notes confirmed to exist; report missing targets instead of creating broken links.
- Treat filename, cleaned H1, frontmatter title and aliases, and prefix-free core titles as one note identity when checking duplicates.
- Do not bypass the deterministic executor with a direct edit when its local Python path is available. A preview is not approval, and a plan ID is valid only while the target hash is unchanged.
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
- "Write exists, so missing validation means `mcp-readonly`." Keep the write transport level, set `validation_available=false`, and block readiness.

## Helper Scripts

- `scripts/scan_vault.py`: summarize notes, titles, tags, and wiki links.
- `scripts/note_identity.py`: derive filename, H1, frontmatter, alias, and prefix-free identity candidates.
- `scripts/find_duplicates.py`: detect duplicate or similar note titles.
- `scripts/suggest_backlinks.py`: suggest related existing notes.
- `scripts/validate_notes.py`: report missing wiki links and hygiene issues.
- `scripts/dry_run.py`: return the zero-write plan, Knowledge Read, and preflight.
- `scripts/write_executor.py`: preview, confirm, atomically apply, validate, and roll back local writes.
- `scripts/quality_eval.py`: measure duplicate precision/recall, backlink precision@k, target accuracy, and mode accuracy on labeled JSONL cases.
- `scripts/knowledge_read.py`: validate mode defaults, evidence, granularity, and display policy.
- `scripts/preflight.py`: derive readiness and deterministic blocked reasons.

Use `--config cobsidian.config.yml` when project configuration supplies vault, threshold, backlink, validation, or interaction settings.

Read [note types](references/note-types.md) for shared note-shape guidance, [backlink policy](references/backlink-policy.md) for links, and [Markdown style](references/markdown-style.md) for formatting.

## Completion Report

End with:

- files created or modified, or an explicit no-write result
- dry-run `decision.action`: `create | append | blocked`
- mode-level note plan: `single-note | multi-note | report-only`; report split as `multi-note`, not a machine action
- selected mode, depth, granularity, and evidence level
- capability level, preflight readiness, and every blocked reason
- duplicate checks and backlink decisions
- validation result, or the exact reason validation was unavailable
- write plan ID and transaction status for local writes, including whether validation triggered an automatic rollback
