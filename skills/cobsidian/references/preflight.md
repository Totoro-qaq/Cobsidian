# Preflight Contract

Preflight records completed evidence and the active host's capability level before any write can be approved. It is deterministic and fail-closed: every unmet requirement adds a blocked reason.

## Readiness

`ready: true` means all required checks passed and the active host has a write path for an approved write. It does not mean that a write already happened. Dry-run still reports `writes: []`, and the agent must receive or consume approval before changing vault files.

`full-local` and `filesystem-only` can become ready only when scan, dry-run, approved write, and validation paths form a complete loop and every check passes. `mcp-readonly` is the transport-neutral effective read-only level for any host that can scan and dry-run but lacks that approved write and validation loop. Its historical name is retained for compatibility and also covers local read-only hosts without MCP. `mcp-readonly` and `chat-only` cannot become write-ready because they have no approved write capability; `chat-only` additionally has no scan path.

## Blocked Reasons

- `vault_unresolved`: no valid target vault was resolved.
- `scan_capability_unavailable`: the active host cannot scan the vault.
- `existing_notes_not_scanned`: no completed existing-note scan supports the decision.
- `duplicate_check_incomplete`: duplicate or near-duplicate evaluation did not complete.
- `backlink_check_incomplete`: backlink targets were not checked against existing notes.
- `mode_unresolved`: no canonical mode was selected or clearly inferred.
- `write_capability_unavailable`: the active host has no approved vault write path.

Blocked reasons are additive and ordered by the shared preflight implementation. Capability and evidence are separate: possessing a scan tool does not prove that a scan completed.

## Reporting

Never claim an unavailable scan, write, validation, create, append, or split action. Report completed checks from tool evidence, list every blocked reason, and describe the exact degradation path. When `ready` is false, return a dry-run, approved change plan, portable draft, or one concise request for the missing path or capability.
