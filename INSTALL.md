# Install Cobsidian

Cobsidian is a local agent workflow skill. It does not require an Obsidian plugin or cloud service.

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

Linux or macOS:

```bash
mkdir -p ~/.codex/skills
cp -r skills/cobsidian ~/.codex/skills/cobsidian
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force .\skills\cobsidian "$env:USERPROFILE\.codex\skills\cobsidian"
```

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
Use Cobsidian and follow cobsidian.config.yml for vault path, naming, safety, and validation rules.
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
cp -r skills/cobsidian ~/.codex/skills/cobsidian
```

Windows PowerShell:

```powershell
Copy-Item -Recurse -Force .\skills\cobsidian "$env:USERPROFILE\.codex\skills\cobsidian"
```

## Uninstall

Remove the copied skill directory:

```bash
rm -rf ~/.codex/skills/cobsidian
```

Windows PowerShell:

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.codex\skills\cobsidian"
```
