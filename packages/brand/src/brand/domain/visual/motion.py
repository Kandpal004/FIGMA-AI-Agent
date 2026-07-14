"""Motion principles — strategic intent for motion (never keyframes or durations).

:class:`MotionPrinciples` states the character and purpose of motion, and the restraint
that governs it — it specifies no durations, easings, or keyframes (that is a later
phase). Cited.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId
from brand.domain.shared.value_objects import MotionCharacter

__all__ = ["InvalidMotionError", "MotionPrinciples"]


class InvalidMotionError(DesignDirectorError):
    """Raised when motion principles are constructed with invalid data."""

    code = "invalid_motion_principles"
    http_status = 422


@dataclass(frozen=True, slots=True)
class MotionPrinciples:
    """The cited strategic intent for motion.

    Attributes:
        character: The character of motion.
        purpose: What motion is for in this brand (e.g. "confirm and guide, never decorate").
        restraint: The restraint that governs motion.
        principles: Motion principles to honour.
        evidence_ids: The evidence supporting it.
    """

    character: MotionCharacter
    purpose: str = ""
    restraint: str = ""
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
