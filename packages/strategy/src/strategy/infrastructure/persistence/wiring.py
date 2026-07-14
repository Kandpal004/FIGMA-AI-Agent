"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory and the ports (the four evidence ports, the strategist,
a clock), wires the SQLAlchemy unit of work into the engine and facade. Kept apart from
the in-memory container so in-memory usage need not depend on SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from strategy.application.ports.clock import Clock
from strategy.application.ports.competitor_insight import CompetitorInsightPort
from strategy.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from strategy.application.ports.reasoning import ReasoningPort
from strategy.application.ports.research_input import ResearchInputPort
from strategy.application.ports.synthesis import StrategySynthesisPort
from strategy.application.strategy_engine import StrategyEngine
from strategy.infrastructure.adapters.inmemory_inputs import (
    NullCompetitorInsight,
    NullKnowledgeAdvisor,
    NullReasoning,
    NullResearchInput,
)
from strategy.infrastructure.adapters.rule_based_strategist import RuleBasedStrategist
from strategy.infrastructure.container import build_engine, build_facade
from strategy.infrastructure.inmemory import SystemClock
from strategy.infrastructure.persistence.models import Base
from strategy.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from strategy.interfaces.strategy_facade import StrategyFacade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine and its facade."""

    facade: StrategyFacade
    engine: StrategyEngine


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    research: ResearchInputPort | None = None,
    knowledge: KnowledgeAdvisorPort | None = None,
    competitor: CompetitorInsightPort | None = None,
    reasoning: ReasoningPort | None = None,
    synthesis: StrategySynthesisPort | None = None,
    clock: Clock | None = None,
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory and the given ports."""
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
    engine = build_engine(
        research=research or NullResearchInput(),
        knowledge=knowledge or NullKnowledgeAdvisor(),
        competitor=competitor or NullCompetitorInsight(),
        reasoning=reasoning or NullReasoning(),
        synthesis=synthesis or RuleBasedStrategist(),
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return SqlAlchemyEnvironment(facade=facade, engine=engine)


async def init_models(engine: AsyncEngine) -> None:
    """Create the strategy tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
