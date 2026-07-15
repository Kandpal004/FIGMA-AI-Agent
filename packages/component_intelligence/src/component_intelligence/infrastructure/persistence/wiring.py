"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory and the ports (the eleven signal ports, the brain, a clock),
wires the SQLAlchemy unit of work into the engine and facade. Kept apart from the in-memory
container so in-memory usage need not depend on SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

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
from component_intelligence.infrastructure.container import build_engine, build_facade
from component_intelligence.infrastructure.inmemory import SystemClock
from component_intelligence.infrastructure.persistence.models import Base
from component_intelligence.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from component_intelligence.interfaces.component_intelligence_facade import (
    ComponentIntelligenceFacade,
)

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine and its facade."""

    facade: ComponentIntelligenceFacade
    engine: ComponentIntelligenceEngine


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
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
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory and the given ports."""
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
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
    return SqlAlchemyEnvironment(facade=facade, engine=engine)


async def init_models(engine: AsyncEngine) -> None:
    """Create the component-intelligence tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
