"""The Unit of Work port — the transaction boundary.

A unit of work exposes the specification repository bound to a single transaction, opened per
``async with``. The infrastructure layer supplies concrete implementations (in-memory and
SQLAlchemy); the engine and facade depend only on this protocol.
"""

from __future__ import annotations

from types import TracebackType
from typing import Protocol, runtime_checkable

from component_intelligence.application.ports.specification_repository import (
    ComponentSpecificationRepository,
)

__all__ = ["UnitOfWork", "UnitOfWorkFactory"]


@runtime_checkable
class UnitOfWork(Protocol):
    """A transactional scope exposing the specification repository."""

    specifications: ComponentSpecificationRepository

    async def __aenter__(self) -> UnitOfWork: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


@runtime_checkable
class UnitOfWorkFactory(Protocol):
    """A zero-argument callable that opens a fresh :class:`UnitOfWork`."""

    def __call__(self) -> UnitOfWork: ...
