"""Stage 15a — Quality scoring.

Computes the report's calibrated quality picture deterministically:

* **coverage** — how many of the required strategic outputs the draft actually
  produced, out of the full checklist.
* **grounding** — the fraction of decisions whose citations resolve (``1.0`` by the
  decision-graph builder's construction, surfaced here so the metric is auditable).
* **confidence** — the mean confidence across the graph's decisions.
* **completeness** — how fully the customer and interlock picture is filled in.
"""

from __future__ import annotations

from strategy.application.contracts import StrategyDraft
from strategy.domain.decision.decision_graph import DecisionGraph
from strategy.domain.quality.quality import StrategyQualityMetrics
from strategy.domain.shared.value_objects import Confidence, Percentage

__all__ = ["QualityScorer"]


class QualityScorer:
    """Scores the strategy's coverage, grounding, confidence, and completeness."""

    def score(
        self, draft: StrategyDraft, decision_graph: DecisionGraph
    ) -> StrategyQualityMetrics:
        coverage = Percentage.ratio(*self._coverage(draft))
        decisions = tuple(decision_graph)
        grounded = sum(1 for d in decisions if d.evidence_ids)
        grounding = Percentage.ratio(grounded, len(decisions)) if decisions else Percentage.of(0.0)
        if decisions:
            confidence = Confidence.clamp(
                sum(d.confidence.value for d in decisions) / len(decisions)
            )
        else:
            confidence = Confidence.of(0.0)
        completeness = Percentage.ratio(*self._completeness(draft))
        return StrategyQualityMetrics(
            coverage=coverage,
            grounding=grounding,
            confidence=confidence,
            completeness=completeness,
        )

    @staticmethod
    def _coverage(draft: StrategyDraft) -> tuple[int, int]:
        checklist = (
            bool(len(draft.goals)),
            bool(len(draft.customer.personas)),
            bool(draft.customer.icp.summary),
            bool(len(draft.customer.jobs)),
            bool(len(draft.customer.journey)),
            bool(draft.value_proposition.headline_promise),
            bool(draft.usp.statement),
            bool(draft.messaging.primary_message),
            bool(draft.brand_voice.tone),
            bool(draft.brand_personality.traits or draft.brand_personality.archetype),
            bool(draft.trust.elements),
            bool(draft.pricing.signals),
            bool(draft.pricing.offer.offers),
            bool(draft.pricing.urgency.kinds),
            bool(draft.trust.social_proof.kinds),
            bool(draft.retention.levers),
        )
        return sum(1 for present in checklist if present), len(checklist)

    @staticmethod
    def _completeness(draft: StrategyDraft) -> tuple[int, int]:
        parts = (
            bool(draft.customer.pains),
            bool(draft.customer.objections),
            bool(draft.customer.motivations),
            bool(draft.customer.emotions),
            bool(draft.customer.journey.stages),
            bool(draft.messaging.pillars),
            bool(draft.positioning.visual.adjectives),
            bool(draft.value_proposition.differentiators),
        )
        return sum(1 for present in parts if present), len(parts)
