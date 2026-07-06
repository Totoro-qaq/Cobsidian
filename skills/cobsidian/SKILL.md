---
name: cobsidian
description: Use when an agent needs to organize material into an Obsidian vault or Markdown knowledge base, including conversations, study notes, logs, source-code/framework/skill dissection, project reviews, comparisons, index notes, duplicate checks, wiki links, backlinks, or Chinese requests such as 整理到Obsidian/知识库/写成Markdown/补双链/反链/学习模式/项目模式/复盘模式/对比模式/索引模式/捕获模式/拆解模式.
---

# Cobsidian

## Core Principle

Maintain the vault as a linked knowledge system. Do not just generate a standalone Markdown file.

## Mode Selection

If the user explicitly selects a mode, use it. If no mode is selected, infer the smallest useful mode. If the mode is ambiguous and file edits are involved, ask briefly before writing.

| Mode | Chinese triggers | Use for |
|---|---|---|
| `learning` | 学习模式, 知识点整理, 学习笔记 | Concepts, courses, videos, papers, technical explanations. |
| `project` | 项目模式, 项目整理, 源码项目 | Project architecture, implementation notes, repo analysis, operational docs. |
| `review` | 复盘模式, 事故复盘, 实验复盘, 失败复盘 | Incidents, experiment results, failures, lessons learned. |
| `comparison` | 对比模式, 选型, 方案比较 | Tool choices, architecture options, model/database/framework comparisons. |
| `index` | 索引模式, 总览, 知识地图, 学习路线 | Topic maps, hub notes, learning paths, navigation pages. |
| `capture` | 捕获模式, 日常记录, 先记下来, daily capture | Lightweight daily capture before deeper organization. |
| `dissection` | 拆解模式, 源码拆解, 框架拆解, skill拆解 | Reverse engineering tools, repos, frameworks, agent systems, prompts, skills, workflows. |

## Workflow

1. Identify the user's vault path and target topic.
2. Search existing notes before writing.
3. Select or infer a mode.
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

## Helper Scripts

- `scripts/scan_vault.py`: summarize notes, titles, tags, and wiki links.
- `scripts/find_duplicates.py`: detect duplicate or similar note titles.
- `scripts/suggest_backlinks.py`: suggest related notes for a draft or target note.
- `scripts/validate_notes.py`: report missing wiki links and basic hygiene issues.

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
