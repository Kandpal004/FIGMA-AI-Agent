"""Stage 14 — Risk & Opportunity analysis.

Assembles the draft's proposed risks and opportunities into their registers. When the
strategy rests on thin evidence, it also raises a cited-free *evidence-gap* risk — an
honest meta-observation that the strategy needs more grounding before large bets ride
on it. (Meta-risks carry no citations because their subject is the *absence* of
evidence; the report's provenance invariant permits an empty citation set, only
rejecting citations that dangle.)
"""

from __future__ import annotations

from strategy.application.contracts import StrategyDraft
from strategy.domain.analysis.opportunity import OpportunityRegister
from strategy.domain.analysis.risk import BusinessRisk, RiskRegister
from strategy.domain.evidence.evidence import EvidenceGraph
from strategy.domain.shared.ids import BusinessRiskId
from strategy.domain.shared.value_objects import (
    Likelihood,
    RiskCategory,
    Severity,
)

__all__ = ["RiskOpportunityAnalyzer"]

# Below this many pieces of evidence, the strategy is flagged as under-grounded.
_THIN_EVIDENCE = 3


class RiskOpportunityAnalyzer:
    """Builds the risk and opportunity registers from the draft."""

    def analyze(
        self, draft: StrategyDraft, evidence: EvidenceGraph
    ) -> tuple[RiskRegister, OpportunityRegister]:
        risks = list(draft.risks)
        if len(evidence) < _THIN_EVIDENCE:
            risks.append(
                BusinessRisk(
                    id=BusinessRiskId.new(),
                    category=RiskCategory.EVIDENCE_GAP,
                    description=(
                        "Strategy rests on limited evidence; validate key assumptions "
                        "with more research before committing large investments."
                    ),
                    severity=Severity(3),
                    likelihood=Likelihood(4),
                    mitigation="Gather additional research, competitor, and voice-of-customer evidence.",
                )
            )
        register = OpportunityRegister.of(
            business=draft.business_opportunities,
            revenue=draft.revenue_opportunities,
        )
        return RiskRegister.of(risks), register
