"""Grounding gate — Draft Validation.

The synthesis port *proposes* the UX content; this stage is where the domain begins to
*dispose*. It verifies that every citation in the draft resolves in the consolidated
:class:`EvidenceGraph` — failing fast with a precise error if a synthesis adapter cited
evidence it was never given — so no ungrounded decision can enter the strategy.

This is the structural realisation of "everything must be evidence-backed": a UX decision
that cannot be traced to its evidence is rejected here, long before it reaches a report.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.errors import DesignDirectorError

from ux.application.contracts import UXDraft
from ux.domain.evidence.evidence import EvidenceGraph
from ux.domain.shared.ids import UXEvidenceId

__all__ = ["DraftValidator", "UngroundedUXError"]


class UngroundedUXError(DesignDirectorError):
    """Raised when a draft cites evidence absent from the consolidated graph."""

    code = "ungrounded_ux"
    http_status = 422


class DraftValidator:
    """Verifies a draft's citations all resolve in the evidence graph."""

    def validate(self, draft: UXDraft, evidence: EvidenceGraph) -> None:
        """Raise :class:`UngroundedUXError` if any citation is dangling."""
        missing = evidence.missing(self._referenced(draft))
        if missing:
            raise UngroundedUXError(
                "UX draft cites evidence absent from the consolidated graph.",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def _referenced(self, draft: UXDraft) -> Iterable[UXEvidenceId]:
        yield from draft.goals.evidence_ids()
        yield from draft.mental_model.evidence_ids
        yield from draft.pages.evidence_ids()
        yield from draft.journeys.evidence_ids()
        yield from draft.flows.evidence_ids()
        yield from draft.strategies.evidence_ids()
