"""Async database engine and session management.

Exposes a lazily-constructed engine + session factory (so importing this module
does not require a live database) and a :func:`session_scope` context manager
that commits on success and rolls back on error. FastAPI request handlers get
sessions via the dependency in :mod:`api.deps`, which builds on this.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from core.config import Settings, get_settings
from core.logging import get_logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

log = get_logger(__name__)

# Module-level singletons, built on first use.
_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """Return the process-wide async engine, creating it on first call."""
    global _engine
    if _engine is None:
        settings = settings or get_settings()
        _engine = create_async_engine(
            settings.postgres_dsn,
            echo=settings.sql_echo,
            pool_size=settings.postgres_pool_size,
            max_overflow=settings.postgres_max_overflow,
            pool_pre_ping=True,
            future=True,
        )
        log.info("database engine created", extra={"echo": settings.sql_echo})
    return _engine


def get_sessionmaker(
    settings: Settings | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Return the process-wide session factory."""
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(settings),
            expire_on_commit=False,
            autoflush=False,
        )
    return _sessionmaker


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Provide a transactional session scope.

    Commits if the block succeeds, rolls back on any exception, and always
    closes the session::

        async with session_scope() as session:
            session.add(obj)
    """
    session = get_sessionmaker()()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def ping() -> bool:
    """Lightweight connectivity check for the health endpoint."""
    from sqlalchemy import text

    async with get_engine().connect() as conn:
        await conn.execute(text("SELECT 1"))
    return True


async def init_models() -> None:
    """Create all tables from the ORM metadata (local dev / tests only).

    Production uses Alembic migrations; this is a convenience for bringing up a
    fresh local database without a migration step.
    """
    from api.db.models import Base

    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("database schema ensured")


async def dispose() -> None:
    """Dispose of the engine's connection pool on shutdown."""
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _sessionmaker = None
