"""Stage 12 — Strategy Graph construction.

Builds the executive interlock map: one :class:`StrategyComponent` per strategic domain
present in the decision graph, wired by typed :class:`StrategyEdge` s that show how the
pillars inform, reinforce, and depend on one another. Where the decision graph is the
detail, this is the board a strategist reads at a glance.
"""

from __future__ import annotations

from strategy.domain.decision.decision_graph import DecisionGraph
from strategy.domain.decision.strategy_graph import (
    StrategyComponent,
    StrategyEdge,
    StrategyGraph,
)
from strategy.domain.shared.ids import StrategyComponentId, StrategyEdgeId
from strategy.domain.shared.value_objects import DecisionType, StrategyRelation

__all__ = ["StrategyGraphBuilder"]

_NAMES: dict[DecisionType, str] = {
    DecisionType.GOAL: "Business Goals",
    DecisionType.CUSTOMER: "Customer",
    DecisionType.POSITIONING: "Positioning",
    DecisionType.VALUE: "Value Proposition",
    DecisionType.MESSAGING: "Messaging",
    DecisionType.TRUST: "Trust",
    DecisionType.PRICING: "Pricing",
    DecisionType.RETENTION: "Retention",
}

# Directed interlocks between pillars, applied only when both endpoints exist.
_INTERLOCKS: tuple[tuple[DecisionType, DecisionType, StrategyRelation], ...] = (
    (DecisionType.GOAL, DecisionType.CUSTOMER, StrategyRelation.INFORMS),
    (DecisionType.CUSTOMER, DecisionType.POSITIONING, StrategyRelation.INFORMS),
    (DecisionType.POSITIONING, DecisionType.VALUE, StrategyRelation.INFORMS),
    (DecisionType.POSITIONING, DecisionType.MESSAGING, StrategyRelation.INFORMS),
    (DecisionType.POSITIONING, DecisionType.PRICING, StrategyRelation.INFORMS),
    (DecisionType.POSITIONING, DecisionType.TRUST, StrategyRelation.REINFORCES),
    (DecisionType.VALUE, DecisionType.MESSAGING, StrategyRelation.REINFORCES),
    (DecisionType.TRUST, DecisionType.PRICING, StrategyRelation.REINFORCES),
    (DecisionType.CUSTOMER, DecisionType.RETENTION, StrategyRelation.INFORMS),
)


class StrategyGraphBuilder:
    """Builds the strategy interlock map from the decision graph."""

    def build(self, decision_graph: DecisionGraph) -> StrategyGraph:
        present = {d.type for d in decision_graph}
        component_ids: dict[DecisionType, StrategyComponentId] = {}
        components: list[StrategyComponent] = []
        for domain in DecisionType:
            if domain not in present:
                continue
            component = StrategyComponent(
                id=StrategyComponentId.new(),
                domain=domain,
                name=_NAMES[domain],
                summary=f"{_NAMES[domain]} pillar.",
            )
            components.append(component)
            component_ids[domain] = component.id

        edges: list[StrategyEdge] = []
        for source_domain, target_domain, relation in _INTERLOCKS:
            source = component_ids.get(source_domain)
            target = component_ids.get(target_domain)
            if source is not None and target is not None:
                edges.append(
                    StrategyEdge(
                        id=StrategyEdgeId.new(),
                        source=source,
                        target=target,
                        relation=relation,
                    )
                )
        return StrategyGraph.of(components, edges)
