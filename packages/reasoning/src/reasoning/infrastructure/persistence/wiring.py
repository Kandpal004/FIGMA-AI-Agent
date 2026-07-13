"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory and the ports (a knowledge advisor, a context
port, a decision-history port, a clock), wires the SQLAlchemy unit of work into
the engine and facade. Kept apart from the in-memory container so in-memory usage
need not depend on SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from reasoning.application.ports.clock import Clock
from reasoning.application.ports.context_port import ContextPort
from reasoning.application.ports.decision_history_port import DecisionHistoryPort
from reasoning.application.ports.knowledge_advisor import KnowledgeAdvisorPort
from reasoning.application.reasoning_engine import ReasoningEngine
from reasoning.infrastructure.container import build_engine, build_facade
from reasoning.infrastructure.inmemory import SystemClock
from reasoning.infrastructure.persistence.models import Base
from reasoning.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from reasoning.interfaces.reasoning_facade import ReasoningFacade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine and its facade."""

    facade: ReasoningFacade
    engine: ReasoningEngine


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    advisor: KnowledgeAdvisorPort,
    context_port: ContextPort,
    decision_history_port: DecisionHistoryPort,
    clock: Clock | None = None,
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory and the given ports."""
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
    engine = build_engine(
        advisor=advisor,
        context_port=context_port,
        decision_history_port=decision_history_port,
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
    )
    facade = build_facade(engine, uow_factory)
    return SqlAlchemyEnvironment(facade=facade, engine=engine)


async def init_models(engine: AsyncEngine) -> None:
    """Create the reasoning tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
