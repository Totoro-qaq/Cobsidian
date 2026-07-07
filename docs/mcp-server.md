# Cobsidian MCP Server

Cobsidian ships a local MCP server for hosts that support the Model Context Protocol.

Use it as a local `stdio` server. Do not expose it as a public HTTP service for private vaults.

## Install Dependencies

```bash
python -m pip install -r requirements-mcp.txt
```

## Server Entry Point

```bash
python skills/cobsidian/mcp_server.py
```

This command is meant to be launched by an MCP host over `stdio`. Running it directly will wait for MCP messages on standard input.

## Host Config

Use an absolute path for reliability:

```json
{
  "mcpServers": {
    "cobsidian": {
      "command": "python",
      "args": ["/absolute/path/to/Cobsidian/skills/cobsidian/mcp_server.py"],
      "cwd": "/absolute/path/to/Cobsidian",
      "env": {
        "PYTHONUTF8": "1",
        "COBSIDIAN_CONFIG": "/absolute/path/to/cobsidian.config.yml"
      }
    }
  }
}
```

If you do not use a config file, set `COBSIDIAN_VAULT`:

```json
{
  "mcpServers": {
    "cobsidian": {
      "command": "python",
      "args": ["/absolute/path/to/Cobsidian/skills/cobsidian/mcp_server.py"],
      "cwd": "/absolute/path/to/Cobsidian",
      "env": {
        "PYTHONUTF8": "1",
        "COBSIDIAN_VAULT": "/absolute/path/to/obsidian-vault"
      }
    }
  }
}
```

Different MCP hosts place this JSON in different settings files. Keep the same server block and adapt only the host-specific wrapper.

## Tools

The server registers read/planning tools only:

| Tool | Purpose |
|---|---|
| `cobsidian_scan_vault` | Scan Markdown notes, titles, tags, and wiki links. |
| `cobsidian_find_duplicates` | Report exact and similar note titles. |
| `cobsidian_suggest_backlinks` | Suggest related notes for text or a target note. |
| `cobsidian_validate_notes` | Report missing wiki links, duplicate titles, and empty notes. |
| `cobsidian_dry_run` | Plan create/append behavior without writing files. |

There is intentionally no write tool yet. Write workflows should go through dry-run first and require user confirmation in the host.

## Resources

| Resource | Purpose |
|---|---|
| `cobsidian://config` | Read the active config summary from `COBSIDIAN_CONFIG`. |
| `cobsidian://vault-summary` | Scan the configured vault. |
| `cobsidian://note/{note_path}` | Read a note by vault-relative path. |

`cobsidian://note/{note_path}` rejects absolute paths and `..` traversal outside the vault.

## Prompts

| Prompt | Purpose |
|---|---|
| `cobsidian-dry-run` | Ask the agent to plan a vault write without changing files. |
| `cobsidian-organize-after-confirmation` | Ask the agent to organize material after the user confirms the dry-run plan. |

## Verify Locally

```bash
python -m unittest discover tests -p "test_mcp_server.py"
```

To inspect registered tools without starting a host:

```bash
python -c "import asyncio; from skills.cobsidian.mcp_server import create_mcp_server; print(asyncio.run(create_mcp_server().list_tools()))"
```

## Security Notes

- Prefer local `stdio` transport for private vaults.
- Do not expose this server to a public network.
- Do not add arbitrary shell execution tools.
- Keep write actions out of MCP until dry-run and confirmation policies are stable.
- Use `COBSIDIAN_CONFIG` or `COBSIDIAN_VAULT` to narrow the intended vault.
- Note resource reads are constrained to the resolved vault path.
