# Agent 兼容性

[English](agent-compatibility.md)

Cobsidian 不绑定某个 Agent。兼容性由当前实际可用工具决定，不根据 host 产品名称或预期功能推断。

## Capability Detection

每次运行都先做 capability detection（能力检测）：分别检查 vault 访问、本地 shell、文件编辑、Cobsidian MCP tools/resources 和校验路径，再映射到唯一 capability level，之后才能声称完成了对应操作。

| Capability level | 扫描 | Dry-run | Agent 写入 | 校验 | 适用条件 |
|---|---:|---:|---:|---:|---|
| `full-local` | 是 | 是 | 是 | 是 | MCP 扫描/dry-run、本地批准写入和校验路径都实际可用。 |
| `filesystem-only` | 是 | 是 | 是 | 是 | 有本地读取、脚本、编辑和校验工具，但没有可用 MCP。 |
| `mcp-readonly` | 是 | 是 | 否 | 是 | Cobsidian MCP 可以检查和规划，但 host 没有批准的文件写入路径。 |
| `chat-only` | 否 | 否 | 否 | 否 | Host 无法访问或扫描目标 vault。 |

`ready: true` 表示所有必要 preflight 检查已完成，并且当前 host 可以在获得批准后写入；它不表示已经写入，dry-run 仍返回 `writes: []`。`mcp-readonly` 永远不会进入写入 ready 状态，并包含 `write_capability_unavailable`。无论调用方怎样描述外部 host capability，MCP server 自身始终 read-only（只读）。

全部阻断原因见共享的 [preflight contract](../skills/cobsidian/references/preflight.md)。

## Capability-based Degradation

这里的 capability-based degradation（按能力降级）保证结果与实际能力一致：

- `full-local` 和 `filesystem-only`：扫描、规划、请求批准，通过检测到的本地路径写入，再校验。
- `mcp-readonly`：返回 zero-write dry-run 和待批准的改动计划，绝不声称修改了 vault。
- `chat-only`：返回可移植草稿，或请求一个可用 vault/config 路径；不声称得到了扫描支持的新建/追加结论。
- 证据缺失或检查失败：保持 `ready=false`，列出全部阻断原因，并 fail closed（失败关闭）。

拥有工具不等于检查已经完成。Preflight 字段记录实际完成的工作，不记录对 host 功能的预期。

## Adapter 对照

| Host 类型 | Adapter reference | 说明 |
|---|---|---|
| Codex | [Codex](../skills/cobsidian/references/hosts/codex.md) | 分别检测 MCP、shell、编辑和校验路径。 |
| Claude Code / OpenCode | [Claude Code](../skills/cobsidian/references/hosts/claude-code.md) | 只使用当前会话实际暴露的工具。 |
| Cursor | [Cursor](../skills/cobsidian/references/hosts/cursor.md) | 分别判断编辑器与终端能力。 |
| Hermes | [Hermes](../skills/cobsidian/references/hosts/hermes.md) | 执行前映射已注册 workflow 和工具。 |
| 通用 MCP host | [MCP](../skills/cobsidian/references/hosts/mcp.md) | Cobsidian server 是 zero-write 的检查与规划面。 |

轻量 adapter 只加载 canonical router、一个匹配的 host reference 和一个 mode reference，不复制完整工作流。

## 必须保留的工作流契约

任何兼容 host 都必须保留：

1. Vault 操作前先解析目标 vault。
2. 有扫描能力时，提出写入方案前先扫描。
3. `decision.action` 仅为 `create | append | blocked`；拆分单独报告为 `multi-note` 计划。
4. 优先追加到近似主题，只链接已确认存在的笔记。
5. 默认 dry-run，本地编辑前请求批准，只汇报实际校验证据。
6. 公共或通用笔记不写私人路径、密钥和原始聊天流水。

## 推荐提示词

```text
Use the Cobsidian workflow in skills/cobsidian/SKILL.md.
Detect the available capabilities, run a dry run, and report Knowledge Read and preflight.
Search existing notes before any proposed write, then wait for confirmation.
```

产品接入见 [集成说明](integrations.zh-CN.md)，MCP 工具和参数 parity 见 [MCP Server](mcp-server.zh-CN.md)。
