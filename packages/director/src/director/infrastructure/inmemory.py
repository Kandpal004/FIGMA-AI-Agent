"""In-memory infrastructure adapters.

Concrete, dependency-free implementations of every application port, backed by
plain dictionaries. Their purpose is twofold:

* they make the entire Director Engine **runnable and testable end-to-end with no
  external services** — no Postgres, no Qdrant, no network; and
* they document, in the simplest possible form, exactly what each port's
  contract requires — a reference the database-backed adapters are checked against.

Everything here honours the port semantics faithfully (e.g. loads of a missing
entity raise :class:`~core.errors.NotFoundError`; the memory store respects scope
coverage), so code that works against these adapters works against the real ones.

These are infrastructure: the application and domain never import this module;
only the composition root (or a test) wires it in.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from types import TracebackType

from core.errors import NotFoundError

from director.application.ports.clock import Clock
from director.domain.director.decision import DecisionRecord
from director.domain.memory.entities import MemoryKind, MemoryRecord, MemoryScope
from director.domain.project.entities import Project
from director.domain.shared.ids import ProjectId, RunId
from director.domain.workflow.run import WorkflowRun

__all__ = [
    "InMemoryDecisionRepository",
    "InMemoryMemoryStore",
    "InMemoryProjectRepository",
    "InMemoryStorage",
    "InMemoryUnitOfWork",
    "InMemoryWorkflowRunRepository",
    "SystemClock",
    "make_unit_of_work_factory",
]


class SystemClock(Clock):
    """A real clock returning the current UTC time."""

    def now(self) -> datetime:
        return datetime.now(UTC)


# --------------------------------------------------------------------------- #
# Backing storage shared across units of work
# --------------------------------------------------------------------------- #
class InMemoryStorage:
    """Process-lifetime storage shared by all in-memory repositories.

    A single instance holds the projects, runs, and decision log; every
    :class:`InMemoryUnitOfWork` reads and writes the same instance, so committed
    writes persist across transactions exactly as a database would.
    """

    def __init__(self) -> None:
        self.projects: dict[ProjectId, Project] = {}
        self.runs: dict[RunId, WorkflowRun] = {}
        self.decisions: dict[RunId, list[DecisionRecord]] = {}


# --------------------------------------------------------------------------- #
# Repositories
# --------------------------------------------------------------------------- #
class InMemoryProjectRepository:
    """Dict-backed :class:`ProjectRepository`."""

    def __init__(self, storage: InMemoryStorage) -> None:
        self._storage = storage

    async def get(self, project_id: ProjectId) -> Project:
        project = self._storage.projects.get(project_id)
        if project is None:
            raise NotFoundError(
                f"Project {project_id} not found.", details={"project_id": str(project_id)}
            )
        return project

    async def add(self, project: Project) -> None:
        self._storage.projects[project.id] = project

    async def save(self, project: Project) -> None:
        self._storage.projects[project.id] = project


class InMemoryWorkflowRunRepository:
    """Dict-backed :class:`WorkflowRunRepository`."""

    def __init__(self, storage: InMemoryStorage) -> None:
        self._storage = storage

    async def get(self, run_id: RunId) -> WorkflowRun:
        run = self._storage.runs.get(run_id)
        if run is None:
            raise NotFoundError(f"Run {run_id} not found.", details={"run_id": str(run_id)})
        return run

    async def save(self, run: WorkflowRun) -> None:
        self._storage.runs[run.id] = run


class InMemoryDecisionRepository:
    """Dict-backed append-only :class:`DecisionRepository`."""

    def __init__(self, storage: InMemoryStorage) -> None:
        self._storage = storage

    async def append(self, decision: DecisionRecord) -> None:
        self._storage.decisions.setdefault(decision.run_id, []).append(decision)

    async def list_for_run(self, run_id: RunId) -> Sequence[DecisionRecord]:
        return list(self._storage.decisions.get(run_id, []))


# --------------------------------------------------------------------------- #
# Unit of Work
# --------------------------------------------------------------------------- #
class InMemoryUnitOfWork:
    """A trivial unit of work over shared in-memory storage.

    Writes take effect immediately against the shared storage; :meth:`commit` and
    :meth:`rollback` are no-ops (there is no transaction to defer). This is
    sufficient for local running and tests; the database-backed unit of work
    provides true transactional semantics.
    """

    def __init__(self, storage: InMemoryStorage) -> None:
        self.projects = InMemoryProjectRepository(storage)
        self.runs = InMemoryWorkflowRunRepository(storage)
        self.decisions = InMemoryDecisionRepository(storage)

    async def __aenter__(self) -> InMemoryUnitOfWork:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


def make_unit_of_work_factory(storage: InMemoryStorage):
    """Return a zero-arg factory that opens units of work over ``storage``."""

    def factory() -> InMemoryUnitOfWork:
        return InMemoryUnitOfWork(storage)

    return factory


# --------------------------------------------------------------------------- #
# Memory store
# --------------------------------------------------------------------------- #
class InMemoryMemoryStore:
    """Dict-backed :class:`MemoryStore`.

    Recall returns records whose scope is covered by the requested scope (so a
    project-wide recall includes section memories, and a section recall includes
    the project-wide ones), optionally filtered by kind, most-recent first.
    Semantic ``query`` ranking is not attempted here — that is the Qdrant-backed
    store's job; this returns by recency.
    """

    def __init__(self) -> None:
        self._records: list[MemoryRecord] = []

    async def remember(self, record: MemoryRecord) -> None:
        self._records.append(record)

    async def recall(
        self,
        scope: MemoryScope,
        *,
        kinds: Sequence[MemoryKind] | None = None,
        query: str | None = None,
        limit: int | None = None,
    ) -> Sequence[MemoryRecord]:
        kind_set = set(kinds) if kinds else None
        matched = [
            record
            for record in reversed(self._records)
            if scope.covers(record.scope) and (kind_set is None or record.kind in kind_set)
        ]
        return matched[:limit] if limit is not None else matched
