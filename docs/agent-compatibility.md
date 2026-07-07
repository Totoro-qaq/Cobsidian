# Agent Compatibility

Cobsidian is designed as an agent-agnostic workflow.

The core contract is simple:

```text
read instructions
-> inspect the vault
-> decide create vs append vs split
-> write Markdown
-> add wiki links and backlink suggestions
-> run validation
-> report changes
```

## Compatibility Matrix

| Agent | Support level | Recommended usage |
|---|---|---|
| Codex | First-class | Install `skills/cobsidian` as a Codex skill. |
| MCP hosts | First-class local server | Launch `skills/cobsidian/mcp_server.py` over local `stdio`. |
| Hermes | Portable workflow | Register or reference `skills/cobsidian/SKILL.md` as a local workflow/skill and allow script execution. |
| Claude Code | Portable workflow | Reference `skills/cobsidian/SKILL.md` from project instructions or a local skill setup, then run scripts from the terminal. |
| Cursor | Portable workflow | Reference the workflow from Cursor rules or project instructions, then run scripts from the integrated terminal. |
| Other coding agents | Portable workflow | Provide `SKILL.md` as instructions and expose the Python scripts. |

## What Must Be Preserved

Any adapter should preserve these behaviors:

1. Search before writing.
2. Prefer append/merge over duplicate notes.
3. Add useful `[[wiki links]]`, not keyword spam.
4. Report whether validation was run.
5. Avoid private paths, secrets, and raw chat logs by default.

## Adapter Strategy

Do not duplicate the whole workflow for every agent.

Keep the canonical instructions here:

```text
skills/cobsidian/SKILL.md
skills/cobsidian/references/
skills/cobsidian/scripts/
```

Agent-specific adapters should stay thin:

```text
adapter = how this agent loads Cobsidian
core = what Cobsidian tells the agent to do
```

For MCP hosts, the adapter is `skills/cobsidian/mcp_server.py`. See [MCP Server](mcp-server.md).

For product-specific setup notes, see [Integrations](integrations.md).

## Suggested Prompts

Generic prompt:

```text
Use the Cobsidian workflow in skills/cobsidian/SKILL.md.
Organize this material into my Obsidian vault.
Search existing notes first, decide create vs append, add useful wiki links, and run validation if possible.
```

Safer dry-run prompt:

```text
Use the Cobsidian workflow in skills/cobsidian/SKILL.md.
Do not edit files yet. First report the target note, duplicate risks, suggested backlinks, and proposed Markdown outline.
```
