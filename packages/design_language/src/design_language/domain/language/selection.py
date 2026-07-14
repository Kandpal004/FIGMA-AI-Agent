"""The Language Selection — which language was chosen, and why the others were not.

A :class:`LanguageSelection` records the chosen :class:`LanguageArchetype`, the rationale for
it, how it maximises the business goals, the influences it draws on, and — crucially — the
considered-and-rejected alternatives. Requiring at least one recorded alternative makes the
selection a deliberate, defensible decision (the mark of a real design director) rather than a
default, and directly answers the spec's "WHY this / WHY not that / WHY it maximises business
goals".

Pure domain: standard library, the shared-kernel error base, DL ids, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_language.domain.shared.ids import DLEvidenceId
from design_language.domain.shared.value_objects import (
    ConsideredAlternative,
    LanguageArchetype,
    Tag,
)

__all__ = ["InvalidSelectionError", "LanguageSelection"]


class InvalidSelectionError(DesignDirectorError):
    """Raised when a language selection is constructed with invalid data."""

    code = "invalid_design_language_selection"
    http_status = 422


@dataclass(frozen=True, slots=True)
class LanguageSelection:
    """The chosen language archetype and the reasoning behind it.

    Attributes:
        archetype: The selected language archetype (or a synthesised blend).
        rationale: Why this language was selected.
        business_alignment: How the language maximises the business goals.
        influences: The archetypes/traits it draws on (for a blend).
        considered: The alternatives weighed and rejected (at least one).
        evidence_ids: The evidence grounding the selection.
    """

    archetype: LanguageArchetype
    rationale: str
    business_alignment: str
    influences: tuple[Tag, ...] = ()
    considered: tuple[ConsideredAlternative, ...] = ()
    evidence_ids: tuple[DLEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.rationale or not self.rationale.strip():
            raise InvalidSelectionError("LanguageSelection.rationale must be non-empty.")
        if not self.business_alignment or not self.business_alignment.strip():
            raise InvalidSelectionError(
                "LanguageSelection.business_alignment must be non-empty."
            )
        if not self.considered:
            raise InvalidSelectionError(
                "LanguageSelection must record at least one considered-and-rejected "
                "alternative (a deliberate choice, never a default)."
            )
        object.__setattr__(self, "influences", tuple(dict.fromkeys(self.influences)))
        object.__setattr__(self, "considered", tuple(self.considered))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return self.evidence_ids
