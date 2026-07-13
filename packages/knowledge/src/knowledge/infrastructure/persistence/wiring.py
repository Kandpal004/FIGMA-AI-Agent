"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory (built from a real engine by the API app or a
seeding tool), wires the SQLAlchemy unit of work and repository into the facade.
Kept apart from the in-memory container so in-memory usage need not depend on
SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from knowledge.application.ports.clock import Clock
from knowledge.application.ports.search_port import KnowledgeSearchPort
from knowledge.infrastructure.inmemory import SystemClock
from knowledge.infrastructure.persistence.models import Base
from knowledge.infrastructure.persistence.repositories import (
    SqlAlchemySessionScopedRepository,
)
from knowledge.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from knowledge.interfaces.knowledge_facade import KnowledgeFacade

# Reuse the shared assembly logic so wiring is identical to the in-memory root.
from knowledge.infrastructure.container import build_facade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine: the facade over a SQLAlchemy session factory."""

    facade: KnowledgeFacade


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    clock: Clock | None = None,
    search: KnowledgeSearchPort | None = None,
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory.

    Reads (query/reasoner) run on a short session scoped to each call; writes go
    through the transactional unit of work.
    """
    repository = SqlAlchemySessionScopedRepository(session_factory)
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
    facade = build_facade(
        repository=repository,
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
        search=search,
    )
    return SqlAlchemyEnvironment(facade=facade)


async def init_models(engine: AsyncEngine) -> None:
    """Create the knowledge tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
