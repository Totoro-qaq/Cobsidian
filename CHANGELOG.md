# Changelog

## Unreleased

## v0.6.0

- Add a real note identity model spanning filename title, cleaned H1, frontmatter `title` and `aliases`, and prefix-free core titles.
- Match duplicates across all identity candidates and weight identity metadata in backlink ranking.
- Add labeled JSONL quality evaluation for duplicate precision/recall, append targets, backlink precision@k, and mode accuracy, including a 60-query private local benchmark excluded from Git.
- Add deterministic `prepare → confirm → atomic apply → validate → rollback` writes with integrity hashes, stale-plan protection, transaction records, and automatic rollback on new warnings.
- Add tested skill installation and host adapters for Kimi Code, OpenCode, Pi, Antigravity, GitHub Copilot CLI, Codex CLI, and Claude Code CLI.
- Refresh the minimal banner and light Obsidian demo around identity-aware matching, safe writes, and a growing knowledge graph.

## v0.5.0

- Add adaptive routing that loads one relevant mode reference and recommends at most two modes when intent is unresolved.
- Add progressive mode and host references for user outcomes, execution rules, capability detection, and degradation.
- Add structured Knowledge Read / `整理判读` output with compact, expanded, and hidden presentation while preserving complete JSON.
- Add deterministic preflight readiness, completed-check evidence, and ordered blocked reasons for four capability levels.
- Enforce the `interaction.knowledge_read` config surface with `auto`, `always`, and `off`, defaulting existing configs to `auto`.
- Add CLI/MCP parity for adaptive dry-run context while preserving existing callers and keeping MCP read-only.
- Include compatibility and safety fixes for scanless hosts, MCP vault-resolution errors, read-only tool registration, and machine-action boundaries.

## v0.4.0

- Validate Agent Skill YAML frontmatter in tests and CI.
- Use one body-aware backlink ranker across CLI, dry-run, and MCP.
- Use the same optional topic-plus-text query contract across all backlink entry points, including topic-only queries and consistent empty-query rejection.
- Add deterministic CJK bigram/trigram matching for Chinese notes.
- Normalize prose punctuation while preserving technical tokens such as `C++17`, `C#`, `node.js`, and `.venv`.
- Stream note bodies during backlink ranking and retain at most the configured result limit.
- Validate backlink limits from `1` to `100`.
- Publish only configuration fields that scripts and MCP tools enforce.
- Paginate MCP vault scans and bound similar-title work to unique normalized titles.
- Preserve the complete static vault-summary resource and add a bounded vault-page resource.
- Keep exact duplicate-title detection complete when fuzzy work is truncated.
- Remove owner-specific workflow rules from the public Claude/OpenCode adapter.
- Add Codex, Obsidian vault, MCP host, and other-agent integration guides.
- Add trademark and independence notices.
- Replace local machine paths in setup examples with neutral absolute-path placeholders.
- Update current status wording from MVP to usable public early release.
- Refresh English and Chinese README landing sections with banner, quick start, workflow diagrams, dry-run preview, and generator comparison.
- Add a local glassmorphism SVG banner for README landing sections.
- Fix README banner label centering and decorative-line overlap.

## v0.3.0

- Add local MCP server with read/planning tools, prompts, and safe note resources.

## v0.2.0

- Add installation guide, prompt examples, and example config conventions.
- Add config-aware helper scripts and dry-run JSON planning.

## v0.1.0

Initial public MVP:

- Cobsidian skill workflow for Obsidian knowledge-base maintenance.
- Learning, project, review, comparison, index, daily capture, and dissection modes.
- Duplicate title detection, vault scanning, backlink suggestions, and note validation scripts.
- English and Chinese documentation.
- CI validation for helper scripts and examples.
