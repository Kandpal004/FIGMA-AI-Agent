"""SQLAlchemy unit of work for knowledge writes.

Binds the repository to a single async session/transaction so an authoring
operation (e.g. activating a version and superseding the prior one) commits
atomically. A factory built from an :class:`async_sessionmaker` opens a fresh unit
per ``async with``.
"""

from __future__ import annotations

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from knowledge.infrastructure.persistence.repositories import (
    SqlAlchemyKnowledgeRepository,
)

__all__ = ["SqlAlchemyUnitOfWork", "make_sqlalchemy_unit_of_work_factory"]


class SqlAlchemyUnitOfWork:
    """A transactional unit of work over a single async session."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self.entries: SqlAlchemyKnowledgeRepository

    async def __aenter__(self) -> SqlAlchemyUnitOfWork:
        self._session = self._session_factory()
        self.entries = SqlAlchemyKnowledgeRepository(self._session)
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
