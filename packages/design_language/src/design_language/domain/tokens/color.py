"""The Colour Philosophy — the language's colour posture, without a single hex.

A :class:`ColorPhilosophy` fixes *how* the language uses colour — its strategy, the abstract
roles it defines, how many accent hues it permits, and its contrast commitment — but never
*which* colours. Restraint here (one accent, neutral-dominant) is one of the strongest guards
against a garish, AI-generated look; the concrete palette is the downstream Design System's
job.

Pure domain: standard library, the shared-kernel error base, DL ids, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_language.domain.shared.ids import DLEvidenceId
from design_language.domain.shared.value_objects import ColorRole, ColorStrategy
from design_language.domain.tokens.scales import ContrastTargets

__all__ = ["ColorPhilosophy", "InvalidColorError"]


class InvalidColorError(DesignDirectorError):
    """Raised when a colour philosophy is constructed with invalid data."""

    code = "invalid_design_language_color"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ColorPhilosophy:
    """How the language uses colour (a posture, never concrete colours).

    Attributes:
        strategy: The colour strategy.
        roles: The abstract colour roles the language defines.
        accent_count: How many accent hues the language permits (restraint = few).
        contrast: The contrast targets the palette must meet.
        evidence_ids: The evidence grounding the colour posture.
    """

    strategy: ColorStrategy
    roles: tuple[ColorRole, ...] = ()
    accent_count: int = 1
    contrast: ContrastTargets = ContrastTargets()
    evidence_ids: tuple[DLEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.accent_count, int) or self.accent_count < 0:
            raise InvalidColorError(
                "ColorPhilosophy.accent_count must be a non-negative int.",
                details={"value": self.accent_count},
            )
        object.__setattr__(self, "roles", tuple(dict.fromkeys(self.roles)))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return self.evidence_ids
