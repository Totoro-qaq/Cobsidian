# Hermes Adapter

## Detect Capabilities

Inspect the actual available tools before choosing a capability level. Query the active tool registry for vault reads, filesystem search, shell execution, edits, Cobsidian MCP operations, and validation. Do not assume an installed connector is active or authorized.

## Capability Mapping

- Use `full-local` only when MCP-backed scan and dry-run plus an approved write path are actually available through detected tools.
- Use `filesystem-only` only when local scan, dry-run, and an approved write path are available without MCP.
- Use `mcp-readonly` when scan and dry-run are available but there is no approved write path, including local read-only operation without MCP.
- Use `chat-only` when no scan path can reach the target vault.

The historical name `mcp-readonly` is retained for compatibility; it is the transport-neutral effective read-only level, including a local read-only host without MCP.

Capability level records the effective scan/write transport. Report validation capability independently through `validation_available`. If write exists but validation does not, keep `full-local` or `filesystem-only` and set `validation_available=false`; preflight blocks readiness with `validation_capability_unavailable`.

Send the observed level to [preflight](../preflight.md); the product name is not capability evidence.

## Execution Path

Map exposed Hermes filesystem, shell, edit, and MCP invocations to the canonical workflow after detection. Run local helper scripts when a shell path is available, use MCP only for advertised read operations, and invoke edits only after explicit approval.

## Degradation

If scan and dry-run work but no approved write path exists, return the approved change plan as `mcp-readonly`, including for local-only reads without MCP. If write exists but validation is unavailable, retain the write-capable level and report the independent validation block. If no vault scan exists, use `chat-only`, provide a portable draft, or request a usable path without fabricating a scan.

## Safety

Use [preflight](../preflight.md) to block unsupported stages. Treat connector presence, authentication, and permissions as separate checks, and report only actions confirmed by returned tool results.
