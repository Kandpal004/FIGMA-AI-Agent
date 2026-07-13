"""Repository ports — the persistence interfaces the application depends on.

These Protocols express *what* the application needs from storage (load a
project, save a run, append a decision) without saying *how* it is stored. The
infrastructure layer supplies concrete implementations (Postgres); tests supply
in-memory fakes. Neither the application nor the domain ever imports a database
driver — dependency inversion in action (Clean Architecture).

All methods are asynchronous: persistence is I/O, and the whole engine runs on
asyncio. Loads for a missing entity raise :class:`~core.errors.NotFoundError`.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from director.domain.director.decision import DecisionRecord
from director.domain.project.entities import Project
from director.domain.shared.ids import ProjectId, RunId
from director.domain.workflow.run import WorkflowRun

__all__ = [
    "DecisionRepository",
    "ProjectRepository",
    "WorkflowRunRepository",
]


@runtime_checkable
class ProjectRepository(Protocol):
    """Loads and persists :class:`Project` aggregates (with their sections)."""

    async def get(self, project_id: ProjectId) -> Project:
        """Return the project.

        Raises:
            NotFoundError: If no project with that id exists.
        """
        ...

    async def add(self, project: Project) -> None:
        """Persist a new project."""
        ...

    async def save(self, project: Project) -> None:
        """Persist changes to an existing project."""
        ...


@runtime_checkable
class WorkflowRunRepository(Protocol):
    """Loads and persists :class:`WorkflowRun` aggregates.

    ``save`` is an upsert: it persists a run whether newly created or advanced.
    Persisting the full run on every transition is what makes runs resumable
    (Principle P3) — a reloaded run continues exactly where it left off.
    """

    async def get(self, run_id: RunId) -> WorkflowRun:
        """Return the run.

        Raises:
            NotFoundError: If no run with that id exists.
        """
        ...

    async def save(self, run: WorkflowRun) -> None:
        """Persist the run (insert or update)."""
        ...


@runtime_checkable
class DecisionRepository(Protocol):
    """Appends to and reads the Director's append-only reasoning log."""

    async def append(self, decision: DecisionRecord) -> None:
        """Append one decision. Records are never updated or deleted."""
        ...

    async def list_for_run(self, run_id: RunId) -> Sequence[DecisionRecord]:
        """Return all decisions for a run, in the order they were appended."""
        ...
