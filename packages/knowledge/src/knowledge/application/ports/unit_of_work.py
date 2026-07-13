"""Unit-of-Work port — the transactional boundary for knowledge writes.

Authoring operations (activating a version and superseding the prior one, for
example) mutate more than one entry and must land atomically. The Unit of Work
groups the repository under one transaction so those writes commit together or
not at all. Reads do not need it — the query service and reasoner take a plain
repository — but writes go through here.
"""

from __future__ import annotations

from collections.abc import Callable
from types import TracebackType
from typing import Protocol, runtime_checkable

from knowledge.application.ports.repository import KnowledgeRepository

__all__ = ["UnitOfWork", "UnitOfWorkFactory"]


@runtime_checkable
class UnitOfWork(Protocol):
    """A transactional scope exposing the knowledge repository."""

    entries: KnowledgeRepository

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
