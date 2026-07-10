from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True)
class Capability:
    scan: bool
    write: bool
    validation: bool


CAPABILITY_FLAGS: Mapping[str, Capability] = MappingProxyType(
    {
        "full-local": Capability(scan=True, write=True, validation=True),
        "filesystem-only": Capability(scan=True, write=True, validation=True),
        "mcp-readonly": Capability(scan=True, write=False, validation=True),
        "chat-only": Capability(scan=False, write=False, validation=False),
    }
)
CAPABILITY_LEVELS = tuple(CAPABILITY_FLAGS)
_BOOLEAN_FIELDS = (
    "vault_resolved",
    "existing_notes_scanned",
    "duplicate_check_completed",
    "backlink_check_completed",
    "mode_selected",
    "validation_available",
)


def validated_capability(capability_level: str) -> Capability:
    if not isinstance(capability_level, str) or capability_level not in CAPABILITY_FLAGS:
        allowed = ", ".join(CAPABILITY_LEVELS)
        raise ValueError(f"capability_level must be one of: {allowed}.")
    return CAPABILITY_FLAGS[capability_level]


def validate_write_policy(write_policy: str) -> None:
    if write_policy != "dry-run":
        raise ValueError("write_policy must be: dry-run.")


@dataclass(frozen=True)
class Preflight:
    vault_resolved: bool
    existing_notes_scanned: bool
    duplicate_check_completed: bool
    backlink_check_completed: bool
    mode_selected: bool
    validation_available: bool
    capability_level: str
    write_policy: str
    ready: bool = field(init=False)
    blocked_reasons: tuple[str, ...] = field(init=False)

    def __post_init__(self) -> None:
        capability = validated_capability(self.capability_level)
        validate_write_policy(self.write_policy)
        self._validate_boolean_types()
        self._validate_evidence_dependencies(capability)
        blocked_reasons = self._derive_blocked_reasons(capability)
        object.__setattr__(self, "blocked_reasons", blocked_reasons)
        object.__setattr__(self, "ready", not blocked_reasons)

    def _validate_boolean_types(self) -> None:
        for field_name in _BOOLEAN_FIELDS:
            if not isinstance(getattr(self, field_name), bool):
                raise ValueError(f"{field_name} must be a bool.")

    def _validate_evidence_dependencies(self, capability: Capability) -> None:
        scan_dependent_checks = (
            self.existing_notes_scanned,
            self.duplicate_check_completed,
            self.backlink_check_completed,
        )
        if not capability.scan and any(scan_dependent_checks):
            raise ValueError(
                f"capability_level {self.capability_level!r} has no scan capability "
                "and cannot claim scan-dependent checks."
            )
        if self.validation_available and not capability.scan:
            raise ValueError(
                f"capability_level {self.capability_level!r} has no scan capability "
                "and cannot claim vault validation capability."
            )
        if self.existing_notes_scanned and not self.vault_resolved:
            raise ValueError(
                "existing_notes_scanned=True requires vault_resolved=True."
            )
        if not self.existing_notes_scanned and (
            self.duplicate_check_completed or self.backlink_check_completed
        ):
            raise ValueError(
                "duplicate_check_completed and backlink_check_completed require "
                "existing_notes_scanned=True."
            )

    def _derive_blocked_reasons(
        self,
        capability: Capability,
    ) -> tuple[str, ...]:
        blocked_reasons: list[str] = []
        if not self.vault_resolved:
            blocked_reasons.append("vault_unresolved")
        if not capability.scan:
            blocked_reasons.append("scan_capability_unavailable")
        if not self.existing_notes_scanned:
            blocked_reasons.append("existing_notes_not_scanned")
        if not self.duplicate_check_completed:
            blocked_reasons.append("duplicate_check_incomplete")
        if not self.backlink_check_completed:
            blocked_reasons.append("backlink_check_incomplete")
        if not self.mode_selected:
            blocked_reasons.append("mode_unresolved")
        if not capability.write:
            blocked_reasons.append("write_capability_unavailable")
        if not self.validation_available:
            blocked_reasons.append("validation_capability_unavailable")
        return tuple(blocked_reasons)

    def to_payload(self) -> dict[str, object]:
        return {
            "vault_resolved": self.vault_resolved,
            "existing_notes_scanned": self.existing_notes_scanned,
            "duplicate_check_completed": self.duplicate_check_completed,
            "backlink_check_completed": self.backlink_check_completed,
            "mode_selected": self.mode_selected,
            "validation_available": self.validation_available,
            "capability_level": self.capability_level,
            "write_policy": self.write_policy,
            "ready": self.ready,
            "blocked_reasons": list(self.blocked_reasons),
        }


def build_preflight(
    capability_level: str,
    vault_resolved: bool = False,
    existing_notes_scanned: bool = False,
    duplicate_check_completed: bool = False,
    backlink_check_completed: bool = False,
    mode_selected: bool = False,
    validation_available: bool | None = None,
    write_policy: str = "dry-run",
) -> Preflight:
    capability = validated_capability(capability_level)
    resolved_validation_available = (
        capability.validation
        if validation_available is None
        else validation_available
    )
    return Preflight(
        vault_resolved=vault_resolved,
        existing_notes_scanned=existing_notes_scanned,
        duplicate_check_completed=duplicate_check_completed,
        backlink_check_completed=backlink_check_completed,
        mode_selected=mode_selected,
        validation_available=resolved_validation_available,
        capability_level=capability_level,
        write_policy=write_policy,
    )
