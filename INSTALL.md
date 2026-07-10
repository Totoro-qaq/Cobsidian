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

## Install As A Codex Skill

Install and configure Codex from the official Codex docs first. Then install Cobsidian as a local skill.

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

Then start a new Codex session and ask:

```text
Use Cobsidian to organize this material into my Obsidian vault.
```

## Use With Other Agents

For Hermes, Claude Code, Cursor, or another coding agent:

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
python -m unittest discover tests
```

Expected result:

- `scan_vault.py` prints note metadata.
- `find_duplicates.py` reports no duplicate or highly similar titles.
- `validate_notes.py --strict` reports no basic note hygiene issues.
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
