# Pi Adapter

## Detect Capabilities

Inspect the actual available tools before choosing a capability level. Check Pi read, search, shell, write or edit, extension-provided tools, and validation access separately. Pi has no built-in MCP client, so do not assume an MCP transport unless an installed extension explicitly exposes one.

## Capability Mapping

- Use `full-local` only when extension-provided MCP-backed scan and dry-run plus an approved write path are actually available through detected tools.
- Use `filesystem-only` only when local scan, dry-run, and an approved write path are available without MCP.
- Use `mcp-readonly` when scan and dry-run are available but there is no approved write path, including local read-only operation without MCP.
- Use `chat-only` when no scan path can reach the target vault.

The historical name `mcp-readonly` is retained for compatibility; it is the transport-neutral effective read-only level, including a local read-only host without MCP. Capability level records scan and write transport. Report validation independently with `validation_available`; when validation is absent, keep `full-local` or `filesystem-only`, set `validation_available=false`, and let [preflight](../preflight.md) report `validation_capability_unavailable`.

## Execution Path

Prefer Pi's built-in local read and shell tools: run the identity-aware scan, duplicate, backlink, dry-run, and validation helpers directly. Use `write_executor.py prepare`, show its diff and plan ID, require the exact ID, then call `write_executor.py apply`. Only use an MCP route when a specific installed Pi extension advertises the required calls.

## Degradation

When no approved write path exists, report `mcp-readonly` and a concrete zero-write plan even if reads are local. If write exists but validation is unavailable, retain the write-capable level and report the independent block. When the vault cannot be scanned, use `chat-only`, return a portable draft, or request a usable path.

## Safety

Follow [preflight](../preflight.md). Do not present MCP as a Pi core feature, do not treat a package or extension as active before its tools are observed, and do not replace the plan-confirm-apply transaction with an untracked direct edit.
