"""SQLAlchemy repository implementations.

Concrete, Postgres-backed implementations of the application repository ports.
Each operates on an injected :class:`AsyncSession` (supplied by the unit of work)
and translates at the boundary via the mappers, so no ORM object escapes into the
application. Aggregates (project, run) are upserted whole, matching how they are
loaded.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.errors import NotFoundError

from director.domain.director.decision import DecisionRecord
from director.domain.project.entities import Project
from director.domain.shared.ids import ProjectId, RunId
from director.domain.workflow.run import WorkflowRun
from director.infrastructure.persistence import mappers
from director.infrastructure.persistence.models import (
    DecisionModel,
    ProjectModel,
    RunModel,
)

__all__ = [
    "SqlAlchemyDecisionRepository",
    "SqlAlchemyProjectRepository",
    "SqlAlchemyWorkflowRunRepository",
]


class SqlAlchemyProjectRepository:
    """Postgres-backed :class:`ProjectRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, project_id: ProjectId) -> Project:
        model = await self._session.get(ProjectModel, project_id.value)
        if model is None:
            raise NotFoundError(
                f"Project {project_id} not found.", details={"project_id": str(project_id)}
            )
        return mappers.model_to_project(model)

    async def add(self, project: Project) -> None:
        self._session.add(mappers.project_to_model(project))

    async def save(self, project: Project) -> None:
        model = await self._session.get(ProjectModel, project.id.value)
        if model is None:
            self._session.add(mappers.project_to_model(project))
        else:
            mappers.apply_project(model, project)


class SqlAlchemyWorkflowRunRepository:
    """Postgres-backed :class:`WorkflowRunRepository` (upsert on save)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, run_id: RunId) -> WorkflowRun:
        model = await self._session.get(RunModel, run_id.value)
        if model is None:
            raise NotFoundError(f"Run {run_id} not found.", details={"run_id": str(run_id)})
        return mappers.model_to_run(model)

    async def save(self, run: WorkflowRun) -> None:
        model = await self._session.get(RunModel, run.id.value)
        if model is None:
            self._session.add(mappers.run_to_model(run))
        else:
            mappers.apply_run(model, run)


class SqlAlchemyDecisionRepository:
    """Postgres-backed append-only :class:`DecisionRepository`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, decision: DecisionRecord) -> None:
        self._session.add(mappers.decision_to_model(decision))

    async def list_for_run(self, run_id: RunId) -> Sequence[DecisionRecord]:
        stmt = (
            select(DecisionModel)
            .where(DecisionModel.run_id == run_id.value)
            .order_by(DecisionModel.created_at)
        )
        result = await self._session.execute(stmt)
        return [mappers.model_to_decision(m) for m in result.scalars().all()]
