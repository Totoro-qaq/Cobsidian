# Cobsidian

[English](../README.md) | 简体中文

[![validate](https://github.com/Totoro-qaq/Cobsidian/actions/workflows/validate.yml/badge.svg)](https://github.com/Totoro-qaq/Cobsidian/actions/workflows/validate.yml)
[![codeql](https://github.com/Totoro-qaq/Cobsidian/actions/workflows/codeql.yml/badge.svg)](https://github.com/Totoro-qaq/Cobsidian/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

<p align="center">
  <img src="assets/cobsidian-banner.svg" alt="Cobsidian - 用你的编程 Agent 维护一个相互连接的 Obsidian 知识库。" width="100%" />
</p>

> 安全地把 AI 对话整理成带双链的 Obsidian 知识库。

Cobsidian 是一个 agent-agnostic 的 Obsidian / Markdown 知识库维护工作流 Skill。它让 Agent 把对话、学习材料、日志、文档和项目分析整理成长期可维护的笔记，并在写入前检查重复内容、补充 `[[双链]]`、建议反链、做基础校验。

[快速开始](#快速开始) · [MCP Server](mcp-server.zh-CN.md) · [Prompt Examples](../examples/prompts.md) · [Agent 兼容性](agent-compatibility.zh-CN.md)

用你熟悉的 Agent 就行——Cobsidian 可以接入 [Claude Code](../skills/cobsidian/references/hosts/claude-code.md)、[Codex CLI](../skills/cobsidian/references/hosts/codex.md)、[GitHub Copilot CLI](../skills/cobsidian/references/hosts/github-copilot-cli.md)、[Kimi Code](../skills/cobsidian/references/hosts/kimi-code.md)、[OpenCode](../skills/cobsidian/references/hosts/opencode.md)、[Pi](../skills/cobsidian/references/hosts/pi.md) 和 [Antigravity](../skills/cobsidian/references/hosts/antigravity.md)。

<p align="center">
  <img src="assets/cobsidian-demo.gif" alt="Cobsidian 工作流：匹配已有笔记 → 审阅改动 → 安全写入 → 生长知识图谱" width="100%" />
</p>

## Cobsidian 做什么

- 把 AI 对话里有复用价值的内容整理成长期可维护的 Markdown 笔记。
- 写入前先扫描已有笔记，优先追加或合并，减少重复笔记。
- 用结构化 Knowledge Read（`整理判读`）说明准备怎样整理。
- 通过 dry-run、capability-based degradation（按 capability 降级）、反链建议和校验结果，让 Agent 写入变得可审阅。

## 快速开始

```bash
git clone https://github.com/Totoro-qaq/Cobsidian.git
cd Cobsidian
python skills/cobsidian/scripts/dry_run.py examples/demo-vault --topic "AI Conversations" --mode learning --text "agent workflow notes" --json
```

然后让 Agent 读取 `skills/cobsidian/SKILL.md`，并提供 vault 路径或 `cobsidian.config.yml`。

```text
Use Cobsidian to organize this material into my Obsidian vault.
Vault: /absolute/path/to/obsidian-vault
Run a dry run first, check duplicates, suggest backlinks, and wait for confirmation before writing.
```

## 前后对比

```mermaid
flowchart LR
    A["AI 对话、日志、项目分析"] --> B["Cobsidian dry run"]
    B --> C["扫描已有 vault 笔记"]
    C --> D{"机器动作<br/>create | append | blocked"}
    D --> E["笔记计划<br/>single-note | multi-note | report-only<br/>split = multi-note"]
    E --> F["结构清晰的 Markdown 笔记"]
    F --> G["双链和相关笔记"]
    G --> H["经过校验的 Obsidian vault"]
```

| 使用前 | 使用后 |
|---|---|
| 有价值内容留在聊天记录里 | 进入你的 Obsidian vault |
| 零散 Markdown 文件 | 带 `[[双链]]` 的知识网络 |
| 重复问一次就多一篇重复笔记 | 分层汇报机器动作与笔记计划 |
| Agent 直接写入，不好审 | dry-run 先给计划，再确认写入 |

## Dry-run 预览

Dry run 是默认安全路径：只规划，不写文件；它会报告重复风险、目标笔记和建议反链，并保持 `writes` 为空。

```json
{
  "dry_run": true,
  "mode": "learning",
  "decision": {
    "action": "append",
    "target_note": "AI Conversations.md"
  },
  "suggested_backlinks": [
    {
      "title": "Agent Workflows",
      "path": "Agent Workflows.md"
    }
  ],
  "writes": []
}
```

## Knowledge Read / 整理判读

v0.5.0 会在写入前计算 Knowledge Read（整理判读），说明模式、整理深度、笔记粒度、证据级别和展示方式。`auto | always | off` 只控制对话里的展示：选择 `off` 时，`display_style` 为 `hidden`，但 dry-run 仍保留完整 JSON 对象。

Capability-based degradation 会根据实际工具能力降级：本地主机完成检查后可以进入待批准写入状态，MCP 始终只读，chat-only 主机只返回草稿或请求一个可用路径，不会声称完成了无法执行的操作。

以下示例都是 JSON 响应中字段完全一致的 `knowledge_read` 对象。

### Compact Knowledge Read

用户明确选择简单的学习任务时，使用紧凑展示：

```json
{
  "mode": "learning",
  "mode_explicit": true,
  "recommended_modes": [],
  "depth": "standard",
  "granularity": "single-note",
  "evidence": "conversation",
  "display_policy": "auto",
  "display_style": "compact"
}
```

### Expanded Knowledge Read

Agent 推断出的深度源码拆解会展开说明：

```json
{
  "mode": "dissection",
  "mode_explicit": false,
  "recommended_modes": [],
  "depth": "deep",
  "granularity": "multi-note",
  "evidence": "source-grounded",
  "display_policy": "auto",
  "display_style": "expanded"
}
```

Dry-run 的机器动作只有 `create | append | blocked`。拆分属于单独的 mode-level note plan，以 `multi-note` 汇报，不是第四种机器动作。详细执行规则见 [模式与 host references](../skills/cobsidian/references/) 和共享的 [preflight contract](../skills/cobsidian/references/preflight.md)。

## 不是普通 Markdown 生成器

| 普通 Markdown 生成 | Cobsidian |
|---|---|
| 生成一篇孤立文件 | 维护一个带链接的知识系统 |
| 不看已有笔记 | 写入前扫描 vault |
| 容易重复建主题 | 区分 create/append/blocked 动作与笔记形态 |
| 链接靠临场发挥 | 根据已有笔记建议反链 |
| 直接写入 | 支持 dry-run 审阅后再写 |

## Obsidian Vault 工作流

```mermaid
flowchart TD
    U["用户材料"] --> R["解析 vault 路径或配置"]
    R --> S["扫描笔记、标题、标签、双链"]
    S --> A{"机器动作<br/>create | append | blocked"}
    A --> P["笔记计划<br/>single-note | multi-note | report-only<br/>split = multi-note"]
    P --> L["建议反链"]
    L --> V["校验笔记卫生"]
    V --> O["汇报文件、决策、链接和校验结果"]
```

## 功能

- 创建学习笔记、项目笔记、对比笔记、索引笔记。
- 用 filename、清洗后的 H1、frontmatter `title`/`aliases` 与去模式前缀核心标题建立统一笔记身份，减少重复。
- 根据笔记标题、元数据和正文建议 `[[双链]]` 与 Related notes 区块。
- 使用确定性的中文 bigram/trigram 匹配相关短语。
- 校验缺失的 wiki-link 目标。
- 检测完全重复或高度相似的笔记标题。
- 保持笔记结构简洁、可复用。
- 默认避免写入私人路径、密钥和原始聊天流水。
- 提供带分页的本地 MCP tools，用于只读检查和 dry-run 规划。
- 生成带完整性哈希的 diff，要求精确 plan ID 确认，原子写入并支持校验失败自动回滚与手动 rollback。
- 用标注查询集评估 duplicate precision/recall、backlink precision@3、追加目标准确率和 mode accuracy。

## 安装

完整安装、更新和卸载说明见 [INSTALL.md](../INSTALL.md)。
Codex、Obsidian vault、MCP host 和其他 Agent 的接入方式见 [集成说明](integrations.zh-CN.md)。

### 支持的 CLI Skill

一次适配 Kimi Code、OpenCode、Pi、Antigravity、GitHub Copilot CLI、Codex CLI 和 Claude Code CLI：

```bash
python install_cobsidian.py --host all --scope user --dry-run --json
python install_cobsidian.py --host all --scope user
```

也可以手工复制共享 Agent Skills 目录：

把 skill 目录复制到 Agent 的 skills 目录：

```bash
mkdir -p ~/.agents/skills
cp -r skills/cobsidian ~/.agents/skills/cobsidian
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills" | Out-Null
Copy-Item -Recurse -Force .\skills\cobsidian "$env:USERPROFILE\.agents\skills\cobsidian"
```

每个 CLI 的用户级/项目级发现路径和 MCP 配置见 [集成说明](integrations.zh-CN.md)。Pi 没有内置 MCP client，默认直接走本地工作流。

### 其他 Agent

Hermes、Cursor 和其他 Agent 使用同一套核心工作流：

1. 让 Agent 读取 `skills/cobsidian/SKILL.md`。
2. 允许它调用 `skills/cobsidian/scripts/` 里的辅助脚本。
3. 要求它汇报新建/追加判断、重复检查、反链改动和校验结果。

详见 [Agent 兼容性](agent-compatibility.zh-CN.md) 和 [集成说明](integrations.zh-CN.md)。

### MCP Server

Cobsidian 也提供本地 MCP server，适合支持 Model Context Protocol 的 host 使用。

```bash
python -m pip install -r requirements-mcp.txt
python skills/cobsidian/mcp_server.py
```

建议作为本地 `stdio` server 使用，并配置 `COBSIDIAN_CONFIG` 或 `COBSIDIAN_VAULT`。

详见 [MCP Server](mcp-server.zh-CN.md)。

## Agent 用法

可直接复制的提示词见 [Prompt Examples](../examples/prompts.md)。

当你希望 Agent 把材料写入 Obsidian 时，可以这样说：

```text
Use Cobsidian to turn this conversation into an Obsidian learning note.
Check whether it should create a new note or append to an existing one.
Add useful wiki links and report possible duplicates.
```

更多例子：

```text
Use Cobsidian to summarize these logs into my Obsidian vault.
Preserve only reusable lessons, check for existing related notes, and add backlinks.
```

```text
Use Cobsidian to compare these two project attempts and write a comparison note.
If a related note already exists, append instead of creating a duplicate.
```

## 模式

Cobsidian 接受显式模式，也能按自然语言路由。意图清晰时只推断一个模式；有歧义时最多推荐两个相关模式，不展示完整七项菜单。用户结果与路由规则见 [模式说明](modes.zh-CN.md)，详细执行契约见 [mode references](../skills/cobsidian/references/modes/)。

## CLI 工具

需要确定性检查时，可以直接运行脚本：

```bash
python skills/cobsidian/scripts/scan_vault.py /path/to/vault --json
python skills/cobsidian/scripts/find_duplicates.py /path/to/vault
python skills/cobsidian/scripts/suggest_backlinks.py /path/to/vault --file draft.md
python skills/cobsidian/scripts/validate_notes.py /path/to/vault
python skills/cobsidian/scripts/dry_run.py /path/to/vault --topic "RAG" --text "draft text" --json
python skills/cobsidian/scripts/write_executor.py prepare /path/to/vault --action append --target-note "RAG.md" --content-file draft.md --plan-out /tmp/cobsidian-plan.json
python skills/cobsidian/scripts/write_executor.py apply /path/to/vault --plan /tmp/cobsidian-plan.json --confirm PLAN_ID --json
python skills/cobsidian/scripts/quality_eval.py evals/public-smoke.jsonl evals/fixtures/public-vault --mode-predictions evals/public-mode-predictions.jsonl --json
```

当配置里写了 `vault.path` 时，这些脚本也支持 `--config cobsidian.config.yml`。

## 可选配置

`cobsidian.config.example.yml` 是当前支持的配置面，包含 vault 路径、默认模式、模式目录、Knowledge Read 展示、反链数量、重复阈值与追加偏好，以及校验行为。需要复用本地设置时，可以复制为 `cobsidian.config.yml`。

```yaml
interaction:
  knowledge_read: auto
```

`interaction.knowledge_read` 只接受 `auto`、`always`、`off`。旧配置仍然有效，因为默认值是 `auto`。

辅助脚本可以通过 `--config` 读取这个文件。

命名模板、脱敏和写入策略尚未由配置强制执行，仍属于路线图内容。

## 路线图

- 超越身份标题相似度的语义重复检测。
- 在更大、更多样的真实标注 vault benchmark 上调优反链排序。
- 可选笔记模板。
- 可配置命名规则。
- 工作流稳定后再考虑 Obsidian 插件集成。

## 贡献

欢迎贡献。请阅读 [CONTRIBUTING.md](../CONTRIBUTING.md)。

不要提交私人知识库内容、个人路径、API key、未公开笔记或私人知识库截图。

## 商标和独立性声明

Cobsidian 是独立开源项目。OpenAI、Codex、Obsidian、Claude、Cursor、Hermes 以及其他名称均属于各自权利人。本项目不隶属于这些权利人，也未获得其背书或赞助。

## License

MIT. See [LICENSE](../LICENSE).
