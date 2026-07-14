"""The Language Explanation — the engine's articulated WHY.

A :class:`LanguageExplanation` makes the engine's reasoning explicit and auditable: why the
chosen language was selected, why each alternative was rejected, and how the language maximises
the business goals. It directly satisfies the spec's demand that the engine explain WHY this
language, WHY not another, and WHY it serves the business — grounded in evidence, never
asserted.

Pure domain: standard library, the shared-kernel error base, DL ids, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_language.domain.shared.ids import DLEvidenceId

__all__ = ["InvalidExplanationError", "LanguageExplanation"]


class InvalidExplanationError(DesignDirectorError):
    """Raised when an explanation is constructed with invalid data."""

    code = "invalid_design_language_explanation"
    http_status = 422


@dataclass(frozen=True, slots=True)
class LanguageExplanation:
    """The articulated reasoning behind the selected visual language.

    Attributes:
        why_selected: Why the chosen language was selected.
        why_rejected: The reasons each alternative was rejected.
        business_alignment: How the language maximises the business goals.
        evidence_ids: The evidence grounding the explanation.
    """

    why_selected: str
    business_alignment: str
    why_rejected: tuple[str, ...] = ()
    evidence_ids: tuple[DLEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.why_selected or not self.why_selected.strip():
            raise InvalidExplanationError("LanguageExplanation.why_selected must be non-empty.")
        if not self.business_alignment or not self.business_alignment.strip():
            raise InvalidExplanationError(
                "LanguageExplanation.business_alignment must be non-empty."
            )
        object.__setattr__(
            self, "why_rejected", tuple(r for r in self.why_rejected if r and r.strip())
        )
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return self.evidence_ids
