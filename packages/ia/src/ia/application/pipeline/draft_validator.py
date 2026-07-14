"""Grounding gate — Draft Validation.

The synthesis port *proposes* the IA content; this stage is where the domain begins to
*dispose*. It verifies that every citation in the draft resolves in the consolidated
:class:`EvidenceGraph` — failing fast with a precise error if a synthesis adapter cited
evidence it was never given — so no ungrounded decision can enter the architecture.

This is the structural realisation of "everything must be evidence-backed": an IA decision
that cannot be traced to its evidence is rejected here, long before it reaches a report.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.errors import DesignDirectorError

from ia.application.contracts import IADraft
from ia.domain.evidence.evidence import EvidenceGraph
from ia.domain.shared.ids import IAEvidenceId

__all__ = ["DraftValidator", "UngroundedIAError"]


class UngroundedIAError(DesignDirectorError):
    """Raised when a draft cites evidence absent from the consolidated graph."""

    code = "ungrounded_ia"
    http_status = 422


class DraftValidator:
    """Verifies a draft's citations all resolve in the evidence graph."""

    def validate(self, draft: IADraft, evidence: EvidenceGraph) -> None:
        """Raise :class:`UngroundedIAError` if any citation is dangling."""
        missing = evidence.missing(self._referenced(draft))
        if missing:
            raise UngroundedIAError(
                "IA draft cites evidence absent from the consolidated graph.",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def _referenced(self, draft: IADraft) -> Iterable[IAEvidenceId]:
        yield from draft.sitemap.evidence_ids()
        yield from draft.navigation.evidence_ids()
        yield from draft.relationships.evidence_ids()
        yield from draft.discovery.evidence_ids()
