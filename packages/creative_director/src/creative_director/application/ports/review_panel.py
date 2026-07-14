"""The Review panel port — the critic brain.

Given the assembled input and the consolidated evidence, an implementation reviews the
subject across the sixteen dimensions, returning a :class:`ReviewDraft` of cited
:class:`DimensionReview` s. The engine owns everything downstream — validating grounding,
scoring, evaluating approval, and building the graphs — so the panel proposes and the domain
disposes. The default is the deterministic rule-based panel; this port lets an AI panel be
swapped in without the engine changing. An implementation must cite only supplied evidence.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from creative_director.application.contracts import ReviewDraft, ReviewInput
from creative_director.domain.evidence.evidence import EvidenceGraph

__all__ = ["ReviewPanelPort"]


@runtime_checkable
class ReviewPanelPort(Protocol):
    """Reviews the subject across the sixteen dimensions."""

    async def review(
        self, review_input: ReviewInput, evidence: EvidenceGraph
    ) -> ReviewDraft:
        """Return cited dimension reviews (awaiting scoring and approval)."""
        ...
