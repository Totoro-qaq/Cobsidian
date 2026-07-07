# Agent 兼容性

Cobsidian 设计成 agent-agnostic workflow，也就是不绑定某一个具体工具。

核心契约很简单：

```text
读取工作流说明
-> 检查 Obsidian vault
-> 判断新建 / 追加 / 拆分
-> 写 Markdown
-> 添加双链和反链建议
-> 运行校验
-> 汇报改动
```

## 兼容矩阵

| Agent | 支持级别 | 推荐用法 |
|---|---|---|
| Codex | 一等支持 | 把 `skills/cobsidian` 安装成 Codex skill。 |
| MCP hosts | 本地 server 一等支持 | 通过本地 `stdio` 启动 `skills/cobsidian/mcp_server.py`。 |
| Hermes | 可移植工作流 | 把 `skills/cobsidian/SKILL.md` 注册或引用成本地 workflow/skill，并允许执行脚本。 |
| Claude Code | 可移植工作流 | 在项目指令或本地 skill 设置中引用 `skills/cobsidian/SKILL.md`，然后通过终端运行脚本。 |
| Cursor | 可移植工作流 | 在 Cursor rules 或项目指令中引用该工作流，通过集成终端运行脚本。 |
| 其他 coding agents | 可移植工作流 | 把 `SKILL.md` 作为指令，并暴露 Python 脚本。 |

## 必须保留的行为

任何适配层都应该保留这些行为：

1. 写入前先搜索。
2. 优先追加或合并，避免重复笔记。
3. 添加有价值的 `[[双链]]`，不要关键词刷屏。
4. 汇报是否运行了校验。
5. 默认避免私人路径、密钥和原始聊天流水。

## 适配策略

不要为每个 Agent 复制一整套工作流。

规范说明只保留一份：

```text
skills/cobsidian/SKILL.md
skills/cobsidian/references/
skills/cobsidian/scripts/
```

各工具适配层应该很薄：

```text
adapter = 这个 agent 如何加载 Cobsidian
core = Cobsidian 要求 agent 做什么
```

对于 MCP host，adapter 就是 `skills/cobsidian/mcp_server.py`。详见 [MCP Server](mcp-server.zh-CN.md)。

## 推荐提示词

通用提示词：

```text
Use the Cobsidian workflow in skills/cobsidian/SKILL.md.
Organize this material into my Obsidian vault.
Search existing notes first, decide create vs append, add useful wiki links, and run validation if possible.
```

更安全的 dry-run 提示词：

```text
Use the Cobsidian workflow in skills/cobsidian/SKILL.md.
Do not edit files yet. First report the target note, duplicate risks, suggested backlinks, and proposed Markdown outline.
```
