"""Grounding gate — Draft Validation.

The designer *proposes* the visual language; this stage is where the domain begins to
*dispose*. It verifies that every citation in the draft — the DNA, the token system, the
philosophies and personalities, the systems, and the language selection — resolves in the
consolidated :class:`EvidenceGraph`, failing fast with a precise error if the designer cited
evidence it was never given, so no ungrounded visual decision can enter the specification.

This is the structural realisation of "every recommendation must reference its evidence": a
visual decision that cannot be traced to its evidence is rejected here — which is exactly what
keeps the language from being arbitrary or AI-generated.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.errors import DesignDirectorError

from design_language.application.contracts import LanguageDraft
from design_language.domain.evidence.evidence import EvidenceGraph
from design_language.domain.shared.ids import DLEvidenceId

__all__ = ["DraftValidator", "UngroundedLanguageError"]


class UngroundedLanguageError(DesignDirectorError):
    """Raised when a draft cites evidence absent from the consolidated graph."""

    code = "ungrounded_design_language"
    http_status = 422


class DraftValidator:
    """Verifies a draft's citations all resolve in the evidence graph."""

    def validate(self, draft: LanguageDraft, evidence: EvidenceGraph) -> None:
        """Raise :class:`UngroundedLanguageError` if any citation is dangling."""
        missing = evidence.missing(self._referenced(draft))
        if missing:
            raise UngroundedLanguageError(
                "Language draft cites evidence absent from the consolidated graph.",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def _referenced(self, draft: LanguageDraft) -> Iterable[DLEvidenceId]:
        yield from draft.visual_dna.all_evidence_ids()
        yield from draft.tokens.all_evidence_ids()
        yield from draft.philosophies.evidence_ids()
        yield from draft.personalities.evidence_ids()
        yield from draft.grid_system.all_evidence_ids()
        yield from draft.responsive_strategy.all_evidence_ids()
        yield from draft.language_selection.all_evidence_ids()
