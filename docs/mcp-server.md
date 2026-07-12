# Cobsidian MCP Server

Cobsidian ships a local MCP server for hosts that support the Model Context Protocol.

Use it as a local `stdio` server. Do not expose it as a public HTTP service for private vaults.

## Install Dependencies

```bash
python -m pip install -r requirements-mcp.txt
```

## Server Entry Point

```bash
python skills/cobsidian/mcp_server.py
```

This command is meant to be launched by an MCP host over `stdio`. Running it directly will wait for MCP messages on standard input.

## Host Config

Use an absolute path for reliability:

```json
{
  "mcpServers": {
    "cobsidian": {
      "command": "python",
      "args": ["/absolute/path/to/Cobsidian/skills/cobsidian/mcp_server.py"],
      "cwd": "/absolute/path/to/Cobsidian",
      "env": {
        "PYTHONUTF8": "1",
        "COBSIDIAN_CONFIG": "/absolute/path/to/cobsidian.config.yml"
      }
    }
  }
}
```

If you do not use a config file, set `COBSIDIAN_VAULT`:

```json
{
  "mcpServers": {
    "cobsidian": {
      "command": "python",
      "args": ["/absolute/path/to/Cobsidian/skills/cobsidian/mcp_server.py"],
      "cwd": "/absolute/path/to/Cobsidian",
      "env": {
        "PYTHONUTF8": "1",
        "COBSIDIAN_VAULT": "/absolute/path/to/obsidian-vault"
      }
    }
  }
}
```

Different MCP hosts place this JSON in different settings files. Keep the same server block and adapt only the host-specific wrapper.

## Tools

The server registers read/planning tools only:

| Tool | Purpose |
|---|---|
| `cobsidian_scan_vault` | Scan Markdown notes with bounded `offset` / `limit` pagination. |
| `cobsidian_find_duplicates` | Report exact and similar note titles with bounded comparisons. |
| `cobsidian_suggest_backlinks` | Suggest related notes for a topic, text, or target note. |
| `cobsidian_validate_notes` | Report missing wiki links, duplicate titles, and empty notes. |
| `cobsidian_dry_run` | Plan create/append behavior without writing files. |

There is intentionally no MCP write tool. A write-capable host may use the separate local deterministic executor after MCP planning; the server itself remains read-only.

## Companion Local Writer

When the host has approved shell access, use this sequence outside MCP:

```bash
python skills/cobsidian/scripts/write_executor.py prepare /path/to/vault \
  --action append --target-note "RAG.md" --content-file draft.md \
  --plan-out /tmp/cobsidian-plan.json

python skills/cobsidian/scripts/write_executor.py apply /path/to/vault \
  --plan /tmp/cobsidian-plan.json --confirm PLAN_ID --json
```

`prepare` writes only the plan file and prints a unified diff plus integrity-derived plan ID. `apply` requires that exact ID, rejects stale target hashes, writes with atomic replacement, validates the vault, and automatically restores the previous note when the change introduces new warnings. Transactions live under the vault's private `.cobsidian/transactions/` directory and can be reverted with the `rollback` subcommand when the target has not changed since apply.

## Adaptive Dry-run Contract

`cobsidian_dry_run` is a zero-write MCP tool. It returns the existing planning payload plus `knowledge_read` and `preflight`; `writes` is always `[]`. The MCP server remains read-only regardless of the supplied `capability_level`. That parameter describes the active host for preflight and never grants the server write access.

The historical capability name `mcp-readonly` is retained for compatibility. It is the transport-neutral effective read-only level for any host that can scan and dry-run but has no approved write path, including local read-only operation without MCP. It does not imply that MCP is the active transport.

Capability level records effective scan/write transport. Validation is modeled independently by strict Boolean `validation_available`, defaulting from the level unless explicitly overridden. Keep `full-local` or `filesystem-only` when write exists but validation does not; set `validation_available=false`, which adds `validation_capability_unavailable` and keeps `ready=false`. With default `mcp-readonly`, validation is available and preflight is blocked only by `write_capability_unavailable`. `chat-only` defaults validation to unavailable.

### CLI/MCP Parameter Parity

CLI/MCP parameter parity comes from the shared dry-run implementation, which validates the same optional context from both entry points:

