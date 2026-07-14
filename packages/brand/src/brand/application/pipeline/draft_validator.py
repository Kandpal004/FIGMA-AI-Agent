"""Grounding gate — Draft Validation.

The synthesis port *proposes* the brand's content; this stage is where the domain begins
to *dispose*. It verifies that every citation in the draft resolves in the consolidated
:class:`EvidenceGraph` — failing fast with a precise error if a synthesis adapter cited
evidence it was never given — so no ungrounded claim can become a brand decision.

This is the structural realisation of "no citation ⇒ no brand decision": a brand that
cannot be traced to its evidence is rejected here, long before it reaches a report.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.errors import DesignDirectorError

from brand.application.contracts import BrandDraft
from brand.domain.evidence.evidence import EvidenceGraph
from brand.domain.shared.ids import BrandEvidenceId

__all__ = ["DraftValidator", "UngroundedBrandError"]


class UngroundedBrandError(DesignDirectorError):
    """Raised when a draft cites evidence absent from the consolidated graph."""

    code = "ungrounded_brand"
    http_status = 422


class DraftValidator:
    """Verifies a draft's citations all resolve in the evidence graph."""

    def validate(self, draft: BrandDraft, evidence: EvidenceGraph) -> None:
        """Raise :class:`UngroundedBrandError` if any citation is dangling."""
        missing = evidence.missing(self._referenced(draft))
        if missing:
            raise UngroundedBrandError(
                "Brand draft cites evidence absent from the consolidated graph.",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def _referenced(self, draft: BrandDraft) -> Iterable[BrandEvidenceId]:
        yield from draft.classification.evidence_ids
        yield from draft.identity.evidence_ids()
        yield from draft.character.evidence_ids()
        yield from draft.emotional.evidence_ids()
        yield from draft.visual.evidence_ids()
        yield from draft.verbal.evidence_ids()
