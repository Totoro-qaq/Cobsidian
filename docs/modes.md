# Cobsidian Modes

[简体中文](modes.zh-CN.md)

Cobsidian modes help users tell the agent what kind of note they want. The mode affects the note structure, level of polish, and create/append decision.

If the user does not choose a mode, the agent should infer one and report the inferred mode before or after writing.

## Quick Selection

| If you want to... | Use |
|---|---|
| Learn a concept or summarize a course/video/article | Learning |
| Document a project, repo, architecture, or implementation | Project |
| Analyze what happened and what to improve next time | Review |
| Choose between options | Comparison |
| Build a topic hub or learning path | Index |
| Save rough notes quickly | Daily Capture |
| Break down how a tool/framework/repo/skill works | Dissection |

## Learning Mode

Use for concepts, courses, papers, videos, articles, and technical explanations.

Best for:

- "Explain this and save it to my vault."
- "Turn this video summary into a learning note."
- "Organize these concepts with related notes."

Typical sections:

- Summary
- Core Concepts
- Workflow or Mental Model
- Common Mistakes
- Related Notes

## Project Mode

Use for a concrete project, repository, codebase, feature, architecture, implementation, or operation.

Best for:

- repo analysis
- architecture notes
- implementation logs
- deployment and operation notes

Typical sections:

- Context
- Goal
- Architecture or Implementation
- Evidence
- Result
- Risks and Next Steps
- Related Notes

## Review Mode

Use for incidents, failed experiments, training runs, debugging sessions, decisions, and lessons learned.

Best for:

- "Why did this fail?"
- "Write a postmortem."
- "Compare the attempt, fix, and remaining risk."

Typical sections:

- Context
- Timeline
- Symptoms
- Root Cause
- Fix or Decision
- Lessons
- Next Steps

## Comparison Mode

Use when the value is in comparing options.

Best for:

- tool selection
- model selection
- database selection
- architecture tradeoffs
- version-to-version comparison

Typical sections:

- Short Conclusion
- Comparison Table
- Decision Rules
- Recommended Use Cases
- Related Notes

## Index Mode

Use for topic maps, learning paths, navigation pages, and hub notes.

Best for:

- "Build a learning roadmap."
- "Make a hub note for this topic."
- "Organize these notes into a map."

Typical sections:

- Map
- Core Notes
- Project Notes
- Open Questions
- Next Learning Path

## Daily Capture Mode

Use when the material is worth saving but not ready for a polished note.

Best for:

- quick ideas
- rough chat output
- short daily learning
- links to revisit
- temporary notes that should not block the current flow

Typical sections:

- Capture
- Useful Points
- Possible Links
- Follow-up

Keep it short. The goal is retrieval, not polish.

## Dissection Mode

Use when breaking down how something works internally.

Best for:

- source-code analysis
- framework analysis
- agent systems
- workflow or harness design
- prompt/skill repositories
- products such as Claude Code, Superpowers, OpenSpec, Hermes-like systems

Typical sections:

- Object of Study
- Purpose
- Entry Points
- Core Concepts
- Architecture or Flow
- Key Files or Components
- Reusable Patterns
- Limits and Open Questions
- Related Notes

Dissection mode is different from project mode: project mode documents your own project; dissection mode extracts reusable patterns from something you are studying.

