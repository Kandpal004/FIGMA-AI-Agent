"""TradeoffDeriver — surfaces the compromises baked into the decisions.

Wherever a decision chose one option over a genuinely-considered alternative, a
:class:`TradeOff` is recorded: what won, what was sacrificed, and why (with the
evidence behind the winner). Deterministic: it walks the decision graph in order
and derives one trade-off per decision that had a rejected alternative.
"""

from __future__ import annotations

from reasoning.domain.evidence.evidence import EvidenceGraph
from reasoning.domain.graph.decision import DecisionGraph
from reasoning.domain.shared.ids import TradeOffId
from reasoning.domain.tradeoff.tradeoff import TradeOff

__all__ = ["TradeoffDeriver"]


class TradeoffDeriver:
    """Derives trade-offs from the decisions a strategy made."""

    def derive(
        self, decision_graph: DecisionGraph, evidence_graph: EvidenceGraph
    ) -> tuple[TradeOff, ...]:
        tradeoffs: list[TradeOff] = []
        for decision in decision_graph:
            if not decision.considered:
                continue
            sacrificed = max(decision.considered, key=lambda option: option.score)
            tradeoffs.append(
                TradeOff(
                    id=TradeOffId.new(),
                    dimension=decision.dimension,
                    chosen=decision.chosen.label,
                    sacrificed=sacrificed.label,
                    rationale=(
                        f"Chosen for {decision.dimension.value}: scored "
                        f"{decision.chosen.score:.0f} vs {sacrificed.score:.0f}."
                    ),
                    decision_id=decision.id,
                    evidence_ids=decision.chosen.evidence_ids,
                )
            )
        return tuple(tradeoffs)
