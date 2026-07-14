"""Production wiring — assemble the engine over a SQLAlchemy database.

Given an async session factory, a source registry, and the ports (an optional
knowledge-link port, a clock), wires the SQLAlchemy unit of work into the engine and
facade. Kept apart from the in-memory container so in-memory usage need not depend on
SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from research.application.ports.clock import Clock
from research.application.ports.knowledge_link import KnowledgeLinkPort
from research.application.research_engine import ResearchEngine
from research.application.source_registry import SourceRegistry
from research.infrastructure.container import build_default_registry, build_engine, build_facade
from research.infrastructure.inmemory import SystemClock
from research.infrastructure.persistence.models import Base
from research.infrastructure.persistence.unit_of_work import (
    make_sqlalchemy_unit_of_work_factory,
)
from research.interfaces.research_facade import ResearchFacade

__all__ = ["SqlAlchemyEnvironment", "build_sqlalchemy_environment", "init_models"]


@dataclass(frozen=True, slots=True)
class SqlAlchemyEnvironment:
    """A database-backed engine and its facade."""

    facade: ResearchFacade
    engine: ResearchEngine
    registry: SourceRegistry


def build_sqlalchemy_environment(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    registry: SourceRegistry | None = None,
    knowledge_link: KnowledgeLinkPort | None = None,
    clock: Clock | None = None,
) -> SqlAlchemyEnvironment:
    """Wire the engine over a SQLAlchemy session factory and the given ports."""
    registry = registry or build_default_registry()
    uow_factory = make_sqlalchemy_unit_of_work_factory(session_factory)
    engine = build_engine(
        registry=registry,
        unit_of_work_factory=uow_factory,
        clock=clock or SystemClock(),
        knowledge_link=knowledge_link,
    )
    facade = build_facade(engine, uow_factory)
    return SqlAlchemyEnvironment(facade=facade, engine=engine, registry=registry)


async def init_models(engine: AsyncEngine) -> None:
    """Create the research tables from ORM metadata (local dev / tests)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
