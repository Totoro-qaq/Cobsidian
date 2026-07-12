# Integrations

Cobsidian is an independent local workflow for agents that maintain Markdown knowledge bases. It can work with Obsidian vaults, Codex skills, and MCP hosts, but it is not part of those products.

Use this page after you have installed the product you want to use. For product installation and account setup, follow the official docs linked below instead of copying instructions from this repository.

## Official References

- Codex CLI: <https://developers.openai.com/codex/cli>
- Codex skills: <https://developers.openai.com/codex/skills>
- Codex MCP and configuration docs: <https://developers.openai.com/codex/mcp>
- Kimi Code skills: <https://moonshotai.github.io/kimi-code/en/customization/skills>
- Kimi Code MCP: <https://moonshotai.github.io/kimi-code/en/customization/mcp>
- OpenCode skills: <https://opencode.ai/docs/skills>
- OpenCode MCP servers: <https://opencode.ai/docs/mcp-servers>
- Pi coding agent: <https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent>
- Antigravity skills: <https://antigravity.google/docs/skills>
- Antigravity MCP: <https://antigravity.google/docs/mcp>
- GitHub Copilot CLI skills: <https://docs.github.com/en/enterprise-cloud@latest/copilot/how-tos/copilot-cli/customize-copilot/add-skills>
- GitHub Copilot CLI command reference: <https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference>
- Claude Code skills: <https://code.claude.com/docs/en/slash-commands>
- Claude Code MCP: <https://code.claude.com/docs/en/mcp>
- Obsidian vault management: <https://obsidian.md/help/manage-vaults>
- Obsidian Brand Guidelines: <https://obsidian.md/brand>

## Adaptive Host Path

Run capability detection against the tools exposed in the current session; do not infer access from a product name. Cobsidian uses capability-based degradation across four levels:

| Level | Integration path |
|---|---|
| `full-local` | Use MCP-backed scan/dry-run with an approved write path. |
| `filesystem-only` | Use local scan/dry-run with an approved write path without MCP. |
| `mcp-readonly` | Scan and dry-run, then return a change plan because no approved write path exists, regardless of transport. |
| `chat-only` | Return a portable draft or request a usable vault/config path; do not claim a scan or write. |

Capability level records effective scan/write transport; report validation independently through `validation_available`. A write-capable host without validation keeps `full-local` or `filesystem-only`, sets `validation_available=false`, and reports `validation_capability_unavailable`. The historical name `mcp-readonly` is retained for compatibility. It is the transport-neutral effective read-only level, including local read-only operation without MCP. This remains a zero-write MCP design: Cobsidian's MCP server exposes inspection and planning only, always returns `writes: []` from dry-run, and never gains write access from a `capability_level` argument. `ready` describes whether the active host has completed checks and can proceed after approval, not whether a write already happened.

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

## Install For Supported CLIs

The checked-in installer maps Cobsidian to the documented user or project discovery path for Kimi Code, OpenCode, Pi, Antigravity, GitHub Copilot CLI, Codex CLI, and Claude Code CLI. Preview before copying:

```bash
python install_cobsidian.py --host all --scope user --dry-run --json
python install_cobsidian.py --host all --scope user
```

Use `--scope project --project /path/to/workspace` for a workspace-local install. Pass `--symlink` for a development checkout or `--force` to replace an existing installation explicitly. Shared hosts collapse into one `~/.agents/skills/cobsidian` copy; Antigravity and Claude Code use their distinct global paths.

| CLI | User skill path | Project skill path | MCP support |
|---|---|---|---|
| Kimi Code | `~/.agents/skills/cobsidian` | `.agents/skills/cobsidian` | Native local stdio MCP |
| OpenCode | `~/.agents/skills/cobsidian` | `.agents/skills/cobsidian` | Native local MCP in `opencode.json` |
| Pi | `~/.agents/skills/cobsidian` | `.agents/skills/cobsidian` | No built-in MCP; extension only |
| Antigravity | `~/.gemini/config/skills/cobsidian` | `.agents/skills/cobsidian` | Native global/workspace MCP config |
| GitHub Copilot CLI | `~/.agents/skills/cobsidian` | `.agents/skills/cobsidian` | Native local stdio MCP |
| Codex CLI | `~/.agents/skills/cobsidian` | `.agents/skills/cobsidian` | Native local stdio MCP |
| Claude Code CLI | `~/.claude/skills/cobsidian` | `.claude/skills/cobsidian` | Native local stdio MCP |

You can still copy a single Codex-compatible skill manually:

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

Codex, Kimi Code, OpenCode, Pi, and GitHub Copilot CLI all document the shared `.agents/skills` convention. Product-specific directories may also be supported; the installer deliberately chooses the smallest portable set.

Start a new CLI session and ask for Cobsidian explicitly:

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

Recommended host setup:

- Kimi Code: `kimi mcp add --env COBSIDIAN_CONFIG=/absolute/path/to/cobsidian.config.yml cobsidian -- python /absolute/path/to/Cobsidian/skills/cobsidian/mcp_server.py`
- OpenCode: add the same Python command as a `type: "local"` server under the `mcp` key in `opencode.json`.
- Antigravity: place the server in global `~/.gemini/config/mcp_config.json` or workspace `.agents/mcp_config.json`.
- GitHub Copilot CLI: use `copilot mcp add cobsidian --env COBSIDIAN_CONFIG=/absolute/path/to/cobsidian.config.yml -- python /absolute/path/to/Cobsidian/skills/cobsidian/mcp_server.py`.
- Codex CLI: use `codex mcp add cobsidian --env COBSIDIAN_CONFIG=/absolute/path/to/cobsidian.config.yml -- python /absolute/path/to/Cobsidian/skills/cobsidian/mcp_server.py`.
- Claude Code CLI: use `claude mcp add --transport stdio --scope user --env COBSIDIAN_CONFIG=/absolute/path/to/cobsidian.config.yml cobsidian -- python /absolute/path/to/Cobsidian/skills/cobsidian/mcp_server.py`.
- Pi: use the local scripts and deterministic writer by default. Only configure MCP through a Pi extension that explicitly implements it.


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
