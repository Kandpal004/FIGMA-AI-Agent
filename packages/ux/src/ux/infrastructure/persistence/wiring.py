"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory and the ports (the seven signal ports, the strategist, a
clock), wires the SQLAlchemy unit of work into the engine and facade. Kept apart from the
in-memory container so in-memory usage need not depend on SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from ux.application.ports.brand_input import BrandInputPort
from ux.application.ports.business_strategy_input import BusinessStrategyInputPort
from ux.application.ports.clock import Clock
from ux.application.ports.competitor_insight import CompetitorInsightPort
from ux.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from ux.application.ports.psychology_input import PsychologyInputPort
from ux.application.ports.reasoning import ReasoningPort
from ux.application.ports.research_input import ResearchInputPort
from ux.application.ports.synthesis import UXSynthesisPort
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
from ux.infrastructure.container import build_engine, build_facade
from ux.infrastructure.inmemory import SystemClock
from ux.infrastructure.persistence.models import Base
from ux.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from ux.interfaces.ux_facade import UXFacade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine and its facade."""

    facade: UXFacade
    engine: UXEngine


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
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
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory and the given ports."""
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
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
    return SqlAlchemyEnvironment(facade=facade, engine=engine)


async def init_models(engine: AsyncEngine) -> None:
    """Create the UX tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
