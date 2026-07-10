# Cursor Adapter

## Detect Capabilities

Inspect the actual available tools before choosing a capability level. Confirm whether workspace search reaches the vault, whether a terminal can run local scripts, whether edits are permitted, whether Cobsidian MCP is connected, and whether validation can execute.

## Capability Mapping

- Use `full-local` only when MCP-backed scan and dry-run plus approved write and validation paths are all actually available through detected tools.
- Use `filesystem-only` only when local scan, dry-run, approved write, and validation paths are all available without MCP.
- Use `mcp-readonly` when scan and dry-run are available but the host lacks a complete approved write and validation loop, including local read-only operation without MCP.
- Use `chat-only` when no scan path can reach the target vault.

The historical name `mcp-readonly` is retained for compatibility; it is the transport-neutral effective read-only level, including a local read-only host without MCP.

Persist the detected result in [preflight](../preflight.md), independent of the product name.

## Execution Path

Map exposed Cursor workspace search, terminal, edit, and MCP calls to the canonical stages. Use local helper scripts for filesystem workflows; use advertised Cobsidian MCP calls for read-only retrieval. Apply an approved edit only through a confirmed writable workspace path.

## Degradation

When scan and dry-run work but the approved write and validation loop is incomplete, report `mcp-readonly` regardless of transport. When no scan path can reach the vault, use `chat-only` and return a portable draft or request one usable path.

## Safety

Follow [preflight](../preflight.md), keep dry-run first, and distinguish workspace visibility from write permission. Report only observed duplicate, backlink, write, and validation results from tools that actually ran.
