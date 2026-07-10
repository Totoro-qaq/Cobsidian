# Claude Code Adapter

## Detect Capabilities

Inspect the actual available tools before choosing a capability level. Check for vault reads, search, shell execution, file editing, Cobsidian MCP access, and validation commands as separate facts. Tool names may vary, so do not infer access from the product name.

## Capability Mapping

- Use `full-local` only when MCP reads and approved filesystem writes are both actually available.
- Use `filesystem-only` when local filesystem, shell, edit, and validation tools exist without usable MCP access.
- Use `mcp-readonly` when Cobsidian MCP supports scan or dry-run but no approved write tool is available.
- Use `chat-only` when the target vault cannot be scanned through any exposed tool.

Record the chosen level through [preflight](../preflight.md) after detection, not before it.

## Execution Path

Map currently exposed Claude Code read, search, shell, edit, and MCP calls to the canonical workflow. Local execution runs helper scripts for scan, duplicates, backlinks, dry-run, and validation; an edit call is used only after approval. MCP calls remain read-only.

## Degradation

If edit access is missing, keep `mcp-readonly` and return a concrete approved change plan. If vault reads are missing, select `chat-only` and provide a portable draft or ask for a usable vault or configuration path.

## Safety

Apply [preflight](../preflight.md) exactly. Never claim a scan, write, or validation that the active call surface did not perform, and never treat a familiar product label as proof of local access.
