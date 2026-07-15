"""Grounding gate — Draft Validation.

The brain *proposes* the composition; this stage is where the domain begins to *dispose*. It
verifies that every citation in the draft — across component decisions and compatibility links —
resolves in the consolidated :class:`EvidenceGraph`, failing fast with a precise error if the
brain cited evidence it was never given, so no ungrounded component decision can enter the
specification.

This is the structural realisation of "every component exists because the evidence says it
improves a business outcome": a component the brain cannot ground is rejected here, long before
it reaches a specification.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.errors import DesignDirectorError

from component_intelligence.application.contracts import CompositionDraft
from component_intelligence.domain.evidence.evidence import EvidenceGraph
from component_intelligence.domain.shared.ids import CIEvidenceId

__all__ = ["DraftValidator", "UngroundedCompositionError"]


class UngroundedCompositionError(DesignDirectorError):
    """Raised when a draft cites evidence absent from the consolidated graph."""

    code = "ungrounded_component_intelligence"
    http_status = 422


class DraftValidator:
    """Verifies a draft's citations all resolve in the evidence graph."""

    def validate(self, draft: CompositionDraft, evidence: EvidenceGraph) -> None:
        """Raise :class:`UngroundedCompositionError` if any citation is dangling."""
        missing = evidence.missing(self._referenced(draft))
        if missing:
            raise UngroundedCompositionError(
                "Composition draft cites evidence absent from the consolidated graph.",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def _referenced(self, draft: CompositionDraft) -> Iterable[CIEvidenceId]:
        for decision in draft.composition:
            yield from decision.all_evidence_ids()
        yield from draft.compatibility.evidence_ids()
