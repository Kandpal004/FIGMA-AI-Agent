"""The Visual Tokens — the systematised, abstract token ramps of the language.

A :class:`VisualTokens` bundles the language's token scales (spacing, type, radius, elevation,
motion, contrast) and its colour philosophy into one system. It is the abstract structure the
downstream Design System materialises into concrete tokens, palettes, and — eventually — Figma
variables. It holds no rendered value; it holds the *shape* the values must take.

Pure domain: standard library, the shared-kernel error base, DL ids, and the token scales.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from design_language.domain.shared.ids import DLEvidenceId
from design_language.domain.tokens.color import ColorPhilosophy
from design_language.domain.tokens.scales import (
    ContrastTargets,
    ElevationScale,
    MotionTokens,
    RadiusScale,
    SpacingScale,
    TypeScale,
)
from design_language.domain.shared.value_objects import ColorStrategy

__all__ = ["VisualTokens"]


@dataclass(frozen=True, slots=True)
class VisualTokens:
    """The abstract token system of the design language.

    Attributes:
        spacing: The spacing ramp.
        type_scale: The type ramp.
        radius: The corner-radius ramp.
        elevation: The elevation ramp.
        motion: The motion timing tiers.
        color: The colour philosophy.
        contrast: The contrast targets.
        evidence_ids: The evidence grounding the token system.
    """

    spacing: SpacingScale = field(default_factory=SpacingScale)
    type_scale: TypeScale = field(default_factory=TypeScale)
    radius: RadiusScale = field(default_factory=RadiusScale)
    elevation: ElevationScale = field(default_factory=ElevationScale)
    motion: MotionTokens = field(default_factory=MotionTokens)
    color: ColorPhilosophy = field(
        default_factory=lambda: ColorPhilosophy(strategy=ColorStrategy.NEUTRAL_ACCENT)
    )
    contrast: ContrastTargets = field(default_factory=ContrastTargets)
    evidence_ids: tuple[DLEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return tuple(self.evidence_ids) + self.color.all_evidence_ids()
