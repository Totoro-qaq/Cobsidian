# Cursor Adapter

## Detect Capabilities

Inspect the actual available tools before choosing a capability level. Confirm whether workspace search reaches the vault, whether a terminal can run local scripts, whether edits are permitted, whether Cobsidian MCP is connected, and whether validation can execute.

## Capability Mapping

- Use `full-local` only when MCP reads and approved workspace or filesystem writes are both actually available.
- Use `filesystem-only` when workspace reads, terminal scripts, edits, and validation work without MCP.
- Use `mcp-readonly` when Cobsidian MCP can scan or dry-run but no approved write path exists.
- Use `chat-only` when the vault is outside every accessible workspace and no scan tool can reach it.

Persist the detected result in [preflight](../preflight.md), independent of the product name.

## Execution Path

Map exposed Cursor workspace search, terminal, edit, and MCP calls to the canonical stages. Use local helper scripts for filesystem workflows; use advertised Cobsidian MCP calls for read-only retrieval. Apply an approved edit only through a confirmed writable workspace path.

## Degradation

When the workspace is readable but not writable, report `mcp-readonly` if MCP supplies the scan path; otherwise do not claim write readiness. When the vault is inaccessible, use `chat-only` and return a portable draft or request one usable path.

## Safety

Follow [preflight](../preflight.md), keep dry-run first, and distinguish workspace visibility from write permission. Report only observed duplicate, backlink, write, and validation results from tools that actually ran.
