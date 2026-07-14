"""Composition root — where concrete adapters meet the design-language application.

Assembles the engine (with its pipeline stages) and the facade from injected ports. Provides a
batteries-included in-memory environment — defaulting to the deterministic rule-based designer
and null input ports — and helpers to build the engine over any ports (e.g. the real Phase
13 / 9 / 8 / 7 / 3 adapters).
"""

from __future__ import annotations

from dataclasses import dataclass

from design_language.application.design_language_engine import DesignLanguageEngine
from design_language.application.ports.brand_input import BrandInputPort
from design_language.application.ports.business_strategy_input import BusinessStrategyInputPort
from design_language.application.ports.clock import Clock
from design_language.application.ports.competitor_insight import CompetitorInsightPort
from design_language.application.ports.creative_director_input import CreativeDirectorInputPort
from design_language.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from design_language.application.ports.language_designer import LanguageDesignerPort
from design_language.application.ports.psychology_input import PsychologyInputPort
from design_language.application.ports.research_input import ResearchInputPort
from design_language.application.ports.unit_of_work import UnitOfWorkFactory
from design_language.infrastructure.adapters.inmemory_inputs import (
    NullBrandInput,
    NullBusinessStrategyInput,
    NullCompetitorInsight,
    NullCreativeDirectorInput,
    NullKnowledgeAdvisor,
    NullPsychologyInput,
    NullResearchInput,
)
from design_language.infrastructure.adapters.rule_based_language_designer import (
    RuleBasedLanguageDesigner,
)
from design_language.infrastructure.inmemory import (
    SpecificationStorage,
    SystemClock,
    make_unit_of_work_factory,
)
from design_language.interfaces.design_language_facade import DesignLanguageFacade

__all__ = [
    "DesignLanguageEnvironment",
    "build_engine",
    "build_facade",
    "build_in_memory_environment",
]


def build_engine(
    *,
    business_strategy: BusinessStrategyInputPort,
    brand: BrandInputPort,
    psychology: PsychologyInputPort,
    creative_director: CreativeDirectorInputPort,
    knowledge: KnowledgeAdvisorPort,
    research: ResearchInputPort,
    competitor: CompetitorInsightPort,
    designer: LanguageDesignerPort,
    unit_of_work_factory: UnitOfWorkFactory,
    clock: Clock,
) -> DesignLanguageEngine:
    """Assemble a :class:`DesignLanguageEngine` from its ports."""
    return DesignLanguageEngine(
        business_strategy=business_strategy, brand=brand, psychology=psychology,
        creative_director=creative_director, knowledge=knowledge, research=research,
        competitor=competitor, designer=designer, unit_of_work_factory=unit_of_work_factory,
        clock=clock,
    )


def build_facade(
    engine: DesignLanguageEngine, uow_factory: UnitOfWorkFactory
) -> DesignLanguageFacade:
    """Wrap an engine in its inbound facade."""
    return DesignLanguageFacade(engine, uow_factory)


@dataclass(frozen=True, slots=True)
class DesignLanguageEnvironment:
    """A fully wired engine plus a handle to its in-memory specification store."""

    facade: DesignLanguageFacade
    engine: DesignLanguageEngine
    storage: SpecificationStorage
    unit_of_work_factory: UnitOfWorkFactory


def build_in_memory_environment(
    *,
    business_strategy: BusinessStrategyInputPort | None = None,
    brand: BrandInputPort | None = None,
    psychology: PsychologyInputPort | None = None,
    creative_director: CreativeDirectorInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    research: ResearchInputPort | None = None,
    competitor: CompetitorInsightPort | None = None,
    designer: LanguageDesignerPort | None = None,
    clock: Clock | None = None,
) -> DesignLanguageEnvironment:
    """Stand up the whole engine over in-memory persistence.

    Unwired input ports default to null adapters (contributing no signals), and the designer
    defaults to the deterministic rule-based implementation.
    """
    storage = SpecificationStorage()
    uow_factory = make_unit_of_work_factory(storage)
    engine = build_engine(
        business_strategy=business_strategy or NullBusinessStrategyInput(),
        brand=brand or NullBrandInput(),
        psychology=psychology or NullPsychologyInput(),
        creative_director=creative_director or NullCreativeDirectorInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        research=research or NullResearchInput(),
        competitor=competitor or NullCompetitorInsight(),
        designer=designer or RuleBasedLanguageDesigner(),
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return DesignLanguageEnvironment(
        facade=facade, engine=engine, storage=storage, unit_of_work_factory=uow_factory
    )
