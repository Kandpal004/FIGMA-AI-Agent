"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory and the ports (the seven signal ports, the designer, a clock),
wires the SQLAlchemy unit of work into the engine and facade. Kept apart from the in-memory
container so in-memory usage need not depend on SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

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
from design_language.infrastructure.container import build_engine, build_facade
from design_language.infrastructure.inmemory import SystemClock
from design_language.infrastructure.persistence.models import Base
from design_language.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from design_language.interfaces.design_language_facade import DesignLanguageFacade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine and its facade."""

    facade: DesignLanguageFacade
    engine: DesignLanguageEngine


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
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
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory and the given ports."""
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
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
    return SqlAlchemyEnvironment(facade=facade, engine=engine)


async def init_models(engine: AsyncEngine) -> None:
    """Create the design-language tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
