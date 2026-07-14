"""Stage 11 — Decision Graph construction.

Lifts the validated draft's pillars into a traversable :class:`DecisionGraph`: one
:class:`StrategicDecision` per grounded section, wired by ``DERIVES_FROM`` edges into a
coherent derivation — goals and the customer model are foundational; positioning
derives from them; value, messaging, trust, pricing, and retention derive from
positioning (and the customer). A section with no citations produces no decision, so
the graph carries only grounded choices.

Each decision's confidence is the mean confidence of the evidence it cites — a
deterministic, explainable roll-up, not a guess.
"""

from __future__ import annotations

from collections.abc import Sequence

from strategy.application.contracts import StrategyDraft
from strategy.domain.decision.decision import StrategicDecision
from strategy.domain.decision.decision_graph import DecisionEdge, DecisionGraph
from strategy.domain.evidence.evidence import EvidenceGraph
from strategy.domain.shared.ids import (
    DecisionEdgeId,
    StrategicDecisionId,
    StrategyEvidenceId,
)
from strategy.domain.shared.value_objects import (
    Confidence,
    ConsideredAlternative,
    DecisionRelation,
    DecisionType,
    Priority,
)

__all__ = ["DecisionGraphBuilder"]

_PRIORITY: dict[DecisionType, int] = {
    DecisionType.GOAL: 5,
    DecisionType.CUSTOMER: 5,
    DecisionType.POSITIONING: 5,
    DecisionType.VALUE: 4,
    DecisionType.MESSAGING: 4,
    DecisionType.TRUST: 4,
    DecisionType.PRICING: 3,
    DecisionType.RETENTION: 3,
}


class DecisionGraphBuilder:
    """Builds the decision graph from a validated draft."""

    def build(self, draft: StrategyDraft, evidence: EvidenceGraph) -> DecisionGraph:
        decisions: list[StrategicDecision] = []
        role_ids: dict[str, StrategicDecisionId] = {}

        def add(
            role: str,
            decision_type: DecisionType,
            title: str,
            statement: str,
            rationale: str,
            evidence_ids: Sequence[StrategyEvidenceId],
            considered: Sequence[ConsideredAlternative] = (),
        ) -> None:
            ids = tuple(evidence_ids)
            if not ids:  # no citation ⇒ no decision
                return
            decision = StrategicDecision(
                id=StrategicDecisionId.new(),
                type=decision_type,
                title=title,
                statement=statement,
                rationale=rationale,
                confidence=self._confidence(ids, evidence),
                priority=Priority(_PRIORITY[decision_type]),
                considered=tuple(considered),
                evidence_ids=ids,
            )
            decisions.append(decision)
            role_ids[role] = decision.id

        # Foundational: goals + customer.
        for index, goal in enumerate(draft.goals):
            add(
                f"goal:{index}",
                DecisionType.GOAL,
                title=f"Pursue: {goal.statement}"[:120],
                statement=goal.statement,
                rationale=f"Priority {int(goal.priority)} {goal.category.value} goal.",
                evidence_ids=goal.evidence_ids,
            )
        add(
            "customer",
            DecisionType.CUSTOMER,
            title="Serve the defined ideal customer",
            statement=draft.customer.icp.summary,
            rationale="The ideal customer profile all downstream strategy targets.",
            evidence_ids=draft.customer.evidence_ids(),
        )
        # Keystone: positioning.
        add(
            "positioning",
            DecisionType.POSITIONING,
            title=f"Position as {draft.positioning.tier.value}",
            statement=draft.positioning.statement.statement,
            rationale=draft.positioning.brand.perception,
            evidence_ids=draft.positioning.evidence_ids(),
            considered=draft.positioning.statement.considered,
        )
        # Derived pillars.
        add(
            "value",
            DecisionType.VALUE,
            title="Lead with the value proposition",
            statement=draft.value_proposition.headline_promise,
            rationale=draft.value_proposition.primary_benefit,
            evidence_ids=draft.value_proposition.evidence_ids,
        )
        add(
            "messaging",
            DecisionType.MESSAGING,
            title="Communicate the messaging spine",
            statement=draft.messaging.primary_message,
            rationale="The message architecture the experience must carry.",
            evidence_ids=draft.messaging.all_evidence_ids(),
        )
        add(
            "trust",
            DecisionType.TRUST,
            title="Establish the required trust",
            statement="Carry the prioritised trust elements across the journey.",
            rationale="Trust removes the friction that blocks conversion.",
            evidence_ids=draft.trust.all_evidence_ids(),
        )
        add(
            "pricing",
            DecisionType.PRICING,
            title=f"Adopt a {draft.pricing.posture.value} pricing posture",
            statement=f"Communicate {draft.pricing.posture.value} pricing signals.",
            rationale="Pricing signals must match the positioning tier.",
            evidence_ids=draft.pricing.all_evidence_ids(),
        )
        add(
            "retention",
            DecisionType.RETENTION,
            title="Build the retention engine",
            statement=draft.retention.lifecycle_focus or "Retain and grow customers.",
            rationale="Retention compounds the value of every acquisition.",
            evidence_ids=draft.retention.all_evidence_ids(),
        )

        edges = self._edges(role_ids)
        return DecisionGraph.of(decisions, edges)

    @staticmethod
    def _confidence(
        evidence_ids: Sequence[StrategyEvidenceId], evidence: EvidenceGraph
    ) -> Confidence:
        values = [evidence.get(eid).confidence.value for eid in evidence_ids]
        return Confidence.clamp(sum(values) / len(values)) if values else Confidence.of(0.5)

    @staticmethod
    def _edges(role_ids: dict[str, StrategicDecisionId]) -> list[DecisionEdge]:
        edges: list[DecisionEdge] = []

        def link(
            source_role: str, target_role: str, relation: DecisionRelation
        ) -> None:
            source = role_ids.get(source_role)
            target = role_ids.get(target_role)
            if source is not None and target is not None:
                edges.append(
                    DecisionEdge(
                        id=DecisionEdgeId.new(),
                        source=source,
                        target=target,
                        relation=relation,
                    )
                )

        goal_roles = [r for r in role_ids if r.startswith("goal:")]
        for role in goal_roles:
            link("customer", role, DecisionRelation.DERIVES_FROM)
        link("positioning", "customer", DecisionRelation.DERIVES_FROM)
        link("value", "positioning", DecisionRelation.DERIVES_FROM)
        link("messaging", "positioning", DecisionRelation.DERIVES_FROM)
        link("messaging", "value", DecisionRelation.SUPPORTS)
        link("trust", "positioning", DecisionRelation.DERIVES_FROM)
        link("trust", "customer", DecisionRelation.SUPPORTS)
        link("pricing", "positioning", DecisionRelation.DERIVES_FROM)
        link("retention", "customer", DecisionRelation.DERIVES_FROM)
        return edges
