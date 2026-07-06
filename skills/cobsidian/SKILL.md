---
name: cobsidian
description: Use when Codex needs to turn conversations, study material, logs, project analysis, or summaries into an Obsidian vault while checking duplicate notes, choosing create vs append, adding wiki links, suggesting backlinks, and preserving Markdown note style.
---

# Cobsidian

## Core Principle

Maintain the vault as a linked knowledge system. Do not just generate a standalone Markdown file.

## Workflow

1. Identify the user's vault path and target topic.
2. Search existing notes before writing.
3. Decide one of:
   - create a new note
   - append to an existing note
   - split into multiple notes
   - only report duplicates and ask before editing
4. Write concise Markdown with stable headings.
5. Add relevant `[[wiki links]]` to existing notes.
6. Add a `Related notes` section when useful.
7. Run validation or at least report what was checked.

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

