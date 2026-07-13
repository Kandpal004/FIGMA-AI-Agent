"""RiskAnalyzer — deterministically derived strategic risks.

Risks are *derived* from the assembled strategy, never invented:

* a **knowledge gap** is a risk — the strategy rests on an unanswered question;
* a **low-confidence decision** is a risk — a shaky choice;
* a **platform constraint** is a risk — a real limitation the design must respect.

Each derived risk gets a deterministic category, severity, and likelihood, so the
same strategy always yields the same risk assessment. Iteration follows the
insertion order of the graphs, keeping output stable.

Pure application logic: no I/O, no randomness.
"""

from __future__ import annotations

from collections.abc import Sequence

from reasoning.domain.evidence.evidence import EvidenceGraph
from reasoning.domain.graph.decision import DecisionGraph
from reasoning.domain.risk.risk import Risk, RiskAssessment, RiskCategory
from reasoning.domain.shared.ids import RiskId
from reasoning.domain.shared.value_objects import (
    Likelihood,
    ReasoningDimension,
    Severity,
)
from reasoning.domain.strategy.gap import KnowledgeGap

__all__ = ["RiskAnalyzer"]

# A decision below this confidence is flagged as a risk.
_LOW_CONFIDENCE = 0.5
_VERY_LOW_CONFIDENCE = 0.3

# Which dimension maps to which risk category.
_DIMENSION_CATEGORY: dict[ReasoningDimension, RiskCategory] = {
    ReasoningDimension.BUSINESS: RiskCategory.BUSINESS,
    ReasoningDimension.CUSTOMER: RiskCategory.BUSINESS,
    ReasoningDimension.TARGET_MARKET: RiskCategory.BUSINESS,
    ReasoningDimension.CUSTOMER_PROBLEMS: RiskCategory.BUSINESS,
    ReasoningDimension.OBJECTIONS: RiskCategory.CONVERSION,
    ReasoningDimension.EMOTIONAL_TRIGGERS: RiskCategory.BRAND,
    ReasoningDimension.TRUST_MECHANISMS: RiskCategory.CONVERSION,
    ReasoningDimension.CONVERSION: RiskCategory.CONVERSION,
    ReasoningDimension.USER_EXPERIENCE: RiskCategory.UX,
    ReasoningDimension.ACCESSIBILITY: RiskCategory.ACCESSIBILITY,
    ReasoningDimension.PLATFORM_CONSTRAINTS: RiskCategory.PLATFORM,
    ReasoningDimension.COMPETITIVE: RiskCategory.BUSINESS,
    ReasoningDimension.DESIGN_SYSTEM: RiskCategory.BRAND,
    ReasoningDimension.TYPOGRAPHY: RiskCategory.BRAND,
    ReasoningDimension.SPACING: RiskCategory.BRAND,
    ReasoningDimension.VISUAL_HIERARCHY: RiskCategory.UX,
    ReasoningDimension.STRUCTURE: RiskCategory.UX,
    ReasoningDimension.CREATIVE_REVIEW: RiskCategory.BRAND,
}


class RiskAnalyzer:
    """Derives a :class:`RiskAssessment` from a strategy's graphs and gaps."""

    def analyze(
        self,
        decision_graph: DecisionGraph,
        evidence_graph: EvidenceGraph,
        gaps: Sequence[KnowledgeGap],
    ) -> RiskAssessment:
        risks: list[Risk] = []

        # 1. Platform constraints are real limitations that must be respected.
        for evidence in evidence_graph.by_dimension(
            ReasoningDimension.PLATFORM_CONSTRAINTS
        ):
            risks.append(
                Risk(
                    id=RiskId.new(),
                    category=RiskCategory.PLATFORM,
                    description=f"Platform constraint: {evidence.statement}",
                    severity=Severity.HIGH,
                    likelihood=Likelihood.ALMOST_CERTAIN,
                    mitigation="Design within the platform's supported surfaces.",
                    evidence_ids=(evidence.id,),
                )
            )

        # 2. Low-confidence decisions are shaky choices.
        for decision in decision_graph:
            if decision.confidence >= _LOW_CONFIDENCE:
                continue
            severity = (
                Severity.HIGH
                if decision.confidence < _VERY_LOW_CONFIDENCE
                else Severity.MEDIUM
            )
            risks.append(
                Risk(
                    id=RiskId.new(),
                    category=_DIMENSION_CATEGORY.get(
                        decision.dimension, RiskCategory.UX
                    ),
                    description=(
                        f"Low-confidence decision: {decision.question} "
                        f"(confidence {decision.confidence:.2f})."
                    ),
                    severity=severity,
                    likelihood=Likelihood.POSSIBLE,
                    threatens=(decision.id,),
                    mitigation="Gather more evidence or escalate for human review.",
                    evidence_ids=decision.evidence_ids,
                )
            )

        # 3. Knowledge gaps are unanswered questions the strategy rests on.
        for gap in gaps:
            severity = (
                Severity.HIGH
                if gap.dimension is ReasoningDimension.ACCESSIBILITY
                else Severity.MEDIUM
            )
            risks.append(
                Risk(
                    id=RiskId.new(),
                    category=_DIMENSION_CATEGORY.get(gap.dimension, RiskCategory.UX),
                    description=f"Knowledge gap: {gap.question}",
                    severity=severity,
                    likelihood=Likelihood.LIKELY,
                    mitigation=gap.suggested_action,
                )
            )

        return RiskAssessment(risks=tuple(risks))
