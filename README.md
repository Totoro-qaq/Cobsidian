# Cobsidian

Cobsidian is an agent workflow skill for turning conversations, study material, logs, and project analysis into an Obsidian knowledge base.

It focuses on durable knowledge-base maintenance rather than one-off Markdown generation:

- decide whether to create a new note or append to an existing one
- scan for duplicate or overlapping notes before writing
- add useful `[[wiki links]]` and backlink suggestions
- keep note names, sections, tags, and related-note blocks consistent
- validate missing links and obvious vault hygiene issues

## Status

Early MVP. The first version is a Codex/agent skill plus small Python utilities. It is not an Obsidian plugin.

## Repository Layout

```text
Cobsidian/
├── skills/cobsidian/          # Agent skill
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
├── examples/                  # Example note outputs
├── .github/workflows/         # CI validation
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Install The Skill

Copy the skill folder into your agent's skill directory:

```bash
cp -r skills/cobsidian ~/.codex/skills/cobsidian
```

On Windows PowerShell:

```powershell
Copy-Item -Recurse -Force .\skills\cobsidian "$env:USERPROFILE\.codex\skills\cobsidian"
```

## Basic Usage

Ask your agent to use Cobsidian when you want to write into an Obsidian vault:

```text
Use Cobsidian to turn this conversation into an Obsidian learning note.
Check whether it should create a new note or append to an existing one.
Add useful wiki links and report possible duplicates.
```

Run helper scripts directly when you need a deterministic vault check:

```bash
python skills/cobsidian/scripts/scan_vault.py /path/to/vault --json
python skills/cobsidian/scripts/find_duplicates.py /path/to/vault
python skills/cobsidian/scripts/validate_notes.py /path/to/vault
```

## What Cobsidian Is Not

- Not a cloud sync service
- Not an Obsidian plugin
- Not a vector database
- Not an automatic writer that should modify a vault without review

## License

MIT. See [LICENSE](LICENSE).

