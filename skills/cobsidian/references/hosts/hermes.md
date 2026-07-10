# Hermes Adapter

## Detect Capabilities

Inspect the actual available tools before choosing a capability level. Query the active tool registry for vault reads, filesystem search, shell execution, edits, Cobsidian MCP operations, and validation. Do not assume an installed connector is active or authorized.

## Capability Mapping

- Use `full-local` only when MCP reads and approved filesystem writes are both actually available.
- Use `filesystem-only` when local read, shell, edit, and validation operations are available without MCP.
- Use `mcp-readonly` when the Cobsidian MCP surface can scan or dry-run but cannot write.
- Use `chat-only` when no active tool can read and scan the requested vault.

Send the observed level to [preflight](../preflight.md); the product name is not capability evidence.

## Execution Path

Map exposed Hermes filesystem, shell, edit, and MCP invocations to the canonical workflow after detection. Run local helper scripts when a shell path is available, use MCP only for advertised read operations, and invoke edits only after explicit approval.

## Degradation

If the registry exposes only MCP reads, return the dry-run and approved change plan as `mcp-readonly`. If no vault read exists, use `chat-only`, provide a portable draft, or request a usable path without fabricating a scan.

## Safety

Use [preflight](../preflight.md) to block unsupported stages. Treat connector presence, authentication, and permissions as separate checks, and report only actions confirmed by returned tool results.
