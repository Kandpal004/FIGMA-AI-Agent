"""The mental model — how users already expect the experience to work.

A :class:`MentalModel` captures the conventions and expectations the target user brings
from other sites (the anchor for Jakob's Law: users spend most of their time on *other*
sites, so meet the conventions they already know). Cited, and the foundation the
navigation and interaction strategies must respect.

Pure domain: standard library, the shared-kernel error base, UX ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from ux.domain.shared.ids import UXEvidenceId

__all__ = ["InvalidMentalModelError", "MentalModel"]


class InvalidMentalModelError(DesignDirectorError):
    """Raised when a mental model is constructed with invalid data."""

    code = "invalid_mental_model"
    http_status = 422


@dataclass(frozen=True, slots=True)
class MentalModel:
    """The cited model of how users expect the experience to work.

    Attributes:
        summary: A one-line statement of the user's mental model.
        expectations: The conventions/expectations users bring.
        familiar_patterns: The patterns users already know and expect to reuse.
        anti_patterns: Expectation violations to avoid (surprises that break trust).
        evidence_ids: The evidence supporting it.
    """

    summary: str
    expectations: tuple[str, ...] = ()
    familiar_patterns: tuple[str, ...] = ()
    anti_patterns: tuple[str, ...] = ()
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.summary or not self.summary.strip():
            raise InvalidMentalModelError("MentalModel.summary must be non-empty.")
        object.__setattr__(self, "expectations", tuple(self.expectations))
        object.__setattr__(self, "familiar_patterns", tuple(self.familiar_patterns))
        object.__setattr__(self, "anti_patterns", tuple(self.anti_patterns))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
