# Cobsidian 模式说明

[English](modes.md)

模式描述 Cobsidian 要交付给用户的结果。它会影响整理深度和 mode-level note plan；dry-run 则用另一份契约记录机器可以新建、追加，还是必须阻断。

## 自然语言路由

Cobsidian 使用 natural-language routing（自然语言路由），用户不需要记住模式 ID。

- 用户明确指定模式：使用该 canonical mode，并在结果中说明。
- 意图清晰：根据目标推断一个模式，并说明选择。
- 请求有歧义：保持模式未决，at most two（最多推荐两个）相关模式。
- 一两个上下文选项足够时，不展示完整七项菜单。

`recommended_modes` 只在 `mode` 未决时使用，包含零到两个 canonical mode ID，不会用未支持的值代替。

## 结果速查

| 用户想得到的结果 | Canonical mode | 默认深度 | 默认粒度 | 详细契约 |
|---|---|---|---|---|
| 理解概念，整理课程、论文、视频或技术解释 | `learning` | `standard` | `single-note` | [学习模式](../skills/cobsidian/references/modes/learning.md) |
| 维护自己项目的上下文、架构、实现或运维记录 | `project` | `deep` | `single-note` | [项目模式](../skills/cobsidian/references/modes/project.md) |
| 解释事故、失败实验、决策和经验教训 | `review` | `deep` | `single-note` | [复盘模式](../skills/cobsidian/references/modes/review.md) |
| 对比方案并明确展示取舍 | `comparison` | `standard` | `single-note` | [对比模式](../skills/cobsidian/references/modes/comparison.md) |
| 创建主题总览、知识地图、学习路线或导航页 | `index` | `deep` | `multi-note` | [索引模式](../skills/cobsidian/references/modes/index.md) |
| 尽量不打断当前工作，快速保存有价值的粗糙材料 | `capture` | `capture` | `single-note` | [捕获模式](../skills/cobsidian/references/modes/capture.md) |
| 从工具、仓库、skill、prompt 或工作流提取内部机制与可复用模式 | `dissection` | `deep` | `multi-note` | [拆解模式](../skills/cobsidian/references/modes/dissection.md) |

这些默认值会进入 Knowledge Read。证据级别仍从 `conversation` 开始。证据升级必须提交 host-completed facts（host 已完成动作的事实）：`source-grounded` 要求 `source_read_completed=true`，`verified` 同时要求 `source_read_completed=true` 和 `verification_completed=true`。模式选择或用户声称都不会自动升级证据。

## 机器动作与笔记计划

Dry-run 的机器动作和 mode-level note plan 是两份不同契约：

- `decision.action`: `create | append | blocked`
- mode-level note plan: `single-note | multi-note | report-only`

拆分要求以 `multi-note` 计划汇报，不是第四种机器动作。请求 `granularity=append` 时，只有 `decision.action=append` 合法；重复检查决定追加到已有笔记时，Knowledge Read 始终强制 append granularity。`report-only` 描述不写入的用户结果，不是 Knowledge Read 的 `granularity` 枚举。

## 用户会得到什么

- `learning`：便于以后复习的长期解释。
- `project`：当前项目上下文、实现证据、风险和下一步。
- `review`：原因、决策、教训和后续行动。
- `comparison`：由明确取舍支撑的简洁结论。
- `index`：可导航的链接和已有笔记阅读路径。
- `capture`：简短、可检索，并明确留待后续整理的记录。
- `dissection`：入口、内部流程、证据、可复用模式和边界。

详细标题、证据规则、拆分条件和校验要求只放在 [`skills/cobsidian/references/modes/`](../skills/cobsidian/references/modes/) 中。本文只讲用户可见结果和路由，不复制完整操作 prompt。
