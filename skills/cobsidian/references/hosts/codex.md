# Codex Adapter

## Detect Capabilities

Inspect the actual available tools before choosing a capability level. Check separately for vault reads, local shell execution, filesystem edits, Cobsidian MCP resources or tools, and a runnable validation path. Do not infer any capability from the product name.

## Capability Mapping

- Use `full-local` only when MCP-backed scan and dry-run plus approved write and validation paths are all actually available through detected tools.
- Use `filesystem-only` only when local scan, dry-run, approved write, and validation paths are all available without MCP.
- Use `mcp-readonly` when scan and dry-run are available but the host lacks a complete approved write and validation loop, including local read-only operation without MCP.
- Use `chat-only` when no scan path can reach the target vault.

The historical name `mcp-readonly` is retained for compatibility; it is the transport-neutral effective read-only level, including a local read-only host without MCP.

Record the selected level through [preflight](../preflight.md); never promote the level because a tool is expected but absent.

## Execution Path

Map exposed Codex shell and file-edit calls to the local helper scripts only after capability detection. Prefer Cobsidian MCP resource and dry-run calls for read-only retrieval when they are advertised. For a local path, run scan, duplicate, backlink, dry-run, approved edit, and validation in that order.

## Degradation

Without a complete approved write and validation loop, return the dry-run and an approved change plan under `mcp-readonly`, whether reads come from MCP or local tools. Without scan access, use `chat-only` and return a portable draft or request one usable vault or config path. Do not invent results for skipped stages.

## Safety

Use [preflight](../preflight.md) as the readiness authority. Keep dry-run as the default, require approval before local edits, resolve links only from confirmed notes, and report the exact actions the detected tools completed.
