# Cobsidian 模式说明

[English](modes.md)

Cobsidian 的模式用于告诉 Agent：这次要生成哪一类笔记。模式会影响笔记结构、整理深度，以及是新建、追加还是拆分。

如果用户没有指定模式，Agent 应该自动推断，并在结果中说明使用了哪个模式。

用户不应该必须先读这个文档。实际交互时，如果请求比较宽泛、有歧义，或者同一份材料可能整理成不同形态，Agent 应该先用很短的方式介绍可选模式；如果模式很明显，则直接说明推断出的模式并继续执行。

## 快速选择

| 你想做什么 | 使用模式 |
|---|---|
| 学一个概念，整理课程、视频、文章 | 学习模式 |
| 整理项目、仓库、架构、实现 | 项目模式 |
| 分析发生了什么，下次怎么避免 | 复盘模式 |
| 在多个方案之间做选择 | 对比模式 |
| 建主题总览、学习路线、导航页 | 索引模式 |
| 先快速保存粗糙材料 | 日常捕获模式 |
| 拆解一个工具、框架、仓库、skill 的工作方式 | 拆解模式 |

## 学习模式

用于概念、课程、论文、视频、文章和技术解释。

适合：

- “解释一下这个并存到知识库。”
- “把这个视频总结整理成学习笔记。”
- “把这些概念整理并补相关链接。”

常见结构：

- Summary
- Core Concepts
- Workflow or Mental Model
- Common Mistakes
- Related Notes

## 项目模式

用于具体项目、仓库、代码库、功能、架构、实现和运维。

适合：

- 仓库分析
- 架构笔记
- 实现记录
- 部署和运维记录

常见结构：

- Context
- Goal
- Architecture or Implementation
- Evidence
- Result
- Risks and Next Steps
- Related Notes

## 复盘模式

用于事故、失败实验、训练记录、调试过程、技术决策和经验总结。

适合：

- “这次为什么失败？”
- “写一个复盘。”
- “对比尝试、修复和剩余风险。”

常见结构：

- Context
- Timeline
- Symptoms
- Root Cause
- Fix or Decision
- Lessons
- Next Steps

## 对比模式

用于多个选项之间的比较。

适合：

- 工具选型
- 模型选型
- 数据库选型
- 架构取舍
- 版本对比

常见结构：

- Short Conclusion
- Comparison Table
- Decision Rules
- Recommended Use Cases
- Related Notes

## 索引模式

用于主题地图、学习路线、导航页和总览笔记。

适合：

- “做一个学习路线。”
- “给这个主题建一个总览页。”
- “把这些笔记组织成知识地图。”

常见结构：

- Map
- Core Notes
- Project Notes
- Open Questions
- Next Learning Path

## 日常捕获模式

用于材料值得保存，但还不值得深度整理的时候。

适合：

- 临时想法
- 粗糙聊天输出
- 今日短学习
- 待回看链接
- 不想打断当前流程的临时记录

常见结构：

- Capture
- Useful Points
- Possible Links
- Follow-up

保持简短。目标是以后能搜到，不是当场写漂亮。

## 拆解模式

用于拆解一个东西内部是怎么工作的。

适合：

- 源码分析
- 框架分析
- Agent 系统
- 工作流或 harness 设计
- prompt / skill 仓库
- Claude Code、Superpowers、OpenSpec、Hermes 这类系统或案例

常见结构：

- Object of Study
- Purpose
- Entry Points
- Core Concepts
- Architecture or Flow
- Key Files or Components
- Reusable Patterns
- Limits and Open Questions
- Related Notes

拆解模式和项目模式不同：项目模式记录你自己的项目；拆解模式从你研究的对象里抽取可复用模式。
