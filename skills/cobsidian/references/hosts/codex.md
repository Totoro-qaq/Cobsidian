# Codex Adapter

## Detect Capabilities

Inspect the actual available tools before choosing a capability level. Check separately for vault reads, local shell execution, filesystem edits, Cobsidian MCP resources or tools, and a runnable validation path. Do not infer any capability from the product name.

## Capability Mapping

- Use `full-local` only when MCP-backed scan and dry-run plus approved write and validation paths are all actually available through detected tools.
- Use `filesystem-only` when local read, shell, edit, and validation tools exist without usable MCP access.
- Use `mcp-readonly` when Cobsidian MCP can scan or dry-run but no approved filesystem write path exists.
- Use `chat-only` when neither the target vault nor a usable scan path is accessible.

Record the selected level through [preflight](../preflight.md); never promote the level because a tool is expected but absent.

## Execution Path

Map exposed Codex shell and file-edit calls to the local helper scripts only after capability detection. Prefer Cobsidian MCP resource and dry-run calls for read-only retrieval when they are advertised. For a local path, run scan, duplicate, backlink, dry-run, approved edit, and validation in that order.

## Degradation

Without writes, return the dry-run and an approved change plan under `mcp-readonly`. Without scan access, use `chat-only` and return a portable draft or request one usable vault or config path. Do not invent results for skipped stages.

## Safety

Use [preflight](../preflight.md) as the readiness authority. Keep dry-run as the default, require approval before local edits, resolve links only from confirmed notes, and report the exact actions the detected tools completed.
