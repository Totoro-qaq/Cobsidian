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

如果不用配置文件，可以设置 `COBSIDIAN_VAULT`：

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

不同 MCP host 的配置文件位置不同。保留这个 server block，只调整外层 host 配置即可。

## Tools

当前只注册读取和规划类工具：

| Tool | 作用 |
|---|---|
| `cobsidian_scan_vault` | 使用有界的 `offset` / `limit` 分页扫描 Markdown 笔记。 |
| `cobsidian_find_duplicates` | 在有界比较次数内报告完全重复和相似标题。 |
| `cobsidian_suggest_backlinks` | 根据主题、文本或目标笔记建议相关笔记。 |
| `cobsidian_validate_notes` | 报告缺失双链目标、重复标题和空笔记。 |
| `cobsidian_dry_run` | 只规划新建/追加行为，不写文件。 |

现在故意不提供写入 tool。写入流程应该先 dry-run，再由用户在 host 里确认。

## 自适应 Dry-run 契约

`cobsidian_dry_run` 是 zero-write MCP tool。它在原有规划 payload 上增加 `knowledge_read` 和 `preflight`，`writes` 始终是 `[]`。无论传入什么 `capability_level`，MCP server 本身都保持 read-only；这个参数只描述 preflight 所评估的当前 host，不会授予 server 写权限。

历史 capability 名称 `mcp-readonly` 为兼容而保留。它表示 transport-neutral effective read-only level（传输无关的实际只读级别）：任何能扫描和 dry-run、但没有批准写入路径的 host 都归入该级，包括不依赖 MCP 的本地只读运行；名称不表示当前 transport 必须是 MCP。

Capability level 只记录有效 scan/write transport。校验由严格布尔字段 `validation_available` independently（独立）建模；省略时从 level 默认推导，也可显式覆盖。写入能力存在但校验不可用时，保留 `full-local` 或 `filesystem-only`，设置 `validation_available=false`，增加 `validation_capability_unavailable` 并保持 `ready=false`。默认 `mcp-readonly` 的校验可用，只因 `write_capability_unavailable` 阻断；`chat-only` 默认校验不可用。

### CLI/MCP Parameter Parity

CLI/MCP parameter parity（参数一致性）由共享 dry-run 实现保证，两种入口校验同一组可选上下文：

| MCP 参数 | CLI 选项 | 契约 |
|---|---|---|
| `mode` | `--mode` | `learning`、`project`、`review`、`comparison`、`index`、`capture`、`dissection` 之一；未决时省略。 |
| `mode_explicit` | `--mode-explicit` / `--no-mode-explicit` | 严格布尔值；入口会先把省略/`null` 推断为真正 bool，再调用共享 builder。 |
| `recommended_modes` | 重复使用 `--recommended-mode` | 仅在 `mode` 未决时给出零到两个 canonical mode。 |
| `depth` | `--depth` | `capture`、`standard` 或 `deep`。 |
| `granularity` | `--granularity` | `append`、`single-note` 或 `multi-note`；请求 `granularity=append` 必须对应 append 决策。 |
| `evidence` | `--evidence` | `conversation`、`source-grounded` 或 `verified`。 |
| `source_read_completed` | `--source-read-completed` | 严格布尔型 host-completed fact，表示相关来源读取确实已完成。 |
| `verification_completed` | `--verification-completed` | 严格布尔型 host-completed fact，表示附加验证确实已完成。 |
| `validation_available` | `--validation-available` / `--no-validation-available` | 可选严格布尔覆盖；省略/`null` 时从 capability 默认推导。 |
| `knowledge_read_policy` | `--knowledge-read` | `auto`、`always` 或 `off`。 |
| `capability_level` | `--capability-level` | `full-local`、`filesystem-only`、`mcp-readonly` 或 `chat-only`。 |

MCP 的 `capability_level` 默认值是 `mcp-readonly`，本地 CLI 默认值是 `filesystem-only`。等价输入会得到相同的 Knowledge Read 字段和 preflight 规则。

`source-grounded` 要求 `source_read_completed=true`；`verified` 同时要求两个完成事实。这些事实由 host 根据已完成动作提交，模式选择、偏向来源的措辞或用户声称都不会自动升级证据。它们只参与校验，不会加入现有 8 字段 `knowledge_read` JSON。

### 错误边界

Server 与共享 dry-run 会 fail closed（失败关闭）：

- Vault/config 输入缺失或无效时拒绝请求，不声称完成规划或写入。
- 空 topic、无效枚举、超过两个推荐，或 mode 已解析时仍传推荐，都会被拒绝。
- 请求 `granularity=append` 时，如果重复检查没有得到 `decision.action=append` 就会被拒绝；实际 append 决策始终强制 append granularity。
- 没有完成事实支持的 `source-grounded` / `verified` 证据，以及非布尔完成事实，都会被拒绝。
- `auto` 下模式未决时返回 expanded Knowledge Read、`ready=false` 和 `mode_unresolved`；`off` 只隐藏对话展示，任何策略都不会静默选择模式。
- Host 没有扫描能力时，decision 为 `blocked`，不能声称完成扫描派生检查。
- 只读 host 报告 `write_capability_unavailable`，不会把自己升级成写入路径。
- 校验不可用时，在 write capability reason 之后报告 `validation_capability_unavailable`，并 independently 阻断 readiness，不改变 transport level。
- 无扫描能力的 `chat-only` 不允许把 `validation_available` 覆盖为 true。
- Note resource 拒绝绝对路径和越出已解析 vault 的 `..` 路径。

## 大型 Vault 边界

- `cobsidian_scan_vault` 默认 `offset=0`、`limit=100`，单页最大 `500`；响应包含 `total_note_count` 和分页元数据。
- `cobsidian_find_duplicates` 始终完整发现归一化标题完全相同的笔记；相似标题只比较唯一归一化标题，默认最多比较 `100000` 次，并返回 `comparisons` 与 `truncated`。
- 反链排名会读取标题、标签、已有双链和正文；中文采用确定性的 CJK bigram/trigram，不依赖外部分词器。
- 反链结果数量必须在 `1` 到 `100` 之间，配置默认值为 `8`。
- 反链请求至少需要一个非空主题或素材来源；纯空白字符串与空文件会被拒绝。

## Resources

| Resource | 作用 |
|---|---|
| `cobsidian://config` | 读取 `COBSIDIAN_CONFIG` 指向的配置摘要；`interaction` 只发布规范化 `knowledge_read`。 |
| `cobsidian://vault-summary` | 为兼容已有客户端，读取完整 vault 摘要。 |
| `cobsidian://vault-page/{offset}/{limit}` | 读取已配置 vault 的有界分页。 |
| `cobsidian://note/{note_path}` | 按 vault 相对路径读取笔记。 |

`cobsidian://note/{note_path}` 会拒绝绝对路径和 `..` 越界路径。

大型 vault 应优先使用 `cobsidian://vault-page/{offset}/{limit}`。静态 `vault-summary` 保持完整，避免已有客户端被静默截断。

## Prompts

| Prompt | 作用 |
|---|---|
| `cobsidian-dry-run` | 要求 agent 先规划，不改文件。 |
| `cobsidian-organize-after-confirmation` | 用户确认 dry-run 方案后，再组织材料。 |

Prompt 只向 host 提供说明，不会给这个 server 增加写入 tool。

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
- 所有 vault 写入都保持在 MCP server 之外，并由 host 明确批准。
- 用 `COBSIDIAN_CONFIG` 或 `COBSIDIAN_VAULT` 限定目标 vault。
- note resource 读取会限制在已解析的 vault 路径内。
