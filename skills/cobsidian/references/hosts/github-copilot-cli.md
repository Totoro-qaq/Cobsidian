# GitHub Copilot CLI Adapter

## Detect Capabilities

Inspect the actual available tools before choosing a capability level. Check GitHub Copilot CLI filesystem reads, search, shell, edit, configured MCP tools, and validation access separately. Skill discovery and MCP registration are not evidence that the current session can reach the vault.

## Capability Mapping

- Use `full-local` only when MCP-backed scan and dry-run plus an approved write path are actually available through detected tools.
- Use `filesystem-only` only when local scan, dry-run, and an approved write path are available without MCP.
- Use `mcp-readonly` when scan and dry-run are available but there is no approved write path, including local read-only operation without MCP.
- Use `chat-only` when no scan path can reach the target vault.

The historical name `mcp-readonly` is retained for compatibility; it is the transport-neutral effective read-only level, including a local read-only host without MCP. Capability level records scan and write transport. Report validation independently with `validation_available`; when validation is absent, keep `full-local` or `filesystem-only`, set `validation_available=false`, and let [preflight](../preflight.md) report `validation_capability_unavailable`.

## Execution Path

Use the discovered Cobsidian skill and exposed shell or file tools for identity-aware scan, dry-run, and validation. For local writes, call `write_executor.py prepare`, show the diff and plan ID, require that exact ID, and call `write_executor.py apply`. A registered Cobsidian MCP server supplies read-only inspection and planning only.

## Degradation

Without an approved write path, retain `mcp-readonly` and return a concrete change plan. If write exists but validation is unavailable, retain the write-capable level and report the independent validation block. Without vault scan access, use `chat-only` and return a portable draft or request a usable path.

## Safety

Use [preflight](../preflight.md) as the readiness authority. Keep Copilot CLI tool approval separate from Cobsidian's exact plan-ID confirmation, and never claim that skill or MCP discovery implies a completed operation.
