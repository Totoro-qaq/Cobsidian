---
name: cobsidian
description: Use when the user wants to organize, save, or structure knowledge from conversations into an Obsidian vault or Markdown knowledge base. Covers study notes, project analysis, incident reviews, tool comparisons, topic maps, daily capture, and source dissection with duplicate checks, wiki-link suggestions, and dry-run planning. Also triggered by Chinese phrases: 整理到Obsidian, 知识库, 写成笔记, 记笔记, 帮我整理, 总结成笔记, 双链笔记, 知识点整理, 补双链, 学习模式, 项目模式, 复盘模式, 对比模式, 索引模式, 捕获模式, 拆解模式.
---

# Cobsidian

## Core Principle

Maintain the vault as a linked knowledge system. Do not just generate a standalone Markdown file.

## Iron Law

```text
NEVER WRITE TO THE VAULT WITHOUT SEARCHING EXISTING NOTES FIRST.
```

Dry-run is the default safe path. Skip it only when the user explicitly says to write immediately.

## Response Language

Match the user's language for mode selection, clarification questions, and completion reports.

- Chinese request -> Chinese mode names.
- English request -> English mode names.
- Mixed-language request -> use the dominant user language and include canonical mode IDs in backticks when helpful.

## Vault Resolution

Resolve the target vault in this order:

1. Explicit vault path in the user's request.
2. `cobsidian.config.yml` with `vault.path`.
3. MCP host configuration through `COBSIDIAN_CONFIG`.
4. MCP host configuration through `COBSIDIAN_VAULT`.

Do not guess a private vault path. If no valid vault path is available, ask for one concise input: the vault path or the config path. If a path is present but invalid, report the invalid path and ask for a corrected vault/config path before writing.

## Mode Selection

If the user explicitly selects a mode, use it and do not show the full mode menu. If no mode is selected, infer the smallest useful mode and state it before writing. If the mode is ambiguous and file edits are involved, introduce the modes briefly and ask one concise question before writing.

| Mode | English triggers | Chinese triggers | Use for |
|---|---|---|---|
| `learning` | learning mode, study note, explain, teach me about | 学习模式, 知识点整理, 学习笔记, 帮我学, 这个概念讲一下 | Concepts, courses, videos, papers, technical explanations. |
| `project` | project mode, repo analysis, architecture, document this repo | 项目模式, 项目整理, 源码项目, 这个仓库帮我分析一下 | Project architecture, implementation notes, repo analysis, operational docs. |
| `review` | review mode, retrospective, failure review, what went wrong | 复盘模式, 事故复盘, 实验复盘, 失败复盘, 总结教训 | Incidents, experiment results, failures, lessons learned. |
| `comparison` | comparison mode, compare, evaluate options, which should I choose | 对比模式, 选型, 方案比较, 哪个更好 | Tool choices, architecture options, model/database/framework comparisons. |
| `index` | index mode, map, learning path, give me an overview | 索引模式, 总览, 知识地图, 学习路线, 帮我画个知识图谱 | Topic maps, hub notes, learning paths, navigation pages. |
| `capture` | capture mode, daily capture, quick note, just save this | 捕获模式, 日常记录, 先记下来, 记一下, 帮我记笔记 | Lightweight daily capture before deeper organization. |
| `dissection` | dissection mode, teardown, source analysis, how does X work internally | 拆解模式, 源码拆解, 框架拆解, skill拆解, 这个怎么实现的 | Reverse engineering tools, repos, frameworks, agent systems, prompts, skills, workflows. |

## Interactive Mode Introduction

Do not assume the user has read the README or mode docs. Explain modes in the conversation when:

- the user is new to Cobsidian or asks what Cobsidian can do
- the user broadly asks to organize/write material into Obsidian without a clear note type
- the same material could reasonably become different note types
- the target edit would differ by mode, such as polished learning note vs rough daily capture

Skip the picker when the user already chose a mode, the mode is obvious, or the user asked for direct execution. In that case, state the inferred mode and continue:

```text
Mode: dissection / 拆解, because this is a framework or workflow teardown.
```

