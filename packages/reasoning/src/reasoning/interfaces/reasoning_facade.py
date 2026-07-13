"""The Reasoning facade — the inbound entry point of the engine.

The single surface everything above the engine calls: the Director (which must
obtain a sound strategy before any design begins), an API, or tests. It runs the
engine, retrieves produced strategies, and explains individual decisions by
walking the reason/evidence graphs — returning serializable views, never domain
aggregates. It owns no reasoning logic; it delegates to the engine and reads
through the unit of work.
"""

from __future__ import annotations

from reasoning.application.commands import GenerateStrategy
from reasoning.application.ports.unit_of_work import UnitOfWorkFactory
from reasoning.application.reasoning_engine import ReasoningEngine
from reasoning.domain.shared.ids import DecisionNodeId, StrategyId
from reasoning.interfaces.dto import (
    AlternativeView,
    ConfidenceView,
    DesignStrategyView,
    GapView,
    ReasoningTraceView,
    RiskView,
)

__all__ = ["ReasoningFacade"]


class ReasoningFacade:
    """Reason, retrieve, and explain — commands in, views out."""

    def __init__(
        self, engine: ReasoningEngine, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        self._engine = engine
        self._uow = unit_of_work_factory

    async def reason(self, command: GenerateStrategy) -> DesignStrategyView:
        """Run the full pipeline and return the produced strategy view."""
        strategy = await self._engine.generate(command)
        return DesignStrategyView.from_strategy(strategy)

    async def get(self, strategy_id: StrategyId) -> DesignStrategyView:
        """Retrieve a produced strategy.

        Raises:
            NotFoundError: If no such strategy exists.
        """
        async with self._uow() as uow:
            strategy = await uow.strategies.get(strategy_id)
        return DesignStrategyView.from_strategy(strategy)

    async def alternatives(self, strategy_id: StrategyId) -> list[AlternativeView]:
        """The alternative strategies considered."""
        view = await self.get(strategy_id)
        return view.alternatives

    async def risks(self, strategy_id: StrategyId) -> list[RiskView]:
        """The risk assessment."""
        view = await self.get(strategy_id)
        return view.risks

    async def confidence(self, strategy_id: StrategyId) -> ConfidenceView:
        """The confidence breakdown."""
        view = await self.get(strategy_id)
        return view.confidence

    async def gaps(self, strategy_id: StrategyId) -> list[GapView]:
        """The knowledge gaps recorded."""
        view = await self.get(strategy_id)
        return view.gaps

    async def explain(
        self, strategy_id: StrategyId, decision_id: DecisionNodeId
    ) -> ReasoningTraceView:
        """Explain one decision by walking its reasons down to cited evidence."""
        async with self._uow() as uow:
            strategy = await uow.strategies.get(strategy_id)
        decision = strategy.decision_graph.get(decision_id)
        reasons = [strategy.reason_graph.get(rid) for rid in decision.reason_ids]
        evidence_ids = list(decision.evidence_ids)
        for reason in reasons:
            evidence_ids.extend(reason.evidence_ids)
        seen: set[str] = set()
        evidence = []
        for eid in evidence_ids:
            if str(eid) in seen:
                continue
            seen.add(str(eid))
            evidence.append(strategy.evidence_graph.get(eid))
        return ReasoningTraceView.build(decision, reasons, evidence)
