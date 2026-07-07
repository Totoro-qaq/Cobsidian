# Cobsidian MCP Server

Cobsidian 提供本地 MCP server，适合支持 Model Context Protocol 的 host 使用。

建议使用本地 `stdio` server。私人 Obsidian vault 不建议暴露成公网 HTTP 服务。

## 安装依赖

```bash
python -m pip install -r requirements-mcp.txt
```

## Server 入口

```bash
python skills/cobsidian/mcp_server.py
```

这个命令主要给 MCP host 通过 `stdio` 启动。直接运行时，它会等待标准输入里的 MCP 消息。

## Host 配置

推荐使用绝对路径：

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

如果不用配置文件，可以设置 `COBSIDIAN_VAULT`：

```json
{
  "mcpServers": {
    "cobsidian": {
      "command": "python",
      "args": ["D:/python/Cobsidian/skills/cobsidian/mcp_server.py"],
      "cwd": "D:/python/Cobsidian",
      "env": {
        "PYTHONUTF8": "1",
        "COBSIDIAN_VAULT": "D:/path/to/obsidian-vault"
      }
    }
  }
}
```

不同 MCP host 的配置文件位置不同。保留这个 server block，只调整外层 host 配置即可。

## Tools

当前只注册读取和规划类工具：

| Tool | 作用 |
|---|---|
| `cobsidian_scan_vault` | 扫描 Markdown 笔记、标题、标签和双链。 |
| `cobsidian_find_duplicates` | 报告完全重复和相似标题。 |
| `cobsidian_suggest_backlinks` | 根据文本或目标笔记建议相关笔记。 |
| `cobsidian_validate_notes` | 报告缺失双链目标、重复标题和空笔记。 |
| `cobsidian_dry_run` | 只规划新建/追加行为，不写文件。 |

现在故意不提供写入 tool。写入流程应该先 dry-run，再由用户在 host 里确认。

## Resources

| Resource | 作用 |
|---|---|
| `cobsidian://config` | 读取 `COBSIDIAN_CONFIG` 指向的配置摘要。 |
| `cobsidian://vault-summary` | 扫描已配置的 vault。 |
| `cobsidian://note/{note_path}` | 按 vault 相对路径读取笔记。 |

`cobsidian://note/{note_path}` 会拒绝绝对路径和 `..` 越界路径。

## Prompts

| Prompt | 作用 |
|---|---|
| `cobsidian-dry-run` | 要求 agent 先规划，不改文件。 |
| `cobsidian-organize-after-confirmation` | 用户确认 dry-run 方案后，再组织材料。 |

## 本地验证

```bash
python -m unittest discover tests -p "test_mcp_server.py"
```

不启动 host，直接查看已注册工具：

```bash
python -c "import asyncio; from skills.cobsidian.mcp_server import create_mcp_server; print(asyncio.run(create_mcp_server().list_tools()))"
```

## 安全边界

- 私人 vault 优先使用本地 `stdio`。
- 不要把 server 暴露到公网。
- 不要加入任意 shell 执行工具。
- 写入 tool 等 dry-run 和确认策略稳定后再加。
- 用 `COBSIDIAN_CONFIG` 或 `COBSIDIAN_VAULT` 限定目标 vault。
- note resource 读取会限制在已解析的 vault 路径内。
