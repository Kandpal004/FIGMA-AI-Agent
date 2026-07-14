"""Composition root — where concrete adapters meet the IA application.

Assembles the engine (with its pipeline stages) and the facade from injected ports. Provides
a batteries-included in-memory environment — defaulting to the deterministic rule-based IA
architect and null input ports — and helpers to build the engine over any ports (e.g. the
real Phase 10 / 9 / 8 / 7 / 3 adapters).
"""

from __future__ import annotations

from dataclasses import dataclass

from ia.application.ia_engine import IAEngine
from ia.application.ports.brand_input import BrandInputPort
from ia.application.ports.business_strategy_input import BusinessStrategyInputPort
from ia.application.ports.clock import Clock
from ia.application.ports.competitor_insight import CompetitorInsightPort
from ia.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from ia.application.ports.psychology_input import PsychologyInputPort
from ia.application.ports.reasoning import ReasoningPort
from ia.application.ports.research_input import ResearchInputPort
from ia.application.ports.synthesis import IASynthesisPort
from ia.application.ports.unit_of_work import UnitOfWorkFactory
from ia.application.ports.ux_input import UXInputPort
from ia.infrastructure.adapters.inmemory_inputs import (
    NullBrandInput,
    NullBusinessStrategyInput,
    NullCompetitorInsight,
    NullKnowledgeAdvisor,
    NullPsychologyInput,
    NullReasoning,
    NullResearchInput,
    NullUXInput,
)
from ia.infrastructure.adapters.rule_based_ia_architect import RuleBasedIAArchitect
from ia.infrastructure.inmemory import (
    ReportStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from ia.interfaces.ia_facade import IAFacade

__all__ = ["IAEnvironment", "build_engine", "build_facade", "build_in_memory_environment"]


def build_engine(
    *,
    ux: UXInputPort,
    psychology: PsychologyInputPort,
    brand: BrandInputPort,
    business_strategy: BusinessStrategyInputPort,
    knowledge: KnowledgeAdvisorPort,
    research: ResearchInputPort,
    competitor: CompetitorInsightPort,
    reasoning: ReasoningPort,
    synthesis: IASynthesisPort,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
) -> IAEngine:
    """Assemble an :class:`IAEngine` from its ports."""
    return IAEngine(
        ux=ux, psychology=psychology, brand=brand, business_strategy=business_strategy,
        knowledge=knowledge, research=research, competitor=competitor, reasoning=reasoning,
        synthesis=synthesis, unit_of_work_factory=unit_of_work_factory, clock=clock,
    )


def build_facade(engine: IAEngine, uow_factory: UnitOfWorkFactory) -> IAFacade:
    """Wrap an engine in its inbound facade."""
    return IAFacade(engine, uow_factory)


@dataclass(frozen=True, slots=True)
class IAEnvironment:
    """A fully wired engine plus a handle to its in-memory report store."""

    facade: IAFacade
    engine: IAEngine
    storage: ReportStorage
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
    *,
    ux: UXInputPort | None = None,
    psychology: PsychologyInputPort | None = None,
    brand: BrandInputPort | None = None,
    business_strategy: BusinessStrategyInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    research: ResearchInputPort | None = None,
    competitor: CompetitorInsightPort | None = None,
    reasoning: ReasoningPort | None = None,
    synthesis: IASynthesisPort | None = None,
    clock: Clock | None = None,
) -> IAEnvironment:
    """Stand up the whole engine over in-memory persistence.

    Unwired input ports default to null adapters (contributing no signals), and the architect
    defaults to the deterministic rule-based implementation.
    """
    storage = ReportStorage()
    uow_factory = make_unit_of_work_factory(storage)
    engine = build_engine(
        ux=ux or NullUXInput(),
        psychology=psychology or NullPsychologyInput(),
        brand=brand or NullBrandInput(),
        business_strategy=business_strategy or NullBusinessStrategyInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        research=research or NullResearchInput(),
        competitor=competitor or NullCompetitorInsight(),
        reasoning=reasoning or NullReasoning(),
        synthesis=synthesis or RuleBasedIAArchitect(),
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return IAEnvironment(
        facade=facade, engine=engine, storage=storage, unit_of_work_factory=uow_factory
    )
