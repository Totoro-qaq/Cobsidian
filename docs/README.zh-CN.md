# Cobsidian

[English](../README.md) | 简体中文

Cobsidian 是一个 agent-agnostic 的 Obsidian 知识库维护工作流 Skill。

它可以帮助 Agent 把对话、学习材料、日志、文档和项目分析整理成长期可维护的 Markdown 笔记，并在写入前检查重复内容、补充 `[[双链]]`、建议反链、做基础知识库校验。

它的目标不是“生成一篇 Markdown”，而是维护一个可持续增长的 Obsidian 知识系统。

## 为什么需要 Cobsidian

AI 对话里经常产生有价值的信息，但这些内容通常留在聊天记录里，或者变成孤立的 Markdown 文件。Cobsidian 给 Agent 一套可复用流程：

```text
输入材料
-> 搜索已有笔记
-> 判断新建 / 追加 / 拆分
-> 写成干净 Markdown
-> 添加有用的 [[双链]]
-> 建议反链
-> 校验基础知识库卫生
```

## 功能

- 创建学习笔记、项目笔记、对比笔记、索引笔记。
- 写入前检查已有笔记，减少重复。
- 建议 `[[双链]]` 和 Related notes 区块。
- 校验缺失的 wiki-link 目标。
- 检测完全重复或高度相似的笔记标题。
- 保持笔记结构简洁、可复用。
- 默认避免写入私人路径、密钥和原始聊天流水。

## 当前状态

早期 MVP。

当前版本以 Codex 兼容 Skill 的形式发布，并提供一组小型 Python 工具；但工作流本身刻意设计成可迁移到 Hermes、Claude Code、Cursor 以及其他可以读取项目指令并执行本地命令的 coding agents。

它不是 Obsidian 插件，不是云同步服务，也不是向量数据库。

## 安装

### Codex Skill

把 skill 目录复制到 Agent 的 skills 目录：

```bash
cp -r skills/cobsidian ~/.codex/skills/cobsidian
```

Windows PowerShell：

```powershell
Copy-Item -Recurse -Force .\skills\cobsidian "$env:USERPROFILE\.codex\skills\cobsidian"
```

### 其他 Agent

Hermes、Claude Code、Cursor 和其他 Agent 使用同一套核心工作流：

1. 让 Agent 读取 `skills/cobsidian/SKILL.md`。
2. 允许它调用 `skills/cobsidian/scripts/` 里的辅助脚本。
3. 要求它汇报新建/追加判断、重复检查、反链改动和校验结果。

详见 [Agent 兼容性](agent-compatibility.zh-CN.md)。

## Agent 用法

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

## CLI 工具

需要确定性检查时，可以直接运行脚本：

```bash
python skills/cobsidian/scripts/scan_vault.py /path/to/vault --json
python skills/cobsidian/scripts/find_duplicates.py /path/to/vault
python skills/cobsidian/scripts/suggest_backlinks.py /path/to/vault --file draft.md
python skills/cobsidian/scripts/validate_notes.py /path/to/vault
```

### `scan_vault.py`

汇总 Markdown 笔记、标题、标签和双链。

```bash
python skills/cobsidian/scripts/scan_vault.py examples --json
```

### `find_duplicates.py`

查找完全重复或高度相似的笔记标题。

```bash
python skills/cobsidian/scripts/find_duplicates.py examples
```

### `suggest_backlinks.py`

根据草稿或文本建议相关笔记。

```bash
python skills/cobsidian/scripts/suggest_backlinks.py examples --text "vector search and RAG evaluation"
```

### `validate_notes.py`

检查缺失双链目标、重复标题和空笔记。

```bash
python skills/cobsidian/scripts/validate_notes.py examples --strict
```

## 仓库结构

```text
Cobsidian/
├── skills/cobsidian/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/
│   │   ├── backlink-policy.md
│   │   ├── markdown-style.md
│   │   └── note-types.md
│   └── scripts/
├── examples/
├── docs/
├── .github/workflows/
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## 工作流

Agent 使用 Cobsidian 时，应遵循：

1. 确认 vault 路径和目标主题。
2. 写入前先搜索已有笔记。
3. 判断是新建、追加、拆分，还是先询问用户。
4. 写成结构清晰的 Markdown。
5. 添加有价值的双链和相关笔记。
6. 运行校验，或说明为什么没有校验。
7. 返回简短变更摘要。

## 路线图

- 更好的重复检测和可配置阈值。
- 支持使用 YAML frontmatter 的 vault。
- 可选笔记模板。
- 可配置命名规则。
- 更安全的 dry-run 模式。
- Hermes、Claude Code、Cursor 的轻量适配层。
- 工作流稳定后再考虑 Obsidian 插件集成。

## 贡献

欢迎贡献。请阅读 [CONTRIBUTING.md](../CONTRIBUTING.md)。

不要提交私人知识库内容、个人路径、API key、未公开笔记或私人知识库截图。

## Cobsidian 不是什么

- 不是 Obsidian 插件。
- 不是云同步服务。
- 不是向量数据库。
- 不是可以不经审阅自动改库的写入器。
- 不是人类编辑判断的替代品。

## License

MIT. See [LICENSE](../LICENSE).
