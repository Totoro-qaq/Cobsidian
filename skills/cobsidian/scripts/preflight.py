from __future__ import annotations

from dataclasses import dataclass


CAPABILITY_FLAGS = {
    "full-local": {"scan": True, "write": True},
    "filesystem-only": {"scan": True, "write": True},
    "mcp-readonly": {"scan": True, "write": False},
    "chat-only": {"scan": False, "write": False},
}
CAPABILITY_LEVELS = tuple(CAPABILITY_FLAGS)


@dataclass(frozen=True)
class Preflight:
    vault_resolved: bool
    existing_notes_scanned: bool
    duplicate_check_completed: bool
    backlink_check_completed: bool
    mode_selected: bool
    capability_level: str
    write_policy: str
    ready: bool
    blocked_reasons: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "vault_resolved": self.vault_resolved,
            "existing_notes_scanned": self.existing_notes_scanned,
            "duplicate_check_completed": self.duplicate_check_completed,
            "backlink_check_completed": self.backlink_check_completed,
            "mode_selected": self.mode_selected,
            "capability_level": self.capability_level,
            "write_policy": self.write_policy,
            "ready": self.ready,
            "blocked_reasons": list(self.blocked_reasons),
        }


def build_preflight(
    capability_level: str,
    vault_resolved: bool = True,
    existing_notes_scanned: bool = True,
    duplicate_check_completed: bool = True,
    backlink_check_completed: bool = True,
    mode_selected: bool = True,
    write_policy: str = "dry-run",
) -> Preflight:
    if capability_level not in CAPABILITY_FLAGS:
        allowed = ", ".join(CAPABILITY_LEVELS)
        raise ValueError(f"capability_level must be one of: {allowed}.")

    capabilities = CAPABILITY_FLAGS[capability_level]
    blocked_reasons: list[str] = []
    if not vault_resolved:
        blocked_reasons.append("vault_unresolved")
    if not capabilities["scan"]:
        blocked_reasons.append("scan_capability_unavailable")
    if not existing_notes_scanned:
        blocked_reasons.append("existing_notes_not_scanned")
    if not duplicate_check_completed:
        blocked_reasons.append("duplicate_check_incomplete")
    if not backlink_check_completed:
        blocked_reasons.append("backlink_check_incomplete")
    if not mode_selected:
        blocked_reasons.append("mode_unresolved")
    if not capabilities["write"]:
        blocked_reasons.append("write_capability_unavailable")

    reasons = tuple(blocked_reasons)
    return Preflight(
        vault_resolved=vault_resolved,
        existing_notes_scanned=existing_notes_scanned,
        duplicate_check_completed=duplicate_check_completed,
        backlink_check_completed=backlink_check_completed,
        mode_selected=mode_selected,
        capability_level=capability_level,
        write_policy=write_policy,
        ready=not reasons,
        blocked_reasons=reasons,
    )
