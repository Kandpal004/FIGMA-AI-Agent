"""The Responsive Strategy — how the language behaves across viewports.

A :class:`ResponsiveStrategy` fixes the responsive posture (fluid, adaptive, or hybrid), how
many breakpoint tiers the language defines, whether type and spacing scale fluidly, and the
governing principles — no pixels, only the strategy the downstream system implements.

Pure domain: standard library, the shared-kernel error base, DL ids, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_language.domain.shared.ids import DLEvidenceId
from design_language.domain.shared.value_objects import ResponsiveApproach

__all__ = ["InvalidResponsiveError", "ResponsiveStrategy"]


class InvalidResponsiveError(DesignDirectorError):
    """Raised when a responsive strategy is constructed with invalid data."""

    code = "invalid_design_language_responsive"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ResponsiveStrategy:
    """The responsive posture of the design language.

    Attributes:
        approach: Fluid, adaptive, or hybrid.
        breakpoint_tiers: How many breakpoint tiers the language defines.
        scales_fluidly: Whether type and spacing scale fluidly between breakpoints.
        principles: The governing responsive principles.
        evidence_ids: The evidence grounding the strategy.
    """

    approach: ResponsiveApproach = ResponsiveApproach.FLUID
    breakpoint_tiers: int = 4
    scales_fluidly: bool = True
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[DLEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.breakpoint_tiers, int) or self.breakpoint_tiers <= 0:
            raise InvalidResponsiveError(
                "ResponsiveStrategy.breakpoint_tiers must be a positive int.",
                details={"value": self.breakpoint_tiers},
            )
        object.__setattr__(self, "principles", tuple(p for p in self.principles if p and p.strip()))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return self.evidence_ids
