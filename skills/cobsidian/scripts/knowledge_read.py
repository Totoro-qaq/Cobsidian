from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


MODES = (
    "learning",
    "project",
    "review",
    "comparison",
    "index",
    "capture",
    "dissection",
)
DEPTHS = ("capture", "standard", "deep")
GRANULARITIES = ("append", "single-note", "multi-note")
EVIDENCE_LEVELS = ("conversation", "source-grounded", "verified")
DISPLAY_POLICIES = ("auto", "always", "off")
MODE_DEFAULTS = {
    "learning": ("standard", "single-note"),
    "project": ("deep", "single-note"),
    "review": ("deep", "single-note"),
    "comparison": ("standard", "single-note"),
    "index": ("deep", "multi-note"),
    "capture": ("capture", "single-note"),
    "dissection": ("deep", "multi-note"),
}


@dataclass(frozen=True)
class KnowledgeRead:
    mode: str | None
    mode_explicit: bool
    recommended_modes: tuple[str, ...]
    depth: str
    granularity: str
    evidence: str
    display_policy: str
    display_style: str

    def to_payload(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "mode_explicit": self.mode_explicit,
            "recommended_modes": list(self.recommended_modes),
            "depth": self.depth,
            "granularity": self.granularity,
            "evidence": self.evidence,
            "display_policy": self.display_policy,
            "display_style": self.display_style,
        }


def validated_choice(
    name: str,
    value: str,
    allowed: tuple[str, ...],
) -> str:
    if value not in allowed:
        raise ValueError(f"{name} must be one of: {', '.join(allowed)}.")
    return value


def validated_recommendations(
    mode: str | None,
    recommended_modes: Iterable[str] | None,
) -> tuple[str, ...]:
    recommendations = tuple(recommended_modes or ())
    if len(recommendations) > 2:
        raise ValueError("recommended_modes accepts at most two modes.")
    if mode is not None and recommendations:
        raise ValueError("recommended_modes requires an unresolved mode.")
    for recommendation in recommendations:
        validated_choice("recommended mode", recommendation, MODES)
    return recommendations


def resolve_display_style(
    policy: str,
    mode_explicit: bool,
    depth: str,
    granularity: str,
    evidence: str,
) -> str:
    if policy == "always":
        return "expanded"
    if policy == "off":
        return "hidden"
    if (
        not mode_explicit
        or depth == "deep"
        or granularity == "multi-note"
        or evidence in {"source-grounded", "verified"}
    ):
        return "expanded"
    return "compact"


def build_knowledge_read(
    mode: str | None,
    mode_explicit: bool,
    recommended_modes: Iterable[str] | None = None,
    depth: str | None = None,
    granularity: str | None = None,
    evidence: str = "conversation",
    display_policy: str = "auto",
    decision_action: str | None = None,
) -> KnowledgeRead:
    if mode is not None:
        validated_choice("mode", mode, MODES)
    recommendations = validated_recommendations(mode, recommended_modes)
    default_depth, default_granularity = MODE_DEFAULTS.get(
        mode,
        ("standard", "single-note"),
    )
    resolved_depth = validated_choice(
        "depth",
        default_depth if depth is None else depth,
        DEPTHS,
    )
    requested_granularity = (
        default_granularity if granularity is None else granularity
    )
    resolved_granularity = validated_choice(
        "granularity",
        "append" if decision_action == "append" else requested_granularity,
        GRANULARITIES,
    )
    resolved_evidence = validated_choice("evidence", evidence, EVIDENCE_LEVELS)
    resolved_policy = validated_choice(
        "display_policy",
        display_policy,
        DISPLAY_POLICIES,
    )
    return KnowledgeRead(
        mode=mode,
        mode_explicit=mode_explicit,
        recommended_modes=recommendations,
        depth=resolved_depth,
        granularity=resolved_granularity,
        evidence=resolved_evidence,
        display_policy=resolved_policy,
        display_style=resolve_display_style(
            resolved_policy,
            mode_explicit,
            resolved_depth,
            resolved_granularity,
            resolved_evidence,
        ),
    )
