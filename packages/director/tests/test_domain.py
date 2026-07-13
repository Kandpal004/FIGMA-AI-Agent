"""Domain-layer tests: the state machine, workflow definitions, and the catalog."""

from __future__ import annotations

import pytest

from director.domain.shared.value_objects import (
    Attempt,
    AttemptsExhaustedError,
    BackoffStrategy,
    InvalidPolicyError,
    Priority,
    RetryPolicy,
)
from director.domain.state.step_state import TERMINAL_STATES, StepState
from director.domain.state.transitions import (
    IllegalStateTransitionError,
    StepStateMachine,
    Transition,
)
from director.domain.workflow.catalog import WorkflowCatalog
from director.domain.workflow.definition import StepKind
from director.domain.shared.value_objects import PageType, WorkflowType


# --------------------------- state machine ------------------------------ #
def test_state_machine_integrity() -> None:
    StepStateMachine.verify_integrity()


def test_terminal_states() -> None:
    assert TERMINAL_STATES == {StepState.COMPLETED, StepState.FAILED, StepState.CANCELLED}
    assert StepState.COMPLETED.is_terminal
    assert not StepState.PENDING.is_terminal


@pytest.mark.parametrize(
    "source,target",
    [
        (StepState.PENDING, StepState.RUNNING),
        (StepState.RUNNING, StepState.COMPLETED),
        (StepState.RUNNING, StepState.WAITING_FOR_APPROVAL),
        (StepState.WAITING_FOR_APPROVAL, StepState.APPROVED),
        (StepState.APPROVED, StepState.COMPLETED),
        (StepState.REJECTED, StepState.PENDING),
        (StepState.RUNNING, StepState.PENDING),  # retry
    ],
)
def test_legal_transitions(source: StepState, target: StepState) -> None:
    machine = StepStateMachine()
    machine.validate(source, target)
    assert Transition(source, target).target is target


@pytest.mark.parametrize(
    "source,target",
    [
        (StepState.PENDING, StepState.COMPLETED),
        (StepState.RUNNING, StepState.APPROVED),  # gate must go via WAITING
        (StepState.COMPLETED, StepState.RUNNING),  # terminal
        (StepState.APPROVED, StepState.REJECTED),
        (StepState.FAILED, StepState.PENDING),
    ],
)
def test_illegal_transitions(source: StepState, target: StepState) -> None:
    machine = StepStateMachine()
    assert not machine.is_legal(source, target)
    with pytest.raises(IllegalStateTransitionError):
        machine.validate(source, target)


# --------------------------- value objects ------------------------------ #
def test_retry_policy_backoff_is_deterministic_and_clamped() -> None:
    policy = RetryPolicy(
        max_attempts=20, backoff=BackoffStrategy.EXPONENTIAL,
        base_delay_seconds=1, max_delay_seconds=10, multiplier=2,
    )
    assert policy.delay_seconds(1) == 0.0
    assert policy.delay_seconds(2) == 1.0
    assert policy.delay_seconds(3) == 2.0
    seq = [policy.delay_seconds(a) for a in range(2, 12)]
    assert max(seq) == 10.0 and seq == sorted(seq)


def test_retry_policy_validation() -> None:
    with pytest.raises(InvalidPolicyError):
        RetryPolicy(max_attempts=0)


def test_attempt_advances_and_exhausts() -> None:
    attempt = Attempt.first(3)
    attempt = attempt.increment().increment()
    assert attempt.number == 3 and attempt.is_exhausted
    with pytest.raises(AttemptsExhaustedError):
        attempt.increment()


def test_priority_ordering() -> None:
    assert Priority.URGENT > Priority.NORMAL > Priority.LOW
    assert Priority.default() is Priority.NORMAL


# --------------------------- catalog / definitions ---------------------- #
def test_catalog_builds_and_cross_references_resolve() -> None:
    catalog = WorkflowCatalog.default()
    section = catalog.section_design()
    assert len(section) == 11
    assert section.step_keys()[0] == "research"
    assert section.step_keys()[-1] == "creative_director_gate"
    assert len(section.gates()) == 6


def test_section_rollback_targets() -> None:
    section = WorkflowCatalog.default().section_design()
    assert section.resolve_rollback("creative_director_gate").key == "ui"
    assert section.resolve_rollback("wireframe_review").key == "ux"


def test_every_page_workflow_spawns_section_design() -> None:
    catalog = WorkflowCatalog.default()
    for page_type in PageType:
        page = catalog.for_page(page_type)
        assert page.workflow_type is WorkflowType.PAGE
        assert page.page_type is page_type
        for step in page.steps:
            assert step.kind is StepKind.COMPOSITE
            assert step.spawns == "section_design"
