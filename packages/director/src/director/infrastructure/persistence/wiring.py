"""Production wiring — assemble the engine over a SQLAlchemy database.

This is the composition root for the database-backed deployment: given an async
session factory (built from a real engine by the API app or worker), it wires the
SQLAlchemy unit of work and the Postgres memory store into a
:class:`DirectorService` and :class:`DirectorFacade`. It lives apart from the
in-memory container so that code using the in-memory engine need not depend on
SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from director.application.director.director_service import (
    DEFAULT_MAX_REDESIGNS,
    DirectorService,
)
from director.application.ports.agent_executor_port import AgentExecutorPort
from director.application.ports.clock import Clock
from director.domain.workflow.catalog import WorkflowCatalog
from director.infrastructure.container import build_director
from director.infrastructure.inmemory import SystemClock
from director.infrastructure.memory.postgres_store import PostgresMemoryStore
from director.infrastructure.persistence.models import Base
from director.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from director.interfaces.director_facade import DirectorFacade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine: the facade and the Director it fronts."""

    facade: DirectorFacade
    director: DirectorService


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    agent_executor: AgentExecutorPort,
    catalog: WorkflowCatalog | None = None,
    clock: Clock | None = None,
    max_redesigns: int = DEFAULT_MAX_REDESIGNS,
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory."""
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
    memory_store = PostgresMemoryStore(session_factory)
    director = build_director(
        catalog=catalog or WorkflowCatalog.default(),
        agent_executor=agent_executor,
        unit_of_work_factory=uow_factory,
        memory_store=memory_store,
        clock=clock or SystemClock(),
        max_redesigns=max_redesigns,
    )
    facade = DirectorFacade(director, uow_factory)
    return SqlAlchemyEnvironment(facade=facade, director=director)


async def init_models(engine: AsyncEngine) -> None:
    """Create the Director's tables from ORM metadata (local dev / tests).

    Production uses Alembic migrations; this is a convenience for a fresh
    database.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
