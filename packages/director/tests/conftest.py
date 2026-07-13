"""Shared test fixtures and fakes for the Director Engine suite.

These fakes exercise the real domain and application code through the ports; no
external services are involved. The scriptable executor lets each test drive the
Director down a specific path.
"""

from __future__ import annotations

import uuid
from collections import deque
from datetime import UTC, datetime

import pytest

from director.application.ports.agent_executor_port import (
    AgentExecutionRequest,
    AgentExecutionResult,
    AgentExecutorPort,
    ExecutionStatus,
)
from director.domain.project.entities import Project, Section
from director.domain.shared.ids import ProjectId, SectionId
from director.domain.shared.value_objects import PageType
from director.infrastructure.container import (
    DirectorEnvironment,
    build_in_memory_environment,
)
from director.infrastructure.inmemory import Clock


class FixedClock(Clock):
    """A deterministic clock for repeatable timestamps."""

    def now(self) -> datetime:
        return datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC)


class ScriptedExecutor(AgentExecutorPort):
    """An executor that returns scripted statuses per step key (default OK)."""

    def __init__(self, script: dict[str, list[ExecutionStatus]] | None = None) -> None:
        self._script = {k: deque(v) for k, v in (script or {}).items()}
        self.calls: list[tuple[str, int]] = []

    async def execute(self, request: AgentExecutionRequest) -> AgentExecutionResult:
        self.calls.append((request.step_key, request.attempt))
        queue = self._script.get(request.step_key)
        status = queue.popleft() if queue else ExecutionStatus.OK
        if status is ExecutionStatus.REJECTED:
            return AgentExecutionResult(
                status=status, revision_notes=(f"fix {request.step_key}",), summary="rejected"
            )
        if status is ExecutionStatus.FAILED:
            return AgentExecutionResult(status=status, error=f"{request.step_key} failed")
        return AgentExecutionResult(status=status, artifact={"by": request.step_key})


@pytest.fixture
def make_env():
    """Factory returning a fully-wired in-memory environment plus a seeded
    project and its identifiers."""

    async def _make(
        script: dict[str, list[ExecutionStatus]] | None = None, max_redesigns: int = 3
    ) -> tuple[DirectorEnvironment, uuid.UUID, ProjectId, SectionId]:
        env = build_in_memory_environment(
            ScriptedExecutor(script), clock=FixedClock(), max_redesigns=max_redesigns
        )
        tenant = uuid.uuid4()
        pid, sid = ProjectId.new(), SectionId.new()
        project = Project(
            id=pid,
            tenant_id=tenant,
            name="Acme Store",
            sections=(Section(id=sid, key="hero", page_type=PageType.HOMEPAGE),),
        )
        async with env.unit_of_work_factory() as uow:
            await uow.projects.add(project)
            await uow.commit()
        return env, tenant, pid, sid

    return _make
