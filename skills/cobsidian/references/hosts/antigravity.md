# Antigravity Adapter

## Detect Capabilities

Inspect the actual available tools before choosing a capability level. Check Antigravity workspace read, search, terminal, edit, plugin-provided MCP, and validation access independently. Discovery of a workspace skill or plugin does not prove that the target vault is in scope.

## Capability Mapping

- Use `full-local` only when MCP-backed scan and dry-run plus an approved write path are actually available through detected tools.
- Use `filesystem-only` only when local scan, dry-run, and an approved write path are available without MCP.
- Use `mcp-readonly` when scan and dry-run are available but there is no approved write path, including local read-only operation without MCP.
- Use `chat-only` when no scan path can reach the target vault.

The historical name `mcp-readonly` is retained for compatibility; it is the transport-neutral effective read-only level, including a local read-only host without MCP. Capability level records scan and write transport. Report validation independently with `validation_available`; when validation is absent, keep `full-local` or `filesystem-only`, set `validation_available=false`, and let [preflight](../preflight.md) report `validation_capability_unavailable`.

## Execution Path

Load Cobsidian from the discovered workspace or global skill path, then map Antigravity's visible terminal and file tools to the identity-aware local workflow. Use `write_executor.py prepare`, exact plan-ID confirmation, and `write_executor.py apply`; use plugin-provided Cobsidian MCP only for read-only scan and planning calls.

## Degradation

If no approved write path exists, keep `mcp-readonly` and return the proposed patch without claiming a write. If write exists but validation is unavailable, retain the write-capable level and report the independent validation block. If workspace permissions cannot reach the vault, use `chat-only` and request one usable vault or config path.

## Safety

Apply [preflight](../preflight.md) exactly. Keep workspace and global plugin trust decisions separate from Cobsidian's explicit plan confirmation. Never infer a completed scan or write merely because the skill or plugin is installed.
