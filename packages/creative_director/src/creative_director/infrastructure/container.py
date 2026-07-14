"""Composition root — where concrete adapters meet the Creative Director application.

Assembles the engine (with its pipeline stages) and the facade from injected ports. Provides
a batteries-included in-memory environment — defaulting to the deterministic rule-based panel
and null input ports — and helpers to build the engine over any ports (e.g. the real Phase
12 / 11 / 10 / 9 / 8 / 7 / 3 adapters).
"""

from __future__ import annotations

from dataclasses import dataclass

from creative_director.application.creative_director_engine import CreativeDirectorEngine
from creative_director.application.ports.brand_input import BrandInputPort
from creative_director.application.ports.business_strategy_input import BusinessStrategyInputPort
from creative_director.application.ports.clock import Clock
from creative_director.application.ports.competitor_insight import CompetitorInsightPort
from creative_director.application.ports.ia_input import IAInputPort
from creative_director.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from creative_director.application.ports.psychology_input import PsychologyInputPort
from creative_director.application.ports.reasoning import ReasoningPort
from creative_director.application.ports.research_input import ResearchInputPort
from creative_director.application.ports.review_panel import ReviewPanelPort
from creative_director.application.ports.unit_of_work import UnitOfWorkFactory
from creative_director.application.ports.ux_input import UXInputPort
from creative_director.application.ports.wireframe_input import WireframeInputPort
from creative_director.infrastructure.adapters.inmemory_inputs import (
    NullBrandInput,
    NullBusinessStrategyInput,
    NullCompetitorInsight,
    NullIAInput,
    NullKnowledgeAdvisor,
    NullPsychologyInput,
    NullReasoning,
    NullResearchInput,
    NullUXInput,
    NullWireframeInput,
)
from creative_director.infrastructure.adapters.rule_based_review_panel import (
    RuleBasedReviewPanel,
)
from creative_director.infrastructure.inmemory import (
    ReviewStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from creative_director.interfaces.creative_director_facade import CreativeDirectorFacade

__all__ = [
    "CreativeDirectorEnvironment",
    "build_engine",
    "build_facade",
    "build_in_memory_environment",
]


def build_engine(
    *,
    wireframe: WireframeInputPort,
    ia: IAInputPort,
    ux: UXInputPort,
    business_strategy: BusinessStrategyInputPort,
    brand: BrandInputPort,
    psychology: PsychologyInputPort,
    knowledge: KnowledgeAdvisorPort,
    research: ResearchInputPort,
    competitor: CompetitorInsightPort,
    reasoning: ReasoningPort,
    panel: ReviewPanelPort,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
) -> CreativeDirectorEngine:
    """Assemble a :class:`CreativeDirectorEngine` from its ports."""
    return CreativeDirectorEngine(
        wireframe=wireframe, ia=ia, ux=ux, business_strategy=business_strategy, brand=brand,
        psychology=psychology, knowledge=knowledge, research=research, competitor=competitor,
        reasoning=reasoning, panel=panel, unit_of_work_factory=unit_of_work_factory, clock=clock,
    )


def build_facade(
    engine: CreativeDirectorEngine, uow_factory: UnitOfWorkFactory, clock: Clock
) -> CreativeDirectorFacade:
    """Wrap an engine in its inbound facade."""
    return CreativeDirectorFacade(engine, uow_factory, clock)


@dataclass(frozen=True, slots=True)
class CreativeDirectorEnvironment:
    """A fully wired engine plus a handle to its in-memory review store."""

    facade: CreativeDirectorFacade
    engine: CreativeDirectorEngine
    storage: ReviewStorage
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
    *,
    wireframe: WireframeInputPort | None = None,
    ia: IAInputPort | None = None,
    ux: UXInputPort | None = None,
    business_strategy: BusinessStrategyInputPort | None = None,
    brand: BrandInputPort | None = None,
    psychology: PsychologyInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    research: ResearchInputPort | None = None,
    competitor: CompetitorInsightPort | None = None,
    reasoning: ReasoningPort | None = None,
    panel: ReviewPanelPort | None = None,
    clock: Clock | None = None,
) -> CreativeDirectorEnvironment:
    """Stand up the whole engine over in-memory persistence.

    Unwired input ports default to null adapters (contributing no signals), and the panel
    defaults to the deterministic rule-based implementation.
    """
    storage = ReviewStorage()
    uow_factory = make_unit_of_work_factory(storage)
    the_clock = clock or SystemClock()
    engine = build_engine(
        wireframe=wireframe or NullWireframeInput(),
        ia=ia or NullIAInput(),
        ux=ux or NullUXInput(),
        business_strategy=business_strategy or NullBusinessStrategyInput(),
        brand=brand or NullBrandInput(),
        psychology=psychology or NullPsychologyInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        research=research or NullResearchInput(),
        competitor=competitor or NullCompetitorInsight(),
        reasoning=reasoning or NullReasoning(),
        panel=panel or RuleBasedReviewPanel(),
        unit_of_work_factory=uow_factory,
        clock=the_clock,
    )
    facade = build_facade(engine, uow_factory, the_clock)
    return CreativeDirectorEnvironment(
        facade=facade, engine=engine, storage=storage, unit_of_work_factory=uow_factory
    )
