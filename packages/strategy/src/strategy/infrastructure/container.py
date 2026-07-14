"""Composition root — where concrete adapters meet the strategy application.

Assembles the engine (with its pipeline stages) and the facade from injected ports.
Provides a batteries-included in-memory environment — defaulting to the deterministic
rule-based strategist and null input ports — and helpers to build the engine over any
ports (e.g. the real Phase 3–6 adapters).
"""

from __future__ import annotations

from dataclasses import dataclass

from strategy.application.ports.clock import Clock
from strategy.application.ports.competitor_insight import CompetitorInsightPort
from strategy.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from strategy.application.ports.reasoning import ReasoningPort
from strategy.application.ports.research_input import ResearchInputPort
from strategy.application.ports.synthesis import StrategySynthesisPort
from strategy.application.ports.unit_of_work import UnitOfWorkFactory
from strategy.application.strategy_engine import StrategyEngine
from strategy.infrastructure.adapters.inmemory_inputs import (
    NullCompetitorInsight,
    NullKnowledgeAdvisor,
    NullReasoning,
    NullResearchInput,
)
from strategy.infrastructure.adapters.rule_based_strategist import RuleBasedStrategist
from strategy.infrastructure.inmemory import (
    ReportStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from strategy.interfaces.strategy_facade import StrategyFacade

__all__ = [
    "StrategyEnvironment",
    "build_engine",
    "build_facade",
    "build_in_memory_environment",
]


def build_engine(
    *,
    research: ResearchInputPort,
    knowledge: KnowledgeAdvisorPort,
    competitor: CompetitorInsightPort,
    reasoning: ReasoningPort,
    synthesis: StrategySynthesisPort,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
) -> StrategyEngine:
    """Assemble a :class:`StrategyEngine` from its ports."""
    return StrategyEngine(
        research=research,
        knowledge=knowledge,
        competitor=competitor,
        reasoning=reasoning,
        synthesis=synthesis,
        unit_of_work_factory=unit_of_work_factory,
        clock=clock,
    )


def build_facade(
    engine: StrategyEngine, uow_factory: UnitOfWorkFactory
) -> StrategyFacade:
    """Wrap an engine in its inbound facade."""
    return StrategyFacade(engine, uow_factory)


@dataclass(frozen=True, slots=True)
class StrategyEnvironment:
    """A fully wired engine plus a handle to its in-memory report store."""

    facade: StrategyFacade
    engine: StrategyEngine
    storage: ReportStorage
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
    *,
    research: ResearchInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    competitor: CompetitorInsightPort | None = None,
    reasoning: ReasoningPort | None = None,
    synthesis: StrategySynthesisPort | None = None,
    clock: Clock | None = None,
) -> StrategyEnvironment:
    """Stand up the whole engine over in-memory persistence.

    Unwired input ports default to null adapters (contributing no evidence), and the
    strategist defaults to the deterministic rule-based implementation.
    """
    storage = ReportStorage()
    uow_factory = make_unit_of_work_factory(storage)
    engine = build_engine(
        research=research or NullResearchInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        competitor=competitor or NullCompetitorInsight(),
        reasoning=reasoning or NullReasoning(),
        synthesis=synthesis or RuleBasedStrategist(),
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return StrategyEnvironment(
        facade=facade,
        engine=engine,
        storage=storage,
        unit_of_work_factory=uow_factory,
    )
