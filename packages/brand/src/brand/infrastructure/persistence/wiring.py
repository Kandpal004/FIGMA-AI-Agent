"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory and the ports (the five signal ports, the strategist, a
clock), wires the SQLAlchemy unit of work into the engine and facade. Kept apart from
the in-memory container so in-memory usage need not depend on SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from brand.application.brand_engine import BrandEngine
from brand.application.ports.business_strategy_input import BusinessStrategyInputPort
from brand.application.ports.clock import Clock
from brand.application.ports.competitor_insight import CompetitorInsightPort
from brand.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from brand.application.ports.reasoning import ReasoningPort
from brand.application.ports.research_input import ResearchInputPort
from brand.application.ports.synthesis import BrandSynthesisPort
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
from brand.infrastructure.container import build_engine, build_facade
from brand.infrastructure.inmemory import SystemClock
from brand.infrastructure.persistence.models import Base
from brand.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from brand.interfaces.brand_facade import BrandFacade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine and its facade."""

    facade: BrandFacade
    engine: BrandEngine


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    business_strategy: BusinessStrategyInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    research: ResearchInputPort | None = None,
    competitor: CompetitorInsightPort | None = None,
    reasoning: ReasoningPort | None = None,
    synthesis: BrandSynthesisPort | None = None,
    clock: Clock | None = None,
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory and the given ports."""
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
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
    return SqlAlchemyEnvironment(facade=facade, engine=engine)


async def init_models(engine: AsyncEngine) -> None:
    """Create the brand tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
