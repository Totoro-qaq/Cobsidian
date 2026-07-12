# Codex Adapter

## Detect Capabilities

Inspect the actual available tools before choosing a capability level. Check separately for vault reads, local shell execution, filesystem edits, Cobsidian MCP resources or tools, and a runnable validation path. Do not infer any capability from the product name.

## Capability Mapping

- Use `full-local` only when MCP-backed scan and dry-run plus an approved write path are actually available through detected tools.
- Use `filesystem-only` only when local scan, dry-run, and an approved write path are available without MCP.
- Use `mcp-readonly` when scan and dry-run are available but there is no approved write path, including local read-only operation without MCP.
- Use `chat-only` when no scan path can reach the target vault.

The historical name `mcp-readonly` is retained for compatibility; it is the transport-neutral effective read-only level, including a local read-only host without MCP.

Capability level records the effective scan/write transport. Report validation capability independently through `validation_available`. If write exists but validation does not, keep `full-local` or `filesystem-only` and set `validation_available=false`; preflight blocks readiness with `validation_capability_unavailable`.

Record the selected level through [preflight](../preflight.md); never promote the level because a tool is expected but absent.

## Execution Path

Map exposed Codex CLI shell and file calls to the local helper scripts only after capability detection. Prefer Cobsidian MCP resources and dry-run calls for read-only retrieval when they are advertised. For a local write, run scan, identity-aware duplicate and backlink checks, dry-run, `write_executor.py prepare`, exact plan-ID confirmation, `write_executor.py apply`, and validation in that order. Do not replace the executor with an untracked direct edit when Python execution is available.

## Degradation

Without an approved write path, return the dry-run and an approved change plan under `mcp-readonly`, whether reads come from MCP or local tools. When write exists but validation is unavailable, retain the write-capable level and report the independent validation block. Without scan access, use `chat-only` and return a portable draft or request one usable vault or config path. Do not invent results for skipped stages.

## Safety

Use [preflight](../preflight.md) as the readiness authority. Keep dry-run as the default, require approval before local edits, resolve links only from confirmed notes, and report the exact actions the detected tools completed.
