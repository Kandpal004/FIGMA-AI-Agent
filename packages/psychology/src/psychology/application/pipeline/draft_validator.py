"""Grounding gate — Draft Validation.

The synthesis port *proposes* the psychology content; this stage is where the domain
begins to *dispose*. It verifies that every citation in the draft resolves in the
consolidated :class:`EvidenceGraph` — failing fast with a precise error if a synthesis
adapter cited evidence it was never given — so no ungrounded claim can enter the model.

This is the structural realisation of "everything must be evidence-backed": a
determination that cannot be traced to its evidence is rejected here, long before it
reaches a report.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.errors import DesignDirectorError

from psychology.application.contracts import PsychologyDraft
from psychology.domain.evidence.evidence import EvidenceGraph
from psychology.domain.shared.ids import PsychologyEvidenceId

__all__ = ["DraftValidator", "UngroundedPsychologyError"]


class UngroundedPsychologyError(DesignDirectorError):
    """Raised when a draft cites evidence absent from the consolidated graph."""

    code = "ungrounded_psychology"
    http_status = 422


class DraftValidator:
    """Verifies a draft's citations all resolve in the evidence graph."""

    def validate(self, draft: PsychologyDraft, evidence: EvidenceGraph) -> None:
        """Raise :class:`UngroundedPsychologyError` if any citation is dangling."""
        missing = evidence.missing(self._referenced(draft))
        if missing:
            raise UngroundedPsychologyError(
                "Psychology draft cites evidence absent from the consolidated graph.",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def _referenced(self, draft: PsychologyDraft) -> Iterable[PsychologyEvidenceId]:
        yield from draft.profile.evidence_ids()
        yield from draft.personas.evidence_ids()
        yield from draft.buying_personas.evidence_ids()
        yield from draft.jobs.evidence_ids()
        yield from draft.buying_journey.evidence_ids()
        yield from draft.decision_journey.evidence_ids()
        for cell in draft.objections:
            yield from cell.evidence_ids
        for cell in draft.behaviors:
            yield from cell.evidence_ids
        for cell in draft.value_cells:
            yield from cell.evidence_ids
        for cell in draft.retention_cells:
            yield from cell.evidence_ids
        if draft.maslow is not None:
            yield from draft.maslow.evidence_ids
        if draft.hook is not None:
            yield from draft.hook.evidence_ids
        yield from draft.principles.evidence_ids()
