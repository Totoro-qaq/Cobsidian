# Generic MCP Adapter

## Detect Capabilities

Inspect the actual available tools and resources advertised by the connected servers before choosing a capability level. Confirm vault resolution, scan or dry-run operations, any separate filesystem write path, and validation support. Generic MCP access defaults to read-only, not write-capable.

## Capability Mapping

- Use `full-local` only when MCP reads plus a separately approved filesystem write and validation path are both actually available.
- Use `filesystem-only` when local read, shell, edit, and validation tools exist but Cobsidian MCP is unavailable.
- Use `mcp-readonly` by default when Cobsidian MCP can scan, retrieve, or dry-run without a write path.
- Use `chat-only` when no advertised resource or tool can reach the target vault.

Record this evidence in [preflight](../preflight.md) instead of inferring capabilities from an MCP server label.

## Execution Path

Map generic MCP resource reads and tool calls only to operations present in the advertised schema. Use Cobsidian scan, retrieval, and dry-run calls as read-only operations. A separate approved filesystem editor may perform writes only after the dry-run and capability checks complete.

## Degradation

Under `mcp-readonly`, return scan evidence, dry-run output, and an approved change plan without claiming a write. Under `chat-only`, return a portable draft or ask for one usable host or path; do not manufacture create, append, or validation results.

## Safety

Follow [preflight](../preflight.md) and preserve the MCP write boundary. Never treat a tool description as proof that a call succeeded, and never claim actions absent from the actual response.
