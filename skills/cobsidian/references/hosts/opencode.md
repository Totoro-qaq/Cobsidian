# OpenCode Adapter

## Detect Capabilities

Inspect the actual available tools before choosing a capability level. Check OpenCode read, search, shell, edit, configured MCP tools, and validation access as separate facts. Its skill discovery and MCP configuration do not by themselves prove vault access.

## Capability Mapping

- Use `full-local` only when MCP-backed scan and dry-run plus an approved write path are actually available through detected tools.
- Use `filesystem-only` only when local scan, dry-run, and an approved write path are available without MCP.
- Use `mcp-readonly` when scan and dry-run are available but there is no approved write path, including local read-only operation without MCP.
- Use `chat-only` when no scan path can reach the target vault.

The historical name `mcp-readonly` is retained for compatibility; it is the transport-neutral effective read-only level, including a local read-only host without MCP. Capability level records scan and write transport. Report validation independently with `validation_available`; when validation is absent, keep `full-local` or `filesystem-only`, set `validation_available=false`, and let [preflight](../preflight.md) report `validation_capability_unavailable`.

## Execution Path

Map OpenCode's exposed shell, file, and MCP tools to the canonical stages. Run identity-aware local scan and dry-run helpers, then use `write_executor.py prepare`, exact plan-ID confirmation, and `write_executor.py apply` for a write. The optional Cobsidian local MCP entry is read-only and may provide scan and planning while OpenCode's shell runs the deterministic executor.

## Degradation

Without an approved write path, return the zero-write dry-run and change plan as `mcp-readonly`. If write exists but validation is unavailable, retain the write-capable level and report the independent block. Without scan access, use `chat-only` and provide a portable draft or ask for a usable vault or configuration path.

## Safety

Use [preflight](../preflight.md) as the readiness authority. OpenCode permission patterns can further restrict shell, edit, skill, or MCP calls, so trust returned tool evidence only. Never bypass plan confirmation with a direct vault edit when the executor is runnable.
