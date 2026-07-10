# Integrations

Cobsidian is an independent local workflow for agents that maintain Markdown knowledge bases. It can work with Obsidian vaults, Codex skills, and MCP hosts, but it is not part of those products.

Use this page after you have installed the product you want to use. For product installation and account setup, follow the official docs linked below instead of copying instructions from this repository.

## Official References

- Codex CLI: <https://developers.openai.com/codex/cli>
- Codex skills: <https://developers.openai.com/codex/skills>
- Codex MCP and configuration docs: <https://developers.openai.com/codex/mcp>
- Obsidian vault management: <https://obsidian.md/help/manage-vaults>
- Obsidian Brand Guidelines: <https://obsidian.md/brand>

## Adaptive Host Path

Run capability detection against the tools exposed in the current session; do not infer access from a product name. Cobsidian uses capability-based degradation across four levels:

| Level | Integration path |
|---|---|
| `full-local` | Use MCP-backed inspection plus an approved local write and validation path. |
| `filesystem-only` | Use the local scripts, filesystem edits, and validation without MCP. |
| `mcp-readonly` | Use Cobsidian MCP for scan and dry-run, then return a change plan because no write path exists. |
| `chat-only` | Return a portable draft or request a usable vault/config path; do not claim a scan or write. |

This is a zero-write MCP design: Cobsidian's MCP server exposes inspection and planning only, always returns `writes: []` from dry-run, and never gains write access from a `capability_level` argument. `ready` describes whether the active host has completed checks and can proceed after approval, not whether a write already happened.

See [Agent Compatibility](agent-compatibility.md) for the full capability table and [MCP Server](mcp-server.md) for parameter parity and fail-closed errors.

## Use With An Obsidian Vault

Cobsidian works with an Obsidian vault because an Obsidian vault is a local folder of Markdown files.

1. Create or open your vault in Obsidian.
2. Copy the vault folder path.
3. Use that path in your agent prompt, `cobsidian.config.yml`, or `COBSIDIAN_VAULT`.
4. Run a dry run before letting an agent edit notes.

Example config:

```yaml
vault:
  path: "/absolute/path/to/obsidian-vault"
```

Example check:

```bash
python skills/cobsidian/scripts/scan_vault.py --config cobsidian.config.yml --json
python skills/cobsidian/scripts/dry_run.py --config cobsidian.config.yml --topic "RAG" --text "RAG and vector search notes" --json
```

Keep private vault contents out of GitHub issues, screenshots, sample prompts, and bug reports.

## Use As A Codex Skill

First install and configure Codex from the official Codex docs. Then copy Cobsidian's skill directory into your local Codex skills directory.

Linux or macOS:

```bash
mkdir -p ~/.agents/skills
cp -r skills/cobsidian ~/.agents/skills/cobsidian
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills" | Out-Null
Copy-Item -Recurse -Force .\skills\cobsidian "$env:USERPROFILE\.agents\skills\cobsidian"
```

Codex currently documents `$HOME/.agents/skills` for user skills. Some local or older Codex builds may scan `$HOME/.codex/skills`; use the skills directory shown by your Codex surface.

Start a new Codex session and ask for Cobsidian explicitly:

```text
Use Cobsidian to organize this material into my Obsidian vault.
Vault: /absolute/path/to/obsidian-vault
Run a dry run first, check for duplicate notes, suggest backlinks, and wait for confirmation before writing.
```

If you use a reusable config, include it in the prompt:

```text
Use Cobsidian and follow /absolute/path/to/cobsidian.config.yml.
```

## Use As A Local MCP Server

Cobsidian also ships a local MCP server. It currently exposes read and planning tools only; it does not expose a write tool.

Vault scans are paginated (`limit=100` by default, `500` maximum), and similar-title comparisons report when their work cap is reached. Backlink suggestions use the same body-aware multilingual ranker as the CLI and dry-run path.

Install the MCP dependency:

```bash
python -m pip install -r requirements-mcp.txt
```

Configure your MCP host with an absolute path:

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

Different hosts store MCP configuration in different places. Keep the server block the same and adapt only the host-specific wrapper.

See [MCP Server](mcp-server.md) for registered tools, resources, prompts, and safety notes.

## Use With Other Agents

For Hermes, Claude Code, Cursor, or another coding agent, keep the adapter thin:

1. Point the agent to `skills/cobsidian/SKILL.md`.
2. Ask it to detect actual scan, write, MCP, and validation capabilities.
3. Give it the vault path or `cobsidian.config.yml`.
4. Allow it to run the helper scripts in `skills/cobsidian/scripts/` when local execution exists.
5. Require Knowledge Read, preflight, and a dry-run summary before write actions.
6. Require duplicate checks, backlink suggestions, and validation output in the final report.

Generic prompt:

```text
Use the Cobsidian workflow in skills/cobsidian/SKILL.md.
Vault: /path/to/my/obsidian-vault
Organize the following material into linked Markdown notes.
Search existing notes first, prefer append over duplicate notes, add useful wiki links, and run validation.
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Agent does not mention Cobsidian | Skill not loaded, session not restarted, or prompt did not name it | Reinstall the skill and start a new agent session. |
| Notes go to the wrong folder | Vault path is missing or relative to the wrong working directory | Use an absolute vault path or `cobsidian.config.yml`. |
| MCP host cannot start the server | Wrong Python executable, missing dependency, or relative path issue | Install `requirements-mcp.txt` and use absolute paths. |
| Agent wants to write immediately | Host prompt skipped the dry-run policy | Ask for dry run first and confirm before writing. |

## Trademark And Affiliation Notice

Cobsidian is an independent open-source project. OpenAI, Codex, Obsidian, Claude, Cursor, Hermes, and other names are trademarks of their respective owners. This project is not affiliated with, endorsed by, or sponsored by those owners.