| MCP parameter | CLI option | Contract |
|---|---|---|
| `mode` | `--mode` | One of `learning`, `project`, `review`, `comparison`, `index`, `capture`, `dissection`; omit when unresolved. |
| `mode_explicit` | `--mode-explicit` / `--no-mode-explicit` | A strict Boolean that records whether the user selected the mode; entry points resolve omitted/`null` inference before the shared builder. |
| `recommended_modes` | repeat `--recommended-mode` | Zero to two canonical modes, only while `mode` is unresolved. |
| `depth` | `--depth` | `capture`, `standard`, or `deep`. |
| `granularity` | `--granularity` | `append`, `single-note`, or `multi-note`; requested `granularity=append` requires an append decision. |
| `evidence` | `--evidence` | `conversation`, `source-grounded`, or `verified`. |
| `source_read_completed` | `--source-read-completed` | Strict Boolean host-completed fact confirming the relevant source read actually finished. |
| `verification_completed` | `--verification-completed` | Strict Boolean host-completed fact confirming the additional verification actually finished. |
| `validation_available` | `--validation-available` / `--no-validation-available` | Optional strict Boolean override; omitted/`null` derives from the capability default. |
| `knowledge_read_policy` | `--knowledge-read` | `auto`, `always`, or `off`. |
| `capability_level` | `--capability-level` | `full-local`, `filesystem-only`, `mcp-readonly`, or `chat-only`. |

MCP defaults `capability_level` to `mcp-readonly`; the local CLI defaults to `filesystem-only`. Equivalent inputs produce the same Knowledge Read fields and preflight rules.

`source-grounded` requires `source_read_completed=true`. `verified` requires both completion facts. These facts are supplied by the host from completed actions; mode choice, source-oriented wording, or a user's claim never upgrades evidence automatically. They are validation inputs and do not add fields to the eight-field `knowledge_read` JSON object.

### Error Boundaries

The server and shared dry-run fail closed:

- Missing or invalid vault/config input is rejected without a planning or write claim.
- A blank topic, invalid enum, more than two recommendations, or recommendations alongside a resolved mode is rejected.
- A requested `granularity=append` is rejected unless duplicate resolution selected `decision.action=append`; an actual append decision always forces append granularity.
- Unproven `source-grounded` or `verified` evidence and non-Boolean completion facts are rejected.
- Under `auto`, an unresolved mode returns expanded Knowledge Read with `ready=false` and `mode_unresolved`; `off` hides only the conversational presentation, and no policy silently selects a mode.
- A host without scan capability gets a `blocked` decision and cannot claim scan-derived checks.
- A read-only host reports `write_capability_unavailable`; it never upgrades itself to a write path.
- Validation unavailable reports `validation_capability_unavailable` after any write-capability reason and blocks readiness independently of the transport level.
- A scanless `chat-only` host cannot override `validation_available` to true.
- Note resources reject absolute paths and `..` traversal outside the resolved vault.

## Large Vault Limits

- `cobsidian_scan_vault` defaults to `offset=0` and `limit=100`; the maximum page size is `500`. Responses include `total_note_count` and page metadata.
- `cobsidian_find_duplicates` always finds all exact normalized-title duplicates. Similar-title work compares unique normalized titles, defaults to at most `100000` comparisons, and returns `comparisons` plus `truncated` metadata.
- Backlink ranking reads title, tags, wiki links, and note body text. Chinese text uses deterministic CJK bigrams and trigrams without an external tokenizer.
- Backlink result limits must be between `1` and `100`; the configured default is `8`.
- Backlink requests require at least one non-empty topic or material source; blank strings and empty source files are rejected.

## Resources

| Resource | Purpose |
|---|---|
| `cobsidian://config` | Read the active config summary from `COBSIDIAN_CONFIG`; `interaction` publishes only normalized `knowledge_read`. |
| `cobsidian://vault-summary` | Read the complete configured-vault summary for backward compatibility. |
| `cobsidian://vault-page/{offset}/{limit}` | Read a bounded page from the configured vault. |
| `cobsidian://note/{note_path}` | Read a note by vault-relative path. |

`cobsidian://note/{note_path}` rejects absolute paths and `..` traversal outside the vault.

Prefer `cobsidian://vault-page/{offset}/{limit}` for large vaults. The static `vault-summary` resource remains complete so existing clients are not silently truncated.

## Prompts

| Prompt | Purpose |
|---|---|
| `cobsidian-dry-run` | Ask the agent to plan a vault write without changing files. |
| `cobsidian-organize-after-confirmation` | Ask the agent to organize material after the user confirms the dry-run plan. |

Prompts provide instructions to the host; they do not add a write tool to this server.

## Verify Locally

```bash
python -m unittest discover tests -p "test_mcp_server.py"
```

To inspect registered tools without starting a host:

```bash
python -c "import asyncio; from skills.cobsidian.mcp_server import create_mcp_server; print(asyncio.run(create_mcp_server().list_tools()))"
```

## Security Notes

- Prefer local `stdio` transport for private vaults.
- Do not expose this server to a public network.
- Do not add arbitrary shell execution tools.
- Keep all vault writes outside this MCP server and behind explicit host approval.
- Use `COBSIDIAN_CONFIG` or `COBSIDIAN_VAULT` to narrow the intended vault.
- Note resource reads are constrained to the resolved vault path.
