"""SQLAlchemy unit of work — one database transaction per Director checkpoint.

Binds the three repositories to a single :class:`AsyncSession`/transaction so a
step's writes (the advanced run and its decision records) commit atomically, as
:class:`~director.application.ports.unit_of_work.UnitOfWork` requires. A factory
built from an :class:`async_sessionmaker` opens a fresh unit — and thus a fresh
session and transaction — per ``async with``.
"""

from __future__ import annotations

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from director.infrastructure.persistence.repositories import (
    SqlAlchemyDecisionRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemyWorkflowRunRepository,
)

__all__ = ["SqlAlchemyUnitOfWork", "make_sqlalchemy_unit_of_work_factory"]


class SqlAlchemyUnitOfWork:
    """A transactional unit of work over a single async session."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        # Repository attributes are bound on __aenter__.
        self.projects: SqlAlchemyProjectRepository
        self.runs: SqlAlchemyWorkflowRunRepository
        self.decisions: SqlAlchemyDecisionRepository

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self.projects = SqlAlchemyProjectRepository(self._session)
        self.runs = SqlAlchemyWorkflowRunRepository(self._session)
        self.decisions = SqlAlchemyDecisionRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        assert self._session is not None
        try:
            if exc_type is not None:
                await self._session.rollback()
        finally:
            await self._session.close()
            self._session = None

    async def commit(self) -> None:
        assert self._session is not None
        await self._session.commit()

    async def rollback(self) -> None:
        assert self._session is not None
        await self._session.rollback()


def make_sqlalchemy_unit_of_work_factory(
    session_factory: async_sessionmaker[AsyncSession],
):
    """Return a zero-arg factory producing :class:`SqlAlchemyUnitOfWork` s."""

    def factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(session_factory)

    return factory
