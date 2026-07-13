"""Response DTOs — serializable views the inbound layer returns.

The interfaces layer must not leak domain aggregates to callers (the API, a
worker, tests): domain objects carry behaviour and typed identifiers that do not
belong on the wire. These frozen view models are the read side of the Director's
contract — flat, primitive-typed projections of a run and the events an operation
emitted, ready to be JSON-encoded by whatever transport sits above.

They are pure data with simple ``from_*`` builders and no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime

from director.application.director.director_service import RunExecutionResult
from director.domain.shared import events as ev
from director.domain.workflow.run import WorkflowRun, WorkflowStep

__all__ = ["EventView", "RunResultView", "RunView", "StepView"]


@dataclass(frozen=True, slots=True)
class StepView:
    """A flat projection of one workflow step."""

    key: str
    state: str
    attempt: int
    limit: int
    is_terminal: bool
    rejection_notes: tuple[str, ...]

    @classmethod
    def from_step(cls, step: WorkflowStep) -> StepView:
        return cls(
            key=step.key,
            state=step.state.value,
            attempt=step.attempt.number,
            limit=step.attempt.limit,
            is_terminal=step.is_terminal,
            rejection_notes=step.rejection_notes,
        )


@dataclass(frozen=True, slots=True)
class RunView:
    """A flat projection of a workflow run."""

    run_id: str
    project_id: str
    section_id: str
    workflow_key: str
    workflow_version: int
    workflow_type: str
    status: str
    current_step_key: str | None
    redesign_count: int
    steps: tuple[StepView, ...]

    @classmethod
    def from_run(cls, run: WorkflowRun) -> RunView:
        return cls(
            run_id=str(run.id),
            project_id=str(run.project_id),
            section_id=str(run.section_id),
            workflow_key=run.workflow_key,
            workflow_version=run.workflow_version,
            workflow_type=run.workflow_type.value,
            status=run.status.value,
            current_step_key=run.current_step_key,
            redesign_count=run.redesign_count,
            steps=tuple(StepView.from_step(s) for s in run.steps),
        )


@dataclass(frozen=True, slots=True)
class EventView:
    """A flat projection of a domain event."""

    name: str
    occurred_at: str
    data: dict[str, object]

    @classmethod
    def from_event(cls, event: ev.DomainEvent) -> EventView:
        data: dict[str, object] = {}
        for f in fields(event):
            if f.name in ("run_id", "occurred_at"):
                continue
            value = getattr(event, f.name)
            data[f.name] = list(value) if isinstance(value, tuple) else value
        occurred = event.occurred_at
        return cls(
            name=event.name,
            occurred_at=occurred.isoformat() if isinstance(occurred, datetime) else str(occurred),
            data=data,
        )


@dataclass(frozen=True, slots=True)
class RunResultView:
    """The view returned by every Director operation: the run plus its events."""

    run: RunView
    events: tuple[EventView, ...]

    @classmethod
    def from_result(cls, result: RunExecutionResult) -> RunResultView:
        return cls(
            run=RunView.from_run(result.run),
            events=tuple(EventView.from_event(e) for e in result.events),
        )
