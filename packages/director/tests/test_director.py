"""The Director loop: the platform's decision behaviour, end to end.

Each test drives the real Director through the in-memory environment and asserts
the resulting run state, emitted events, and persisted audit/memory.
"""

from __future__ import annotations

from director.application.director.commands import (
    ApproveStep,
    CancelRun,
    ProvideInput,
    RejectStep,
    SubmitSectionDesign,
)
from director.application.director.director_service import InvalidDirectorOperationError
from director.application.ports.agent_executor_port import ExecutionStatus
from director.domain.shared.ids import RunId

import pytest

_SECTION_STEPS = [
    "research", "strategy", "ux", "wireframe", "wireframe_review", "ui",
    "ui_review", "design_system_validation", "accessibility_validation",
    "performance_validation",
]


def _event_names(view) -> list[str]:
    return [e.name for e in view.events]


async def test_happy_path_pauses_at_cd_gate_then_approves(make_env) -> None:
    env, tenant, pid, sid = await make_env()
    view = await env.facade.submit_section(
        SubmitSectionDesign(tenant_id=tenant, project_id=pid, section_id=sid, brief={"goal": "convert"})
    )
    assert view.run.status == "paused"
    assert view.run.current_step_key == "creative_director_gate"
    states = {s.key: s.state for s in view.run.steps}
    for key in _SECTION_STEPS:
        assert states[key] == "completed"
    assert states["creative_director_gate"] == "waiting_for_approval"
    assert "RunStarted" in _event_names(view)

    run_id = RunId.from_string(view.run.run_id)
    done = await env.facade.approve(ApproveStep(run_id=run_id, step_key="creative_director_gate", approver="cd"))
    assert done.run.status == "completed"
    assert "RunCompleted" in _event_names(done)

    history = await env.facade.get_history(run_id)
    assert history[0].kind.value == "select_workflow"
    assert any(d.kind.value == "complete" for d in history)
    assert any(r.kind.value == "approved_decision" for r in env.memory_store._records)


async def test_failed_step_is_retried(make_env) -> None:
    env, tenant, pid, sid = await make_env(script={"research": [ExecutionStatus.FAILED]})
    view = await env.facade.submit_section(
        SubmitSectionDesign(tenant_id=tenant, project_id=pid, section_id=sid)
    )
    research = next(s for s in view.run.steps if s.key == "research")
    assert research.state == "completed"
    assert research.attempt == 2
    assert "StepRetried" in _event_names(view)


async def test_cd_rejection_rolls_back_and_redesigns(make_env) -> None:
    env, tenant, pid, sid = await make_env()
    view = await env.facade.submit_section(
        SubmitSectionDesign(tenant_id=tenant, project_id=pid, section_id=sid)
    )
    run_id = RunId.from_string(view.run.run_id)
    rejected = await env.facade.reject(
        RejectStep(run_id=run_id, step_key="creative_director_gate", notes=("more contrast",))
    )
    assert rejected.run.redesign_count == 1
    assert rejected.run.status == "paused"
    assert rejected.run.current_step_key == "creative_director_gate"
    assert "StepRolledBack" in _event_names(rejected)

    approved = await env.facade.approve(ApproveStep(run_id=run_id, step_key="creative_director_gate"))
    assert approved.run.status == "completed"


async def test_guard_rail_fails_after_max_redesigns(make_env) -> None:
    env, tenant, pid, sid = await make_env(
        script={"ui_review": [ExecutionStatus.REJECTED] * 3}, max_redesigns=1
    )
    view = await env.facade.submit_section(
        SubmitSectionDesign(tenant_id=tenant, project_id=pid, section_id=sid)
    )
    assert view.run.status == "failed"
    assert view.run.redesign_count == 2
    assert "RunFailed" in _event_names(view)


async def test_blocked_step_pauses_and_resumes_with_input(make_env) -> None:
    env, tenant, pid, sid = await make_env(script={"research": [ExecutionStatus.NEEDS_INPUT]})
    view = await env.facade.submit_section(
        SubmitSectionDesign(tenant_id=tenant, project_id=pid, section_id=sid)
    )
    assert view.run.status == "paused"
    research = next(s for s in view.run.steps if s.key == "research")
    assert research.state == "blocked"
    assert "StepBlocked" in _event_names(view)

    run_id = RunId.from_string(view.run.run_id)
    resumed = await env.facade.provide_input(
        ProvideInput(run_id=run_id, step_key="research", input={"answer": 42})
    )
    assert resumed.run.status == "paused"  # reached the CD gate
    research2 = next(s for s in resumed.run.steps if s.key == "research")
    assert research2.state == "completed"


async def test_invalid_operation_and_cancel(make_env) -> None:
    env, tenant, pid, sid = await make_env()
    view = await env.facade.submit_section(
        SubmitSectionDesign(tenant_id=tenant, project_id=pid, section_id=sid)
    )
    run_id = RunId.from_string(view.run.run_id)
    with pytest.raises(InvalidDirectorOperationError):
        await env.facade.approve(ApproveStep(run_id=run_id, step_key="research"))

    cancelled = await env.facade.cancel(CancelRun(run_id=run_id, reason="stop"))
    assert cancelled.run.status == "cancelled"
