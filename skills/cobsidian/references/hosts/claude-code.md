# Claude Code Adapter

## Detect Capabilities

Inspect the actual available tools before choosing a capability level. Check for vault reads, search, shell execution, file editing, Cobsidian MCP access, and validation commands as separate facts. Tool names may vary, so do not infer access from the product name.

## Capability Mapping

- Use `full-local` only when MCP-backed scan and dry-run plus approved write and validation paths are all actually available through detected tools.
- Use `filesystem-only` only when local scan, dry-run, approved write, and validation paths are all available without MCP.
- Use `mcp-readonly` when scan and dry-run are available but the host lacks a complete approved write and validation loop, including local read-only operation without MCP.
- Use `chat-only` when no scan path can reach the target vault.

The historical name `mcp-readonly` is retained for compatibility; it is the transport-neutral effective read-only level, including a local read-only host without MCP.

Record the chosen level through [preflight](../preflight.md) after detection, not before it.

## Execution Path

Map currently exposed Claude Code read, search, shell, edit, and MCP calls to the canonical workflow. Local execution runs helper scripts for scan, duplicates, backlinks, dry-run, and validation; an edit call is used only after approval. MCP calls remain read-only.

## Degradation

If the approved write and validation loop is incomplete, keep `mcp-readonly` and return a concrete approved change plan, even when local reads work without MCP. If vault scan access is missing, select `chat-only` and provide a portable draft or ask for a usable vault or configuration path.

## Safety

Apply [preflight](../preflight.md) exactly. Never claim a scan, write, or validation that the active call surface did not perform, and never treat a familiar product label as proof of local access.
