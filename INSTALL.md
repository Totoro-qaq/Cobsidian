# Install Cobsidian

Cobsidian is a local agent workflow skill. It does not require an Obsidian plugin or cloud service.

For Codex, Obsidian vault, MCP host, and other-agent integration notes, see [Integrations](docs/integrations.md).

## Requirements

- Git
- Python 3.10 or newer
- An Obsidian vault or any folder of Markdown notes
- A coding agent that can read local instructions and run commands

## Clone

```bash
git clone https://github.com/Totoro-qaq/Cobsidian.git
cd Cobsidian
```

With SSH:

```bash
git clone git@github.com:Totoro-qaq/Cobsidian.git
cd Cobsidian
```

## Install For Supported CLIs

Install Cobsidian for Kimi Code, OpenCode, Pi, Antigravity, GitHub Copilot CLI, Codex CLI, and Claude Code CLI. Preview the resolved destinations first:

```bash
python install_cobsidian.py --host all --scope user --dry-run --json
python install_cobsidian.py --host all --scope user
```

For only one host, use `--host codex-cli`, `--host claude-code-cli`, or another supported ID. For a workspace-local install, use `--scope project --project /path/to/workspace`. The installer refuses to overwrite an existing skill unless `--force` is explicit; `--symlink` is useful while developing Cobsidian.

Manual shared-path installation remains available:

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

This shared path covers Kimi Code, OpenCode, Pi, GitHub Copilot CLI, and Codex CLI. Antigravity and Claude Code use separate global paths; see [Integrations](docs/integrations.md).

Then start a new Codex session and ask:

```text
Use Cobsidian to organize this material into my Obsidian vault.
```

## Use With Other Agents

For Hermes, Cursor, or another coding agent:

1. Point the agent to `skills/cobsidian/SKILL.md`.
2. Give it the target vault path.
3. Allow it to run the Python helper scripts in `skills/cobsidian/scripts/`.
4. Ask it to report create/append decisions, duplicate checks, backlinks, and validation.

Example:

```text
Use the Cobsidian workflow in skills/cobsidian/SKILL.md.
Vault: /path/to/my/obsidian-vault
Organize the following material into a linked Markdown note.
Search existing notes first, avoid duplicates, add useful wiki links, and run validation.
```

## Install As An MCP Server

Install the MCP SDK dependency:

```bash
python -m pip install -r requirements-mcp.txt
```

Configure your MCP host to launch Cobsidian over local `stdio`:

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

See [MCP Server](docs/mcp-server.md) and [Integrations](docs/integrations.md).

## Optional Config

Copy the example config if you want a reusable project-local convention:

```bash
cp cobsidian.config.example.yml cobsidian.config.yml
```

Windows PowerShell:

```powershell
Copy-Item .\cobsidian.config.example.yml .\cobsidian.config.yml
```

The helper scripts can read this file with `--config`:

```bash
python skills/cobsidian/scripts/scan_vault.py --config cobsidian.config.yml --json
python skills/cobsidian/scripts/dry_run.py --config cobsidian.config.yml --topic "RAG" --text "RAG and vector search notes" --json
```

Also include it in your agent prompt:

```text
Use Cobsidian and follow cobsidian.config.yml for the vault path, mode directories, duplicate checks, backlink limits, and validation behavior.
```

## Verify The Helper Scripts

Run the scripts against the bundled examples:

```bash
python skills/cobsidian/scripts/scan_vault.py examples --json
python skills/cobsidian/scripts/find_duplicates.py examples
python skills/cobsidian/scripts/validate_notes.py examples --strict
python skills/cobsidian/scripts/quality_eval.py evals/public-smoke.jsonl evals/fixtures/public-vault --mode-predictions evals/public-mode-predictions.jsonl --json
python install_cobsidian.py --host all --scope user --dry-run --json
python -m unittest discover tests
```

Expected result:

- `scan_vault.py` prints note metadata.
- `find_duplicates.py` reports no duplicate or highly similar titles.
- `validate_notes.py --strict` reports no basic note hygiene issues.
- `quality_eval.py` reports the public smoke metrics.
- `install_cobsidian.py --dry-run` resolves three deduplicated user-level destinations for all seven CLIs without writing them.
- `unittest` reports all tests passing.

## Update

```bash
git pull
```

Then reinstall the skill if you copied it into an agent skill directory:

```bash
cp -r skills/cobsidian ~/.agents/skills/cobsidian
```

Windows PowerShell:

```powershell
Copy-Item -Recurse -Force .\skills\cobsidian "$env:USERPROFILE\.agents\skills\cobsidian"
```

## Uninstall

Remove the copied skill directory:

```bash
rm -rf ~/.agents/skills/cobsidian
```

Windows PowerShell:

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.agents\skills\cobsidian"
```
