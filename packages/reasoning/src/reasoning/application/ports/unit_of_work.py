"""Unit-of-Work port — the transactional boundary for persisting a strategy.

Producing and storing a strategy is a single logical operation; the Unit of Work
groups the strategy repository under one transaction. Reads use a plain repository;
writes go through here.
"""

from __future__ import annotations

from collections.abc import Callable
from types import TracebackType
from typing import Protocol, runtime_checkable

from reasoning.application.ports.strategy_repository import StrategyRepository

__all__ = ["UnitOfWork", "UnitOfWorkFactory"]


@runtime_checkable
class UnitOfWork(Protocol):
    """A transactional scope exposing the strategy repository."""

    strategies: StrategyRepository

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
