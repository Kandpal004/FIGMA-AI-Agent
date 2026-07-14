"""Composition root — where concrete adapters meet the wireframe application.

Assembles the engine (with its pipeline stages) and the facade from injected ports. Provides
a batteries-included in-memory environment — defaulting to the deterministic rule-based
planner and null input ports — and helpers to build the engine over any ports (e.g. the real
Phase 11 / 10 / 9 / 8 / 7 / 3 adapters).
"""

from __future__ import annotations

from dataclasses import dataclass

from wireframe.application.ports.brand_input import BrandInputPort
from wireframe.application.ports.business_strategy_input import BusinessStrategyInputPort
from wireframe.application.ports.clock import Clock
from wireframe.application.ports.competitor_insight import CompetitorInsightPort
from wireframe.application.ports.ia_input import IAInputPort
from wireframe.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from wireframe.application.ports.psychology_input import PsychologyInputPort
from wireframe.application.ports.reasoning import ReasoningPort
from wireframe.application.ports.research_input import ResearchInputPort
from wireframe.application.ports.synthesis import WireframeSynthesisPort
from wireframe.application.ports.unit_of_work import UnitOfWorkFactory
from wireframe.application.ports.ux_input import UXInputPort
from wireframe.application.wireframe_engine import WireframeEngine
from wireframe.infrastructure.adapters.inmemory_inputs import (
    NullBrandInput,
    NullBusinessStrategyInput,
    NullCompetitorInsight,
    NullIAInput,
    NullKnowledgeAdvisor,
    NullPsychologyInput,
    NullReasoning,
    NullResearchInput,
    NullUXInput,
)
from wireframe.infrastructure.adapters.rule_based_wireframe_planner import (
    RuleBasedWireframePlanner,
)
from wireframe.infrastructure.inmemory import (
    PlanStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from wireframe.interfaces.wireframe_facade import WireframeFacade

__all__ = [
    "WireframeEnvironment",
    "build_engine",
    "build_facade",
    "build_in_memory_environment",
]


def build_engine(
    *,
    ia: IAInputPort,
    ux: UXInputPort,
    business_strategy: BusinessStrategyInputPort,
    brand: BrandInputPort,
    psychology: PsychologyInputPort,
    knowledge: KnowledgeAdvisorPort,
    research: ResearchInputPort,
    competitor: CompetitorInsightPort,
    reasoning: ReasoningPort,
    synthesis: WireframeSynthesisPort,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
) -> WireframeEngine:
    """Assemble a :class:`WireframeEngine` from its ports."""
    return WireframeEngine(
        ia=ia, ux=ux, business_strategy=business_strategy, brand=brand, psychology=psychology,
        knowledge=knowledge, research=research, competitor=competitor, reasoning=reasoning,
        synthesis=synthesis, unit_of_work_factory=unit_of_work_factory, clock=clock,
    )


def build_facade(engine: WireframeEngine, uow_factory: UnitOfWorkFactory) -> WireframeFacade:
    """Wrap an engine in its inbound facade."""
    return WireframeFacade(engine, uow_factory)


@dataclass(frozen=True, slots=True)
class WireframeEnvironment:
    """A fully wired engine plus a handle to its in-memory plan store."""

    facade: WireframeFacade
    engine: WireframeEngine
    storage: PlanStorage
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
    *,
    ia: IAInputPort | None = None,
    ux: UXInputPort | None = None,
    business_strategy: BusinessStrategyInputPort | None = None,
    brand: BrandInputPort | None = None,
    psychology: PsychologyInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    research: ResearchInputPort | None = None,
    competitor: CompetitorInsightPort | None = None,
    reasoning: ReasoningPort | None = None,
    synthesis: WireframeSynthesisPort | None = None,
    clock: Clock | None = None,
) -> WireframeEnvironment:
    """Stand up the whole engine over in-memory persistence.

    Unwired input ports default to null adapters (contributing no signals), and the planner
    defaults to the deterministic rule-based implementation.
    """
    storage = PlanStorage()
    uow_factory = make_unit_of_work_factory(storage)
    engine = build_engine(
        ia=ia or NullIAInput(),
        ux=ux or NullUXInput(),
        business_strategy=business_strategy or NullBusinessStrategyInput(),
        brand=brand or NullBrandInput(),
        psychology=psychology or NullPsychologyInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        research=research or NullResearchInput(),
        competitor=competitor or NullCompetitorInsight(),
        reasoning=reasoning or NullReasoning(),
        synthesis=synthesis or RuleBasedWireframePlanner(),
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return WireframeEnvironment(
        facade=facade, engine=engine, storage=storage, unit_of_work_factory=uow_factory
    )
