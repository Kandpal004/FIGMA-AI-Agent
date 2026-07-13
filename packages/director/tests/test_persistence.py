"""Persistence tests over the real SQLAlchemy stack (SQLite in-memory).

Proves the Postgres-shaped adapters durably persist a run and that it is
resumable: the run is completed across two facade calls, reloaded from the
database each time.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from director.application.director.commands import ApproveStep, SubmitSectionDesign
from director.application.ports.agent_executor_port import (
    AgentExecutionRequest,
    AgentExecutionResult,
    AgentExecutorPort,
    ExecutionStatus,
)
from director.domain.project.entities import Project, Section
from director.domain.shared.ids import ProjectId, RunId, SectionId
from director.domain.shared.value_objects import PageType
from director.infrastructure.persistence.mappers import project_to_model
from director.infrastructure.persistence.wiring import (
    build_sqlalchemy_environment,
    init_models,
)


class OkExecutor(AgentExecutorPort):
    async def execute(self, request: AgentExecutionRequest) -> AgentExecutionResult:
        return AgentExecutionResult(status=ExecutionStatus.OK, artifact={"by": request.step_key})


@pytest.fixture
async def sql_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    await init_models(engine)
    env = build_sqlalchemy_environment(session_factory, agent_executor=OkExecutor())
    tenant = uuid.uuid4()
    pid, sid = ProjectId.new(), SectionId.new()
    project = Project(
        id=pid, tenant_id=tenant, name="Acme",
        sections=(Section(id=sid, key="hero", page_type=PageType.HOMEPAGE),),
    )
    async with session_factory() as session:
        session.add(project_to_model(project))
        await session.commit()
    yield env, tenant, pid, sid
    await engine.dispose()


async def test_run_is_durable_and_resumable(sql_env) -> None:
    env, tenant, pid, sid = sql_env
    view = await env.facade.submit_section(
        SubmitSectionDesign(tenant_id=tenant, project_id=pid, section_id=sid, brief={"goal": "x"})
    )
    assert view.run.status == "paused"
    run_id = RunId.from_string(view.run.run_id)

    # Reloaded from the database (fresh session) — durability + resume.
    reloaded = await env.facade.get_run(run_id)
    assert reloaded.status == "paused"
    completed = {s.key for s in reloaded.steps if s.state == "completed"}
    assert "research" in completed and "performance_validation" in completed

    history = await env.facade.get_history(run_id)
    assert history and history[0].kind.value == "select_workflow"

    done = await env.facade.approve(ApproveStep(run_id=run_id, step_key="creative_director_gate"))
    assert done.run.status == "completed"
    assert (await env.facade.get_run(run_id)).status == "completed"
