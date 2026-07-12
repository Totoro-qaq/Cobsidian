# Agent Compatibility

[简体中文](agent-compatibility.zh-CN.md)

Cobsidian is agent-agnostic. Compatibility depends on detected tools, not the host product name or an assumed feature set.

## Capability Detection

Every run starts with capability detection. Inspect actual access to the vault, local shell, filesystem edits, Cobsidian MCP tools/resources, and validation. Then map the host to exactly one level before making claims.

| Capability level | Scan | Dry-run | Agent write | Validation default | Use when |
|---|---:|---:|---:|---:|---|
| `full-local` | yes | yes | yes | yes | MCP-backed scan/dry-run and an approved write path are available. |
| `filesystem-only` | yes | yes | yes | yes | Local scan/dry-run and an approved write path are available without MCP. |
| `mcp-readonly` | yes | yes | no | yes | Scan and dry-run are available, but no approved write path exists, regardless of transport. |
| `chat-only` | no | no | no | no | The host cannot access or scan the target vault. |

Capability level records effective scan/write transport. Validation is reported independently through `validation_available`; if a write-capable host lacks validation, keep `full-local` or `filesystem-only`, set `validation_available=false`, and report `validation_capability_unavailable`. The historical name `mcp-readonly` is retained for compatibility. It is the transport-neutral effective read-only level and includes a local read-only host without MCP. `ready: true` means every required preflight check completed and the active host can proceed to an approved write. It does not mean a write happened; dry-run still returns `writes: []`. `mcp-readonly` is never write-ready and includes `write_capability_unavailable`. The MCP server itself remains read-only even if a caller describes another host capability.

See the shared [preflight contract](../skills/cobsidian/references/preflight.md) for all blocked reasons.

## Capability-based Degradation

This capability-based degradation preserves truthful results:

- `full-local` and `filesystem-only`: scan, plan, request approval, write through the detected local path, then validate.
- `mcp-readonly`: return the zero-write dry-run and an approved change plan when no approved write path exists; never claim a vault edit.
- Validation unavailable: retain the detected scan/write level, set `validation_available=false`, keep `ready=false`, and report `validation_capability_unavailable` independently.
- `chat-only`: return a portable draft or ask for one usable vault/config path; do not claim scan-derived create or append decisions.
- Missing or failed evidence: keep `ready=false`, report every blocked reason, and fail closed.

Possessing a tool is not evidence that a check completed. Preflight fields reflect completed work, not expected host features.

## Adapter Map

| Host family | Adapter reference | Notes |
|---|---|---|
| Codex CLI | [Codex](../skills/cobsidian/references/hosts/codex.md) | Discover from `.agents/skills`; combine optional read-only MCP with the deterministic local writer. |
| Claude Code CLI | [Claude Code](../skills/cobsidian/references/hosts/claude-code.md) | Discover from `.claude/skills`; use only tools exposed in the current session. |
| Kimi Code | [Kimi Code](../skills/cobsidian/references/hosts/kimi-code.md) | Discover the skill, then detect local and optional MCP paths independently. |
| OpenCode | [OpenCode](../skills/cobsidian/references/hosts/opencode.md) | Use `.agents/skills` plus an optional local MCP entry. |
| Pi | [Pi](../skills/cobsidian/references/hosts/pi.md) | Prefer its local tools; MCP is extension-provided, not a Pi core feature. |
| Antigravity | [Antigravity](../skills/cobsidian/references/hosts/antigravity.md) | Use workspace `.agents/skills` or the documented global skill path. |
| GitHub Copilot CLI | [GitHub Copilot CLI](../skills/cobsidian/references/hosts/github-copilot-cli.md) | Discover from `.agents/skills`; keep CLI approval separate from plan confirmation. |
| Cursor | [Cursor](../skills/cobsidian/references/hosts/cursor.md) | Treat editor and terminal access as separately detected capabilities. |
| Hermes | [Hermes](../skills/cobsidian/references/hosts/hermes.md) | Map the registered workflow and tools before execution. |
| Generic MCP host | [MCP](../skills/cobsidian/references/hosts/mcp.md) | Cobsidian's server is a zero-write inspection and planning surface. |

Thin adapters load the canonical router, one matching host reference, and one mode reference. They do not copy the entire workflow.

## Required Workflow Contract

Any compatible host must preserve these rules:

1. Resolve the target vault before vault operations.
2. Scan before proposing a write when scan capability exists.
3. Keep `decision.action` to `create | append | blocked`; report split separately as a `multi-note` plan.
4. Prefer append over a near-duplicate and link only to confirmed notes.
5. Build one note identity from filename, cleaned H1, frontmatter title and aliases, and prefix-free core titles.
6. Dry-run by default; for local writes require `prepare → exact plan-ID confirmation → atomic apply → validate`, with rollback support.
7. Keep private paths, secrets, and raw chat logs out of public or generic notes.

## Suggested Prompt

```text
Use the Cobsidian workflow in skills/cobsidian/SKILL.md.
Detect the available capabilities, run a dry run, and report Knowledge Read and preflight.
Search existing notes before any proposed write, then wait for confirmation.
```

Product setup is documented in [Integrations](integrations.md); MCP tools and parameter parity are documented in [MCP Server](mcp-server.md).