When the picker is needed, use the user's language.

English mode picker:

```text
Cobsidian can organize this in several modes:
- learning: concepts, courses, videos, papers
- project: repos, architecture, implementation, operations
- review: failures, incidents, experiments, lessons
- comparison: tool/model/database/architecture choices
- index: topic maps, learning paths, hub notes
- capture: quick rough notes for later cleanup
- dissection: internals of tools, frameworks, repos, skills, prompts

Choose one mode, or tell me to infer it.
```

中文模式选择：

```text
Cobsidian 可以按这些模式整理：
- 学习模式：概念、课程、视频、论文、技术解释
- 项目模式：仓库、架构、实现、运维记录
- 复盘模式：失败、事故、实验结果、经验教训
- 对比模式：工具、模型、数据库、架构选型
- 索引模式：主题地图、学习路线、导航页
- 捕获模式：先快速保存粗糙材料，后续再整理
- 拆解模式：拆解工具、框架、仓库、skill、提示词系统

选一个模式，或者告诉我由我推断。
```

## Workflow

1. Identify the user's vault path and target topic.
2. Search existing notes before writing.
3. Select, infer, or introduce the mode before writing.
4. Decide one of:
   - create a new note
   - append to an existing note
   - split into multiple notes
   - only report duplicates and ask before editing
5. Write concise Markdown with stable headings.
6. Add relevant `[[wiki links]]` to existing notes.
7. Add a `Related notes` section when useful.
8. Run validation or at least report what was checked.

## Write Rules

- Preserve the user's existing note naming style.
- Prefer durable concepts over chat transcript summaries.
- Keep private paths, tokens, account names, and raw logs out of generic notes unless the user explicitly wants local operational records.
- Do not fabricate sources, file names, or completed checks.
- If the same topic already exists, append or merge instead of creating a near-duplicate.

## Red Flags

Stop and reconsider if you catch yourself thinking:

- "This topic is obviously new, no need to scan." — Scan anyway. The Iron Law has no exceptions.
- "I will just create a fresh note and add links later." — Check first; there is probably an existing note to append to.
- "The user said write, so I will skip dry-run." — Only skip dry-run when the user **explicitly** says to skip it. "Write this" does not mean "skip safety checks."
- "This note is too small to need backlinks." — Even a one-paragraph capture note should link to related notes if they exist.
- "I already know the vault structure." — Vault state changes between sessions. Always re-scan.

## Common Mistakes

| Mistake | Correction |
|---|---|
| Creating a new note when a highly similar one exists | Run `find_duplicates.py` or scan first; prefer append |
| Dumping raw chat transcript as a note | Extract durable concepts; discard conversational noise |
| Adding `[[wiki links]]` to notes that do not exist in the vault | Only link to notes confirmed by scan; mention missing targets in the report |
| Hardcoding absolute paths in note content | Use relative references; never write `/Users/...` or `C:\...` into notes |
| Skipping the completion report | Always end with files changed, decision, duplicates, backlinks, validation |
| Writing in a different language than the user's request | Match the user's language; see Response Language rules |

## Helper Scripts

- `scripts/scan_vault.py`: summarize notes, titles, tags, and wiki links.
- `scripts/find_duplicates.py`: detect duplicate or similar note titles.
- `scripts/suggest_backlinks.py`: suggest related notes for a draft or target note.
- `scripts/validate_notes.py`: report missing wiki links and basic hygiene issues.
- `scripts/dry_run.py`: plan a write without changing files; reports create/append decision, duplicate risks, backlink suggestions, validation intent, and empty writes.

Use `--config cobsidian.config.yml` when the user has a project config with `vault.path`, thresholds, backlink limits, and validation preferences.

Read `references/note-types.md` when choosing the note shape.
Read `references/backlink-policy.md` when adding links.
Read `references/markdown-style.md` when formatting notes.

## Completion Report

End with:

- files created or modified
- create/append decision
- duplicate checks performed
- backlink suggestions added or skipped
- validation result or reason validation was not run
