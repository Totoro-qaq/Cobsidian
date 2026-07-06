# Cobsidian

English | [简体中文](docs/README.zh-CN.md)

Cobsidian is an agent workflow skill for maintaining an Obsidian knowledge base.

It helps AI agents turn conversations, study material, logs, documents, and project analysis into durable Markdown notes with duplicate checks, wiki links, backlink suggestions, and basic vault validation.

It is designed for knowledge-base maintenance, not one-off Markdown generation.

## Why Cobsidian

AI conversations often produce useful knowledge, but the output usually stays trapped in chat history or becomes isolated Markdown files. Cobsidian gives an agent a repeatable workflow:

```text
input material
-> search existing notes
-> decide create vs append vs split
-> write clean Markdown
-> add useful [[wiki links]]
-> suggest backlinks
-> validate basic vault hygiene
```

## Features

- Create learning notes, project notes, comparison notes, and index notes.
- Check existing notes before writing to reduce duplicates.
- Suggest `[[wiki links]]` and related-note sections.
- Validate missing wiki-link targets.
- Detect exact and similar note titles.
- Keep note structure concise and reusable.
- Avoid writing private paths, secrets, or raw chat transcripts by default.

## Status

Early MVP.

The first version is a Codex-compatible agent skill plus small Python utilities. It is not an Obsidian plugin, cloud sync service, or vector database.

## Install

Copy the skill folder into your agent's skill directory:

```bash
cp -r skills/cobsidian ~/.codex/skills/cobsidian
```

On Windows PowerShell:

```powershell
Copy-Item -Recurse -Force .\skills\cobsidian "$env:USERPROFILE\.codex\skills\cobsidian"
```

## Agent Usage

Ask your agent to use Cobsidian when you want to write into an Obsidian vault:

```text
Use Cobsidian to turn this conversation into an Obsidian learning note.
Check whether it should create a new note or append to an existing one.
Add useful wiki links and report possible duplicates.
```

More examples:

```text
Use Cobsidian to summarize these logs into my Obsidian vault.
Preserve only reusable lessons, check for existing related notes, and add backlinks.
```

```text
Use Cobsidian to compare these two project attempts and write a comparison note.
If a related note already exists, append instead of creating a duplicate.
```

## CLI Utilities

Run helper scripts when you need deterministic vault checks:

```bash
python skills/cobsidian/scripts/scan_vault.py /path/to/vault --json
python skills/cobsidian/scripts/find_duplicates.py /path/to/vault
python skills/cobsidian/scripts/suggest_backlinks.py /path/to/vault --file draft.md
python skills/cobsidian/scripts/validate_notes.py /path/to/vault
```

### `scan_vault.py`

Summarizes Markdown notes, titles, tags, and wiki links.

```bash
python skills/cobsidian/scripts/scan_vault.py examples --json
```

### `find_duplicates.py`

Finds exact and highly similar note titles.

```bash
python skills/cobsidian/scripts/find_duplicates.py examples
```

### `suggest_backlinks.py`

Suggests related notes for a draft or raw text.

```bash
python skills/cobsidian/scripts/suggest_backlinks.py examples --text "vector search and RAG evaluation"
```

### `validate_notes.py`

Reports missing wiki-link targets, duplicate titles, and empty notes.

```bash
python skills/cobsidian/scripts/validate_notes.py examples --strict
```

## Repository Layout

```text
Cobsidian/
├── skills/cobsidian/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/
│   │   ├── backlink-policy.md
│   │   ├── markdown-style.md
│   │   └── note-types.md
│   └── scripts/
├── examples/
├── docs/
├── .github/workflows/
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Workflow

When Cobsidian is used by an agent, the expected behavior is:

1. Identify the vault path and target topic.
2. Search existing notes before writing.
3. Decide whether to create, append, split, or ask before editing.
4. Write clean Markdown with stable headings.
5. Add useful wiki links and related-note references.
6. Run validation or report why validation was skipped.
7. Return a short change summary.

## Roadmap

- Better duplicate detection with configurable thresholds.
- Frontmatter support for vaults that use YAML metadata.
- Optional note templates.
- Configurable naming rules.
- Safer dry-run mode for proposed edits.
- Optional Obsidian plugin integration after the workflow stabilizes.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

Do not include private vault content, personal paths, API keys, unpublished notes, or screenshots from a private knowledge base.

## What Cobsidian Is Not

- Not an Obsidian plugin.
- Not a cloud sync service.
- Not a vector database.
- Not an automatic writer that should modify a vault without review.
- Not a replacement for human editorial judgment.

## License

MIT. See [LICENSE](LICENSE).
