"""Unit-of-Work port — the transactional boundary for a single Director step.

Each iteration of the Director's loop mutates several aggregates (the run, the
decision log, sometimes memory) and those changes must land **atomically**: a
run must never be observed as advanced while its decision record is missing. The
Unit of Work groups the repositories under one transaction so a step's writes
commit together or not at all.

The application depends only on this Protocol; the infrastructure layer binds it
to a real database transaction, and tests bind it to an in-memory fake. A
:data:`UnitOfWorkFactory` produces a fresh unit per transaction::

    async with uow_factory() as uow:
        await uow.runs.save(run)
        await uow.decisions.append(decision)
        await uow.commit()

Leaving the ``async with`` block without calling :meth:`commit` rolls back.
"""

from __future__ import annotations

from collections.abc import Callable
from types import TracebackType
from typing import Protocol, runtime_checkable

from director.application.ports.repositories import (
    DecisionRepository,
    ProjectRepository,
    WorkflowRunRepository,
)

__all__ = ["UnitOfWork", "UnitOfWorkFactory"]


@runtime_checkable
class UnitOfWork(Protocol):
    """A transactional scope exposing the repositories.

    Implementations are async context managers. The repositories they expose
    share one transaction; :meth:`commit` makes the writes durable and
    :meth:`rollback` (also performed automatically if the block exits without a
    commit) discards them.
    """

    projects: ProjectRepository
    runs: WorkflowRunRepository
    decisions: DecisionRepository

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
