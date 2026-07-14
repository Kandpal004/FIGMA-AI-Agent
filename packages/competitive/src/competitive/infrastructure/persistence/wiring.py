"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory and the ports (a data source, a knowledge advisor,
an optional reasoning port, a clock), wires the SQLAlchemy unit of work into the
engine and facade. Kept apart from the in-memory container so in-memory usage need
not depend on SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from competitive.application.intelligence_engine import IntelligenceEngine
from competitive.application.ports.clock import Clock
from competitive.application.ports.data_source import CompetitorDataSourcePort
from competitive.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from competitive.application.ports.reasoning import ReasoningPort
from competitive.infrastructure.container import build_engine, build_facade
from competitive.infrastructure.inmemory import NullReasoningPort, SystemClock
from competitive.infrastructure.persistence.models import Base
from competitive.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from competitive.interfaces.intelligence_facade import IntelligenceFacade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine and its facade."""

    facade: IntelligenceFacade
    engine: IntelligenceEngine


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    data_source: CompetitorDataSourcePort,
    advisor: KnowledgeAdvisorPort,
    reasoning: ReasoningPort | None = None,
    clock: Clock | None = None,
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory and the given ports."""
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
    engine = build_engine(
        data_source=data_source,
        advisor=advisor,
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
        reasoning=reasoning or NullReasoningPort(),
    )
    facade = build_facade(engine, uow_factory)
    return SqlAlchemyEnvironment(facade=facade, engine=engine)


async def init_models(engine: AsyncEngine) -> None:
    """Create the competitive tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
