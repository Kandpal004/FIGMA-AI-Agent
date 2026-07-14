"""Stage 13 — Prioritization.

Scores every decision in the graph on reach, impact, confidence, and effort — the
reach/impact/effort profile is a deterministic function of the decision's strategic
domain; confidence carries through from the decision's evidence — yielding a RICE-style
:class:`PriorityMatrix` that gives downstream execution an evidence-backed sequence.
"""

from __future__ import annotations

from strategy.domain.decision.decision_graph import DecisionGraph
from strategy.domain.prioritization.priority_matrix import (
    PrioritizedItem,
    PriorityMatrix,
)
from strategy.domain.shared.ids import PrioritizedItemId
from strategy.domain.shared.value_objects import (
    DecisionType,
    EffortScore,
    ImpactScore,
    ReachScore,
)

__all__ = ["Prioritizer"]

# (reach, impact, effort) profile per strategic domain.
_PROFILE: dict[DecisionType, tuple[int, int, int]] = {
    DecisionType.GOAL: (4, 4, 3),
    DecisionType.CUSTOMER: (5, 5, 2),
    DecisionType.POSITIONING: (5, 5, 4),
    DecisionType.VALUE: (5, 4, 3),
    DecisionType.MESSAGING: (5, 4, 2),
    DecisionType.TRUST: (4, 4, 2),
    DecisionType.PRICING: (4, 3, 3),
    DecisionType.RETENTION: (3, 4, 4),
}


class Prioritizer:
    """Builds the priority matrix from the decision graph."""

    def prioritize(self, decision_graph: DecisionGraph) -> PriorityMatrix:
        items: list[PrioritizedItem] = []
        for decision in decision_graph:
            reach, impact, effort = _PROFILE[decision.type]
            items.append(
                PrioritizedItem(
                    id=PrioritizedItemId.new(),
                    decision_id=decision.id,
                    title=decision.title,
                    reach=ReachScore(reach),
                    impact=ImpactScore(impact),
                    confidence=decision.confidence,
                    effort=EffortScore(effort),
                    evidence_ids=decision.evidence_ids,
                )
            )
        return PriorityMatrix.of(items)
