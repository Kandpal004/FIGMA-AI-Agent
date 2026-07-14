"""Composition root — where concrete adapters meet the brand application.

Assembles the engine (with its pipeline stages) and the facade from injected ports.
Provides a batteries-included in-memory environment — defaulting to the deterministic
rule-based brand strategist and null input ports — and helpers to build the engine over
any ports (e.g. the real Phase 7 / Phase 3 adapters).
"""

from __future__ import annotations

from dataclasses import dataclass

from brand.application.brand_engine import BrandEngine
from brand.application.ports.business_strategy_input import BusinessStrategyInputPort
from brand.application.ports.clock import Clock
from brand.application.ports.competitor_insight import CompetitorInsightPort
from brand.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from brand.application.ports.reasoning import ReasoningPort
from brand.application.ports.research_input import ResearchInputPort
from brand.application.ports.synthesis import BrandSynthesisPort
from brand.application.ports.unit_of_work import UnitOfWorkFactory
from brand.infrastructure.adapters.inmemory_inputs import (
    NullBusinessStrategyInput,
    NullCompetitorInsight,
    NullKnowledgeAdvisor,
    NullReasoning,
    NullResearchInput,
)
from brand.infrastructure.adapters.rule_based_brand_strategist import (
    RuleBasedBrandStrategist,
)
from brand.infrastructure.inmemory import (
    ReportStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from brand.interfaces.brand_facade import BrandFacade

__all__ = [
    "BrandEnvironment",
    "build_engine",
    "build_facade",
    "build_in_memory_environment",
]


def build_engine(
    *,
    business_strategy: BusinessStrategyInputPort,
    knowledge: KnowledgeAdvisorPort,
    research: ResearchInputPort,
    competitor: CompetitorInsightPort,
    reasoning: ReasoningPort,
    synthesis: BrandSynthesisPort,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
) -> BrandEngine:
    """Assemble a :class:`BrandEngine` from its ports."""
    return BrandEngine(
        business_strategy=business_strategy,
        knowledge=knowledge,
        research=research,
        competitor=competitor,
        reasoning=reasoning,
        synthesis=synthesis,
        unit_of_work_factory=unit_of_work_factory,
        clock=clock,
    )


def build_facade(engine: BrandEngine, uow_factory: UnitOfWorkFactory) -> BrandFacade:
    """Wrap an engine in its inbound facade."""
    return BrandFacade(engine, uow_factory)


@dataclass(frozen=True, slots=True)
class BrandEnvironment:
    """A fully wired engine plus a handle to its in-memory report store."""

    facade: BrandFacade
    engine: BrandEngine
    storage: ReportStorage
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
    *,
    business_strategy: BusinessStrategyInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    research: ResearchInputPort | None = None,
    competitor: CompetitorInsightPort | None = None,
    reasoning: ReasoningPort | None = None,
    synthesis: BrandSynthesisPort | None = None,
    clock: Clock | None = None,
) -> BrandEnvironment:
    """Stand up the whole engine over in-memory persistence.

    Unwired input ports default to null adapters (contributing no signals), and the
    strategist defaults to the deterministic rule-based implementation.
    """
    storage = ReportStorage()
    uow_factory = make_unit_of_work_factory(storage)
    engine = build_engine(
        business_strategy=business_strategy or NullBusinessStrategyInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        research=research or NullResearchInput(),
        competitor=competitor or NullCompetitorInsight(),
        reasoning=reasoning or NullReasoning(),
        synthesis=synthesis or RuleBasedBrandStrategist(),
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return BrandEnvironment(
        facade=facade,
        engine=engine,
        storage=storage,
        unit_of_work_factory=uow_factory,
    )
