"""Composition root — where concrete adapters meet the component-intelligence application.

Assembles the engine (with its pipeline stages) and the facade from injected ports. Provides a
batteries-included in-memory environment — defaulting to the deterministic rule-based brain and
null input ports — and helpers to build the engine over any ports (e.g. the real Phase
14 / 13 / 12 / 11 / 10 / 9 / 8 / 7 / 3 adapters).
"""

from __future__ import annotations

from dataclasses import dataclass

from component_intelligence.application.component_intelligence_engine import (
    ComponentIntelligenceEngine,
)
from component_intelligence.application.ports.brand_input import BrandInputPort
from component_intelligence.application.ports.business_strategy_input import BusinessStrategyInputPort
from component_intelligence.application.ports.clock import Clock
from component_intelligence.application.ports.competitor_insight import CompetitorInsightPort
from component_intelligence.application.ports.component_intelligence import ComponentIntelligencePort
from component_intelligence.application.ports.creative_director_input import CreativeDirectorInputPort
from component_intelligence.application.ports.design_language_input import DesignLanguageInputPort
from component_intelligence.application.ports.ia_input import IAInputPort
from component_intelligence.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from component_intelligence.application.ports.psychology_input import PsychologyInputPort
from component_intelligence.application.ports.research_input import ResearchInputPort
from component_intelligence.application.ports.unit_of_work import UnitOfWorkFactory
from component_intelligence.application.ports.ux_input import UXInputPort
from component_intelligence.application.ports.wireframe_input import WireframeInputPort
from component_intelligence.infrastructure.adapters.inmemory_inputs import (
    NullBrandInput,
    NullBusinessStrategyInput,
    NullCompetitorInsight,
    NullCreativeDirectorInput,
    NullDesignLanguageInput,
    NullIAInput,
    NullKnowledgeAdvisor,
    NullPsychologyInput,
    NullResearchInput,
    NullUXInput,
    NullWireframeInput,
)
from component_intelligence.infrastructure.adapters.rule_based_component_intelligence import (
    RuleBasedComponentIntelligence,
)
from component_intelligence.infrastructure.inmemory import (
    SpecificationStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from component_intelligence.interfaces.component_intelligence_facade import (
    ComponentIntelligenceFacade,
)

__all__ = [
    "ComponentIntelligenceEnvironment",
    "build_engine",
    "build_facade",
    "build_in_memory_environment",
]


def build_engine(
    *,
    business_strategy: BusinessStrategyInputPort,
    brand: BrandInputPort,
    psychology: PsychologyInputPort,
    ux: UXInputPort,
    ia: IAInputPort,
    wireframe: WireframeInputPort,
    creative_director: CreativeDirectorInputPort,
    design_language: DesignLanguageInputPort,
    knowledge: KnowledgeAdvisorPort,
    research: ResearchInputPort,
    competitor: CompetitorInsightPort,
    brain: ComponentIntelligencePort,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
) -> ComponentIntelligenceEngine:
    """Assemble a :class:`ComponentIntelligenceEngine` from its ports."""
    return ComponentIntelligenceEngine(
        business_strategy=business_strategy, brand=brand, psychology=psychology, ux=ux, ia=ia,
        wireframe=wireframe, creative_director=creative_director, design_language=design_language,
        knowledge=knowledge, research=research, competitor=competitor, brain=brain,
        unit_of_work_factory=unit_of_work_factory, clock=clock,
    )


def build_facade(
    engine: ComponentIntelligenceEngine, uow_factory: UnitOfWorkFactory
) -> ComponentIntelligenceFacade:
    """Wrap an engine in its inbound facade."""
    return ComponentIntelligenceFacade(engine, uow_factory)


@dataclass(frozen=True, slots=True)
class ComponentIntelligenceEnvironment:
    """A fully wired engine plus a handle to its in-memory specification store."""

    facade: ComponentIntelligenceFacade
    engine: ComponentIntelligenceEngine
    storage: SpecificationStorage
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
    *,
    business_strategy: BusinessStrategyInputPort | None = None,
    brand: BrandInputPort | None = None,
    psychology: PsychologyInputPort | None = None,
    ux: UXInputPort | None = None,
    ia: IAInputPort | None = None,
    wireframe: WireframeInputPort | None = None,
    creative_director: CreativeDirectorInputPort | None = None,
    design_language: DesignLanguageInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    research: ResearchInputPort | None = None,
    competitor: CompetitorInsightPort | None = None,
    brain: ComponentIntelligencePort | None = None,
    clock: Clock | None = None,
) -> ComponentIntelligenceEnvironment:
    """Stand up the whole engine over in-memory persistence.

    Unwired input ports default to null adapters (contributing no signals), and the brain
    defaults to the deterministic rule-based implementation.
    """
    storage = SpecificationStorage()
    uow_factory = make_unit_of_work_factory(storage)
    engine = build_engine(
        business_strategy=business_strategy or NullBusinessStrategyInput(),
        brand=brand or NullBrandInput(),
        psychology=psychology or NullPsychologyInput(),
        ux=ux or NullUXInput(),
        ia=ia or NullIAInput(),
        wireframe=wireframe or NullWireframeInput(),
        creative_director=creative_director or NullCreativeDirectorInput(),
        design_language=design_language or NullDesignLanguageInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        research=research or NullResearchInput(),
        competitor=competitor or NullCompetitorInsight(),
        brain=brain or RuleBasedComponentIntelligence(),
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return ComponentIntelligenceEnvironment(
        facade=facade, engine=engine, storage=storage, unit_of_work_factory=uow_factory
    )
