"""Stage 3–10 gate — Draft Validation.

The synthesis port *proposes* the eight pillars plus risks and opportunities; this
stage is where the domain begins to *dispose*. It verifies that every citation in the
draft resolves in the consolidated :class:`EvidenceGraph` — failing fast with a precise
error if a synthesis adapter cited evidence it was never given — so no ungrounded claim
can slip through to become a decision.

This is the structural realisation of "no citation ⇒ no decision": a strategy that
cannot be traced to its evidence is rejected here, long before it reaches a report.
"""

from __future__ import annotations

from collections.abc import Iterable

from core.errors import DesignDirectorError

from strategy.application.contracts import StrategyDraft
from strategy.domain.evidence.evidence import EvidenceGraph
from strategy.domain.shared.ids import StrategyEvidenceId

__all__ = ["DraftValidator", "UngroundedStrategyError"]


class UngroundedStrategyError(DesignDirectorError):
    """Raised when a draft cites evidence absent from the consolidated graph."""

    code = "ungrounded_strategy"
    http_status = 422


class DraftValidator:
    """Verifies a draft's citations all resolve in the evidence graph."""

    def validate(self, draft: StrategyDraft, evidence: EvidenceGraph) -> None:
        """Raise :class:`UngroundedStrategyError` if any citation is dangling."""
        missing = evidence.missing(self._referenced(draft))
        if missing:
            raise UngroundedStrategyError(
                "Strategy draft cites evidence absent from the consolidated graph.",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def _referenced(self, draft: StrategyDraft) -> Iterable[StrategyEvidenceId]:
        yield from draft.goals.evidence_ids()
        yield from draft.customer.evidence_ids()
        yield from draft.positioning.evidence_ids()
        yield from draft.value_proposition.evidence_ids
        yield from draft.usp.evidence_ids
        yield from draft.messaging.all_evidence_ids()
        yield from draft.brand_voice.evidence_ids
        yield from draft.brand_personality.evidence_ids
        yield from draft.trust.all_evidence_ids()
        yield from draft.pricing.all_evidence_ids()
        yield from draft.retention.all_evidence_ids()
        for risk in draft.risks:
            yield from risk.evidence_ids
        for opportunity in draft.business_opportunities:
            yield from opportunity.evidence_ids
        for opportunity in draft.revenue_opportunities:
            yield from opportunity.evidence_ids
