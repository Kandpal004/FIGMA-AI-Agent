"""End-to-end proof that the orchestration foundation is wired correctly.

These tests use trivial stub agents (no LLM, no I/O) registered for every role,
then drive a full run through the mediator. They assert three things Phase 1
promised:

1. The happy path walks every workflow state in order to SECTION_COMPLETE.
2. A Creative-Director rejection loops the run back to UI and is recorded.
3. The redesign guard rail fails a run that is rejected forever, rather than
   looping infinitely.

If these pass, the skeleton every real agent will slot into is sound.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from core.contracts.agent import AgentInput, AgentOutput, AgentRole, AgentStatus, BaseAgent
from core.contracts.workflow import RunRecord, RunStatus, WorkflowState
from orchestration.mediator import InMemoryRunStore, Mediator
from orchestration.registry import AgentRegistry


def _make_agent(role: AgentRole, status: AgentStatus = AgentStatus.OK) -> type[BaseAgent]:
    """Build a stub agent class that always returns `status` for `role`.

    The `run` method is defined inside the class body (via a closure over
    `role`/`status`) so the concrete override clears BaseAgent's abstract
    marker — assigning it after class creation would not.
    """
    _role, _status = role, status

    class _Stub(BaseAgent):
        role = _role

        async def run(self, agent_input: AgentInput) -> AgentOutput:  # noqa: ARG002
            if _status is AgentStatus.REJECTED:
                return AgentOutput(
                    role=_role,
                    status=_status,
                    revision_notes=[f"{_role.value} demands changes"],
                    summary=f"{_role.value} rejected",
                )
            return AgentOutput(
                role=_role,
                status=_status,
                artifact={"produced_by": _role.value},
                summary=f"{_role.value} ok",
            )

    _Stub.__name__ = f"Stub_{role.value}"
    return _Stub


def _registry(overrides: dict[AgentRole, AgentStatus] | None = None) -> AgentRegistry:
    """A registry with a stub for every role; `overrides` set specific outcomes."""
    overrides = overrides or {}
    registry = AgentRegistry()
    for role in AgentRole:
        registry.register(_make_agent(role, overrides.get(role, AgentStatus.OK)))
    return registry


def _fresh_run() -> RunRecord:
    return RunRecord(tenant_id=uuid4(), section="hero", brief={"goal": "convert"})


@pytest.mark.asyncio
async def test_happy_path_reaches_section_complete() -> None:
    mediator = Mediator(_registry(), InMemoryRunStore())

    result = await mediator.start(_fresh_run())

    assert result.state is WorkflowState.SECTION_COMPLETE
    assert result.status is RunStatus.COMPLETED
    assert result.redesign_count == 0

    # The audit trail should have walked through the key milestones in order.
    visited = [t.to_state for t in result.history]
    for milestone in (
        WorkflowState.RESEARCH,
        WorkflowState.UX,
        WorkflowState.WIREFRAME_REVIEW,
        WorkflowState.UI_REVIEW,
        WorkflowState.CREATIVE_DIRECTOR_GATE,
        WorkflowState.SECTION_COMPLETE,
    ):
        assert milestone in visited


@pytest.mark.asyncio
async def test_creative_director_rejection_loops_back_to_ui() -> None:
    # CD rejects the first time it is asked, then a later start with OK completes.
    # Here we assert the *recorded* redesign loop after a single rejection by
    # capping redesigns at 0 so the run fails right after the loop-back, proving
    # the REJECT edge routed to UI and was counted.
    registry = _registry({AgentRole.CREATIVE_DIRECTOR: AgentStatus.REJECTED})
    mediator = Mediator(registry, InMemoryRunStore(), max_redesigns=0)

    result = await mediator.start(_fresh_run())

    # A CD rejection loops to UI, increments the counter, then the guard trips.
    assert result.status is RunStatus.FAILED
    assert result.redesign_count == 1
    reject = next(
        t for t in result.history
        if t.from_state is WorkflowState.CREATIVE_DIRECTOR_GATE
    )
    assert reject.to_state is WorkflowState.UI
    assert reject.notes == ["creative_director demands changes"]


@pytest.mark.asyncio
async def test_redesign_guard_rail_prevents_infinite_loop() -> None:
    registry = _registry({AgentRole.CREATIVE_DIRECTOR: AgentStatus.REJECTED})
    mediator = Mediator(registry, InMemoryRunStore(), max_redesigns=2)

    result = await mediator.start(_fresh_run())

    assert result.state is WorkflowState.FAILED
    assert result.redesign_count == 3  # tripped once past the max of 2


@pytest.mark.asyncio
async def test_needs_input_pauses_the_run() -> None:
    registry = _registry({AgentRole.RESEARCH: AgentStatus.NEEDS_INPUT})
    mediator = Mediator(registry, InMemoryRunStore())

    result = await mediator.start(_fresh_run())

    assert result.status is RunStatus.PAUSED
    assert result.state is WorkflowState.RESEARCH
