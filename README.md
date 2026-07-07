# Cobsidian

English | [简体中文](docs/README.zh-CN.md)

[![validate](https://github.com/Totoro-qaq/Cobsidian/actions/workflows/validate.yml/badge.svg)](https://github.com/Totoro-qaq/Cobsidian/actions/workflows/validate.yml)
[![codeql](https://github.com/Totoro-qaq/Cobsidian/actions/workflows/codeql.yml/badge.svg)](https://github.com/Totoro-qaq/Cobsidian/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Cobsidian is an agent-agnostic workflow skill for maintaining an Obsidian knowledge base.

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
- Expose local MCP tools for read-only vault inspection and dry-run planning.

## Status

Early MVP.

The first version ships as a Codex-compatible skill plus small Python utilities, but the workflow is intentionally portable to Hermes, Claude Code, Cursor, and other coding agents that can read project instructions and run local commands.

It is not an Obsidian plugin, cloud sync service, or vector database.

## Install

See [INSTALL.md](INSTALL.md) for full setup, update, and uninstall instructions.
See [Integrations](docs/integrations.md) for Codex, Obsidian vault, MCP host, and other-agent setup notes.

### Codex Skill

```bash
mkdir -p ~/.agents/skills
cp -r skills/cobsidian ~/.agents/skills/cobsidian
```

On Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills" | Out-Null
Copy-Item -Recurse -Force .\skills\cobsidian "$env:USERPROFILE\.agents\skills\cobsidian"
```

Codex currently documents `$HOME/.agents/skills` for user skills. Some local or older Codex builds may scan `$HOME/.codex/skills`; use the skills directory shown by your Codex surface.

### Other Agents

For Hermes, Claude Code, Cursor, and other agents, use the same core workflow:

1. Point the agent to `skills/cobsidian/SKILL.md`.
2. Allow it to call the helper scripts in `skills/cobsidian/scripts/`.
3. Ask it to report create/append decisions, duplicate checks, backlink changes, and validation results.

See [Agent Compatibility](docs/agent-compatibility.md) and [Integrations](docs/integrations.md).

### MCP Server

Cobsidian also ships a local MCP server for hosts that support the Model Context Protocol.

```bash
python -m pip install -r requirements-mcp.txt
python skills/cobsidian/mcp_server.py
```

Use it as a local `stdio` server and configure `COBSIDIAN_CONFIG` or `COBSIDIAN_VAULT`.

See [MCP Server](docs/mcp-server.md).

## Agent Usage

See [Prompt Examples](examples/prompts.md) for copy-ready prompts.

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

## Before / After

Given existing notes:

```text
examples/demo-vault/
├── AI Conversations.md
├── Agent Workflows.md
└── Vector Search.md
```

Run a config-aware dry run:

```bash
python skills/cobsidian/scripts/dry_run.py examples/demo-vault \
  --topic "AI Conversations" \
  --mode learning \
  --text "AI chats should become linked notes with duplicate checks, backlinks, and agent workflows." \
  --json
```

Cobsidian reports an excerpt like this, without writing files:

```json
{
  "dry_run": true,
  "decision": {
    "action": "append",
    "target_note": "AI Conversations.md"
  },
  "suggested_backlinks": [
    {
      "title": "Agent Workflows",
      "path": "Agent Workflows.md"
    }
  ],
  "writes": []
}
```

## Modes

Cobsidian supports modes so users can tell the agent what kind of note they want.

| Mode | Use when | Example prompt |
|---|---|---|
| Learning | You are studying a concept, course, paper, video, or technical topic. | `Use Cobsidian in learning mode to organize this explanation.` |
| Project | You are documenting a project, repository, architecture, implementation, or operation. | `Use Cobsidian in project mode to summarize this repo analysis.` |
| Review | You are reviewing an incident, failed experiment, decision, or result. | `Use Cobsidian in review mode to write a failure review.` |
| Comparison | You are comparing tools, architectures, models, libraries, databases, or approaches. | `Use Cobsidian in comparison mode to compare these options.` |
| Index | You need a topic map, learning path, hub note, or navigation page. | `Use Cobsidian in index mode to build a knowledge map.` |
| Daily Capture | You want to save rough material quickly before deep organization. | `Use Cobsidian in daily capture mode to save this for later.` |
| Dissection | You are breaking down a tool, framework, repo, skill, prompt system, or source code. | `Use Cobsidian in dissection mode to analyze this agent framework.` |

If you do not choose a mode, the agent should infer one and report the choice.

When the request is unclear, the agent should introduce the mode choices in the conversation instead of expecting users to read this README first.

See [Modes](docs/modes.md) for details.

## CLI Utilities

Run helper scripts when you need deterministic vault checks:

```bash
python skills/cobsidian/scripts/scan_vault.py /path/to/vault --json
python skills/cobsidian/scripts/find_duplicates.py /path/to/vault
python skills/cobsidian/scripts/suggest_backlinks.py /path/to/vault --file draft.md
python skills/cobsidian/scripts/validate_notes.py /path/to/vault
python skills/cobsidian/scripts/dry_run.py /path/to/vault --topic "RAG" --text "draft text" --json
```

Each script also accepts `--config cobsidian.config.yml` when the config contains `vault.path`.

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

### `dry_run.py`

Plans a write without modifying files. It reports create/append decision, duplicate risks, backlink suggestions, validation intent, and an empty `writes` list.

```bash
python skills/cobsidian/scripts/dry_run.py examples/demo-vault --topic "AI Conversations" --text "agent workflow notes" --json
```

## Repository Layout

```text
Cobsidian/
├── skills/cobsidian/
│   ├── SKILL.md
│   ├── mcp_server.py
│   ├── agents/openai.yaml
│   ├── references/
│   │   ├── backlink-policy.md
│   │   ├── markdown-style.md
│   │   └── note-types.md
│   └── scripts/
├── examples/
│   └── demo-vault/
├── docs/
├── .github/workflows/
├── cobsidian.config.example.yml
├── INSTALL.md
├── requirements-mcp.txt
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

## Optional Config

`cobsidian.config.example.yml` documents optional vault, naming, safety, linking, and validation conventions for agents or adapters. Copy it to `cobsidian.config.yml` if you want a reusable local convention.

The helper scripts read it with `--config`.

## Roadmap

- Better duplicate detection with configurable thresholds.
- Frontmatter support for vaults that use YAML metadata.
- Optional note templates.
- Configurable naming rules.
- Safer dry-run mode for proposed edits.
- Thin adapters for Hermes, Claude Code, and Cursor.
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

## Trademark And Affiliation Notice

Cobsidian is an independent open-source project. OpenAI, Codex, Obsidian, Claude, Cursor, Hermes, and other names are trademarks of their respective owners. This project is not affiliated with, endorsed by, or sponsored by those owners.

## License

MIT. See [LICENSE](LICENSE).
