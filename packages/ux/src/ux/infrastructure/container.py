"""Composition root — where concrete adapters meet the UX application.

Assembles the engine (with its pipeline stages) and the facade from injected ports.
Provides a batteries-included in-memory environment — defaulting to the deterministic
rule-based UX strategist and null input ports — and helpers to build the engine over any
ports (e.g. the real Phase 9 / Phase 8 / Phase 7 / Phase 3 adapters).
"""

from __future__ import annotations

from dataclasses import dataclass

from ux.application.ports.brand_input import BrandInputPort
from ux.application.ports.business_strategy_input import BusinessStrategyInputPort
from ux.application.ports.clock import Clock
from ux.application.ports.competitor_insight import CompetitorInsightPort
from ux.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from ux.application.ports.psychology_input import PsychologyInputPort
from ux.application.ports.reasoning import ReasoningPort
from ux.application.ports.research_input import ResearchInputPort
from ux.application.ports.synthesis import UXSynthesisPort
from ux.application.ports.unit_of_work import UnitOfWorkFactory
from ux.application.ux_engine import UXEngine
from ux.infrastructure.adapters.inmemory_inputs import (
    NullBrandInput,
    NullBusinessStrategyInput,
    NullCompetitorInsight,
    NullKnowledgeAdvisor,
    NullPsychologyInput,
    NullReasoning,
    NullResearchInput,
)
from ux.infrastructure.adapters.rule_based_ux_strategist import RuleBasedUXStrategist
from ux.infrastructure.inmemory import (
    ReportStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from ux.interfaces.ux_facade import UXFacade

__all__ = [
    "UXEnvironment",
    "build_engine",
    "build_facade",
    "build_in_memory_environment",
]


def build_engine(
    *,
    psychology: PsychologyInputPort,
    brand: BrandInputPort,
    business_strategy: BusinessStrategyInputPort,
    knowledge: KnowledgeAdvisorPort,
    research: ResearchInputPort,
    competitor: CompetitorInsightPort,
    reasoning: ReasoningPort,
    synthesis: UXSynthesisPort,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
) -> UXEngine:
    """Assemble a :class:`UXEngine` from its ports."""
    return UXEngine(
        psychology=psychology,
        brand=brand,
        business_strategy=business_strategy,
        knowledge=knowledge,
        research=research,
        competitor=competitor,
        reasoning=reasoning,
        synthesis=synthesis,
        unit_of_work_factory=unit_of_work_factory,
        clock=clock,
    )


def build_facade(engine: UXEngine, uow_factory: UnitOfWorkFactory) -> UXFacade:
    """Wrap an engine in its inbound facade."""
    return UXFacade(engine, uow_factory)


@dataclass(frozen=True, slots=True)
class UXEnvironment:
    """A fully wired engine plus a handle to its in-memory report store."""

    facade: UXFacade
    engine: UXEngine
    storage: ReportStorage
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
    *,
    psychology: PsychologyInputPort | None = None,
    brand: BrandInputPort | None = None,
    business_strategy: BusinessStrategyInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    research: ResearchInputPort | None = None,
    competitor: CompetitorInsightPort | None = None,
    reasoning: ReasoningPort | None = None,
    synthesis: UXSynthesisPort | None = None,
    clock: Clock | None = None,
) -> UXEnvironment:
    """Stand up the whole engine over in-memory persistence.

    Unwired input ports default to null adapters (contributing no signals), and the
    strategist defaults to the deterministic rule-based implementation.
    """
    storage = ReportStorage()
    uow_factory = make_unit_of_work_factory(storage)
    engine = build_engine(
        psychology=psychology or NullPsychologyInput(),
        brand=brand or NullBrandInput(),
        business_strategy=business_strategy or NullBusinessStrategyInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        research=research or NullResearchInput(),
        competitor=competitor or NullCompetitorInsight(),
        reasoning=reasoning or NullReasoning(),
        synthesis=synthesis or RuleBasedUXStrategist(),
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return UXEnvironment(
        facade=facade, engine=engine, storage=storage, unit_of_work_factory=uow_factory
    )
