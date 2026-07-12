# Kimi Code Adapter

## Detect Capabilities

Inspect the actual available tools before choosing a capability level. Check Kimi Code read, search, shell, file-edit, Cobsidian MCP, and validation access separately; the installed skill or product name alone does not prove that the vault is reachable or writable.

## Capability Mapping

- Use `full-local` only when MCP-backed scan and dry-run plus an approved write path are actually available through detected tools.
- Use `filesystem-only` only when local scan, dry-run, and an approved write path are available without MCP.
- Use `mcp-readonly` when scan and dry-run are available but there is no approved write path, including local read-only operation without MCP.
- Use `chat-only` when no scan path can reach the target vault.

The historical name `mcp-readonly` is retained for compatibility; it is the transport-neutral effective read-only level, including a local read-only host without MCP. Capability level records scan and write transport. Report validation independently with `validation_available`; when validation is absent, keep `full-local` or `filesystem-only`, set `validation_available=false`, and let [preflight](../preflight.md) report `validation_capability_unavailable`.

## Execution Path

Use Kimi Code's discovered skill plus its read and shell tools to run the local identity-aware scan, dry-run, and validation helpers. For writes, call `write_executor.py prepare`, display the diff and plan ID, require the exact ID from the user, then call `write_executor.py apply`. A connected Cobsidian MCP server supplies read-only inspection and planning; it does not replace the local executor.

## Degradation

If no approved write path exists, keep `mcp-readonly` and return the concrete change plan, even when local reads work without MCP. If write exists but validation is unavailable, retain the write-capable level and report the independent validation block. If the vault cannot be scanned, select `chat-only` and return a portable draft or request one usable vault or config path.

## Safety

Apply [preflight](../preflight.md) exactly. Treat Kimi Code tool approval, Cobsidian plan confirmation, and successful validation as separate gates. Never claim an edit from a preview or infer permissions from automatic skill discovery.
