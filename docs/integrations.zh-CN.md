# 集成说明

Cobsidian 是一个独立的本地 Agent 工作流，用来维护 Markdown 知识库。它可以配合 Obsidian vault、Codex skill 和 MCP host 使用，但它不是这些产品的一部分。

这页只说明 Cobsidian 如何接入这些工具。产品本身的安装、账号和环境配置，请以官方文档为准，不要把本仓库当作那些产品的安装文档。

## 官方参考

- Codex CLI: <https://developers.openai.com/codex/cli>
- Codex skills: <https://developers.openai.com/codex/skills>
- Codex MCP 与配置文档: <https://developers.openai.com/codex/mcp>
- Obsidian vault 管理: <https://obsidian.md/help/manage-vaults>
- Obsidian Brand Guidelines: <https://obsidian.md/brand>

## 配合 Obsidian Vault 使用

Cobsidian 可以配合 Obsidian vault 使用，是因为 Obsidian vault 本质上是一个本地 Markdown 文件夹。

1. 在 Obsidian 里创建或打开 vault。
2. 复制 vault 文件夹路径。
3. 把路径写进 Agent 提示词、`cobsidian.config.yml` 或 `COBSIDIAN_VAULT`。
4. 让 Agent 先做 dry run，再确认是否写入。

配置示例：

```yaml
vault:
  path: "D:/path/to/obsidian-vault"
```

检查示例：

```bash
python skills/cobsidian/scripts/scan_vault.py --config cobsidian.config.yml --json
python skills/cobsidian/scripts/dry_run.py --config cobsidian.config.yml --topic "RAG" --text "RAG and vector search notes" --json
```

不要把私人 vault 内容、截图、私有路径、API key 或未公开笔记提交到 GitHub issue、示例提示词或 bug report 里。

## 作为 Codex Skill 使用

先按官方 Codex 文档安装和配置 Codex。然后把 Cobsidian 的 skill 目录复制到本地 Codex skills 目录。

Linux 或 macOS：

```bash
mkdir -p ~/.agents/skills
cp -r skills/cobsidian ~/.agents/skills/cobsidian
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills" | Out-Null
Copy-Item -Recurse -Force .\skills\cobsidian "$env:USERPROFILE\.agents\skills\cobsidian"
```

Codex 当前官方文档里的用户级 skill 目录是 `$HOME/.agents/skills`。部分本地或旧版 Codex 构建可能扫描 `$HOME/.codex/skills`；以你正在使用的 Codex surface 显示的 skills 目录为准。

打开新的 Codex 会话，并明确点名 Cobsidian：

```text
Use Cobsidian to organize this material into my Obsidian vault.
Vault: D:/path/to/obsidian-vault
Run a dry run first, check for duplicate notes, suggest backlinks, and wait for confirmation before writing.
```

如果使用固定配置文件，可以在提示词里写：

```text
Use Cobsidian and follow D:/path/to/cobsidian.config.yml.
```

## 作为本地 MCP Server 使用

Cobsidian 也提供本地 MCP server。当前只暴露只读和规划工具，不暴露写入工具。

安装 MCP 依赖：

```bash
python -m pip install -r requirements-mcp.txt
```

用绝对路径配置 MCP host：

```json
{
  "mcpServers": {
    "cobsidian": {
      "command": "python",
      "args": ["D:/python/Cobsidian/skills/cobsidian/mcp_server.py"],
      "cwd": "D:/python/Cobsidian",
      "env": {
        "PYTHONUTF8": "1",
        "COBSIDIAN_CONFIG": "D:/path/to/cobsidian.config.yml"
      }
    }
  }
}
```

不同 MCP host 的配置文件位置不同。保留这个 server block，只调整外层 host 配置即可。

工具、资源、prompt 和安全边界见 [MCP Server](mcp-server.zh-CN.md)。

## 配合其他 Agent 使用

Hermes、Claude Code、Cursor 或其他 coding agent 使用时，adapter 应该保持很薄：

1. 让 Agent 读取 `skills/cobsidian/SKILL.md`。
2. 给出 vault 路径或 `cobsidian.config.yml`。
3. 允许它运行 `skills/cobsidian/scripts/` 里的辅助脚本。
4. 写入前要求输出 dry-run 摘要。
5. 最终汇报里必须包含重复检查、反链建议和校验结果。

通用提示词：

```text
Use the Cobsidian workflow in skills/cobsidian/SKILL.md.
Vault: /path/to/my/obsidian-vault
Organize the following material into linked Markdown notes.
Search existing notes first, prefer append over duplicate notes, add useful wiki links, and run validation.
```

## 排错

| 现象 | 常见原因 | 处理方式 |
|---|---|---|
| Agent 没提到 Cobsidian | skill 没加载、会话没重启，或提示词没点名 | 重新安装 skill，并开启新的 Agent 会话。 |
| 笔记写到了错误目录 | vault 路径缺失，或相对路径基准不对 | 使用绝对 vault 路径或 `cobsidian.config.yml`。 |
| MCP host 启动不了 server | Python 路径不对、依赖缺失，或使用了相对路径 | 安装 `requirements-mcp.txt`，并使用绝对路径。 |
| Agent 想直接写入 | 提示词没有强调 dry-run 流程 | 先要求 dry run，确认后再写入。 |

## 商标和独立性声明

Cobsidian 是独立开源项目。OpenAI、Codex、Obsidian、Claude、Cursor、Hermes 以及其他名称均属于各自权利人。本项目不隶属于这些权利人，也未获得其背书或赞助。
