"""Unit-of-Work port — the transactional boundary for persisting a report."""

from __future__ import annotations

from collections.abc import Callable
from types import TracebackType
from typing import Protocol, runtime_checkable

from competitive.application.ports.report_repository import ReportRepository

__all__ = ["UnitOfWork", "UnitOfWorkFactory"]


@runtime_checkable
class UnitOfWork(Protocol):
    """A transactional scope exposing the report repository."""

    reports: ReportRepository

    async def __aenter__(self) -> UnitOfWork: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None:
        """Make all writes in this unit durable."""
        ...

    async def rollback(self) -> None:
        """Discard all writes in this unit."""
        ...


#: A zero-argument callable that opens a fresh :class:`UnitOfWork`.
UnitOfWorkFactory = Callable[[], UnitOfWork]
