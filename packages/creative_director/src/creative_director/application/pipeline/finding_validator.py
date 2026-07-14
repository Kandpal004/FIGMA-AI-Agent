"""Grounding gate — Finding Validation.

The critic panel *proposes* the dimension reviews; this stage is where the domain begins to
*dispose*. It verifies that every citation across the draft — dimension reviews, findings, and
required changes — resolves in the consolidated :class:`EvidenceGraph`, failing fast with a
precise error if the panel cited evidence it was never given, so no ungrounded ruling can
enter the review.

This is the structural realisation of "every decision must reference its evidence": a Creative
Director ruling that cannot be traced to its evidence is rejected here, long before it reaches
a report — which is exactly what lets the engine's authority be trusted.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.errors import DesignDirectorError

from creative_director.application.contracts import ReviewDraft
from creative_director.domain.evidence.evidence import EvidenceGraph
from creative_director.domain.shared.ids import CDEvidenceId

__all__ = ["FindingValidator", "UngroundedReviewError"]


class UngroundedReviewError(DesignDirectorError):
    """Raised when a draft cites evidence absent from the consolidated graph."""

    code = "ungrounded_creative_director_review"
    http_status = 422


class FindingValidator:
    """Verifies a draft's citations all resolve in the evidence graph."""

    def validate(self, draft: ReviewDraft, evidence: EvidenceGraph) -> None:
        """Raise :class:`UngroundedReviewError` if any citation is dangling."""
        missing = evidence.missing(self._referenced(draft))
        if missing:
            raise UngroundedReviewError(
                "Review draft cites evidence absent from the consolidated graph.",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def _referenced(self, draft: ReviewDraft) -> Iterable[CDEvidenceId]:
        for dr in draft.dimension_reviews:
            yield from dr.all_evidence_ids()
