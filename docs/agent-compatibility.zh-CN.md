# Agent 兼容性

[English](agent-compatibility.md)

Cobsidian 不绑定某个 Agent。兼容性由当前实际可用工具决定，不根据 host 产品名称或预期功能推断。

## Capability Detection

每次运行都先做 capability detection（能力检测）：分别检查 vault 访问、本地 shell、文件编辑、Cobsidian MCP tools/resources 和校验路径，再映射到唯一 capability level，之后才能声称完成了对应操作。

| Capability level | 扫描 | Dry-run | Agent 写入 | 默认校验 | 适用条件 |
|---|---:|---:|---:|---:|---|
| `full-local` | 是 | 是 | 是 | 是 | MCP 扫描/dry-run 与批准写入路径可用。 |
| `filesystem-only` | 是 | 是 | 是 | 是 | 不依赖 MCP 的本地扫描/dry-run 与批准写入路径可用。 |
| `mcp-readonly` | 是 | 是 | 否 | 是 | 可以扫描和 dry-run，但没有批准写入路径；与 transport 无关。 |
| `chat-only` | 否 | 否 | 否 | 否 | Host 无法访问或扫描目标 vault。 |

Capability level 只记录有效 scan/write transport。校验通过 `validation_available` independently（独立）报告；写入能力存在但校验不可用时，保留 `full-local` 或 `filesystem-only`，设置 `validation_available=false`，并报告 `validation_capability_unavailable`。历史名称 `mcp-readonly` 为兼容而保留；它表示 transport-neutral effective read-only level（传输无关的实际只读级别），也包括没有 MCP 的本地只读 host。`ready: true` 表示所有必要 preflight 检查已完成，并且当前 host 可以在获得批准后写入；它不表示已经写入，dry-run 仍返回 `writes: []`。`mcp-readonly` 永远不会进入写入 ready 状态，并包含 `write_capability_unavailable`。无论调用方怎样描述外部 host capability，MCP server 自身始终 read-only（只读）。

全部阻断原因见共享的 [preflight contract](../skills/cobsidian/references/preflight.md)。

## Capability-based Degradation

这里的 capability-based degradation（按能力降级）保证结果与实际能力一致：

- `full-local` 和 `filesystem-only`：扫描、规划、请求批准，通过检测到的本地路径写入，再校验。
- `mcp-readonly`：没有批准写入路径时返回 zero-write dry-run 和待批准的改动计划，绝不声称修改了 vault。
- 校验不可用：保留已检测的 scan/write level，设置 `validation_available=false`、`ready=false`，并独立报告 `validation_capability_unavailable`。
- `chat-only`：返回可移植草稿，或请求一个可用 vault/config 路径；不声称得到了扫描支持的新建/追加结论。
- 证据缺失或检查失败：保持 `ready=false`，列出全部阻断原因，并 fail closed（失败关闭）。

拥有工具不等于检查已经完成。Preflight 字段记录实际完成的工作，不记录对 host 功能的预期。

## Adapter 对照

| Host 类型 | Adapter reference | 说明 |
|---|---|---|
| Codex CLI | [Codex](../skills/cobsidian/references/hosts/codex.md) | 从 `.agents/skills` 发现；可组合只读 MCP 和确定性本地写入器。 |
| Claude Code CLI | [Claude Code](../skills/cobsidian/references/hosts/claude-code.md) | 从 `.claude/skills` 发现；只使用当前会话实际暴露的工具。 |
| Kimi Code | [Kimi Code](../skills/cobsidian/references/hosts/kimi-code.md) | 发现 skill 后，分别检测本地与可选 MCP 路径。 |
| OpenCode | [OpenCode](../skills/cobsidian/references/hosts/opencode.md) | 使用 `.agents/skills`，可选接入本地 MCP。 |
| Pi | [Pi](../skills/cobsidian/references/hosts/pi.md) | 优先本地工具；MCP 来自 extension，不是 Pi 内置能力。 |
| Antigravity | [Antigravity](../skills/cobsidian/references/hosts/antigravity.md) | 使用 workspace `.agents/skills` 或官方全局 skill 目录。 |
| GitHub Copilot CLI | [GitHub Copilot CLI](../skills/cobsidian/references/hosts/github-copilot-cli.md) | 从 `.agents/skills` 发现；把 CLI 授权与 plan confirmation 分开。 |
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
5. 用 filename、清洗后的 H1、frontmatter title/aliases 和去模式前缀核心标题建立统一笔记身份。
6. 默认 dry-run；本地写入必须经过 `prepare → 精确 plan ID 确认 → 原子 apply → validate`，并支持 rollback。
7. 公共或通用笔记不写私人路径、密钥和原始聊天流水。

## 推荐提示词

```text
Use the Cobsidian workflow in skills/cobsidian/SKILL.md.
Detect the available capabilities, run a dry run, and report Knowledge Read and preflight.
Search existing notes before any proposed write, then wait for confirmation.
```

产品接入见 [集成说明](integrations.zh-CN.md)，MCP 工具和参数 parity 见 [MCP Server](mcp-server.zh-CN.md)。
