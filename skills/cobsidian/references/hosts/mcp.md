# Generic MCP Adapter

## Detect Capabilities

Inspect the actual available tools and resources advertised by the connected servers before choosing a capability level. Confirm vault resolution, scan or dry-run operations, any separate filesystem write path, and validation support. Generic MCP access defaults to read-only, not write-capable.

## Capability Mapping

- Use `full-local` only when scan, dry-run, approved write, and validation paths are all actually available through advertised MCP and companion filesystem tools.
- Use `filesystem-only` only when local scan, dry-run, approved write, and validation paths are all available without MCP.
- Use `mcp-readonly` when scan and dry-run are available but the host lacks a complete approved write and validation loop, including local read-only operation without MCP.
- Use `chat-only` when no scan path can reach the target vault.

The historical name `mcp-readonly` is retained for compatibility; it is the transport-neutral effective read-only level, including a local read-only host without MCP.

Record this evidence in [preflight](../preflight.md) instead of inferring capabilities from an MCP server label.

## Execution Path

Map generic MCP resource reads and tool calls only to operations present in the advertised schema. Use Cobsidian scan, retrieval, and dry-run calls as read-only operations. A separate approved filesystem editor may perform writes only after the dry-run and capability checks complete.

## Degradation

Under `mcp-readonly`, return scan evidence, dry-run output, and an approved change plan without claiming a write, regardless of whether reads use MCP or local tools. Under `chat-only`, return a portable draft or ask for one usable host or path; do not manufacture create, append, or validation results.

## Safety

Follow [preflight](../preflight.md) and preserve the MCP write boundary. Never treat a tool description as proof that a call succeeded, and never claim actions absent from the actual response.
