# Cobsidian — Claude Code / OpenCode Setup

## Install as a Claude Skill

Copy the skill directory into your Claude skills path:

```bash
# Linux / macOS
mkdir -p ~/.claude/skills
cp -r skills/cobsidian ~/.claude/skills/cobsidian

# Windows PowerShell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse -Force .\skills\cobsidian "$env:USERPROFILE\.claude\skills\cobsidian"
```

Claude Code and OpenCode will pick up `SKILL.md` from this path automatically.

## Or Reference from CLAUDE.md

If you prefer not to copy, add this to your project or global `CLAUDE.md`:

```markdown
做后端就用superpowers，openspec等skill
做知识整理就用cobsidian skill

Read skills/cobsidian/SKILL.md when the user asks to organize material into an Obsidian vault or Markdown knowledge base.
```

## MCP Server (stdio)

For private vaults, use the local stdio MCP server instead of exposing tools over HTTP.

Add to your Claude MCP config (`~/.claude/mcp.json` or project-level):

```json
{
  "mcpServers": {
    "cobsidian": {
      "command": "python",
      "args": ["skills/cobsidian/mcp_server.py"],
      "env": {
        "PYTHONUTF8": "1",
        "COBSIDIAN_VAULT": "/absolute/path/to/your/obsidian-vault"
      }
    }
  }
}
```

Replace the vault path with your actual vault. Use `COBSIDIAN_CONFIG` instead if you have a `cobsidian.config.yml`.

## Usage

```text
帮我把刚才讨论的知识点整理到 Obsidian 知识库里。
先 dry-run 看看计划，确认后再写入。
```

```text
Use Cobsidian to organize this conversation into a learning note.
Check for duplicates, suggest backlinks, and wait for my confirmation.
```
