"""Live workflow *instances*: the running counterpart of a definition.

Where a :class:`~director.domain.workflow.definition.WorkflowDefinition` is the
immutable *plan*, a :class:`WorkflowRun` is a concrete *execution* of that plan
for one subject (a section). Each :class:`WorkflowStep` in the run is the live
instance of a step spec, carrying the two orthogonal axes the platform tracks:

* its **position** — the step ``key``, which points back into the definition;
* its **lifecycle** — a :class:`~director.domain.state.step_state.StepState`.

The aggregate is **immutable**: every change (a state transition, an attempt
increment, a status change) is applied with a functional updater that returns a
*new* :class:`WorkflowRun`. This mirrors the discipline used throughout the
domain — it makes runs trivially snapshot-able, comparable, and free of hidden
mutation, and it is what lets the State Engine remain a pure function.

This module performs no I/O and reads no clock; persistence and timestamps are
the infrastructure layer's concern.

Testing considerations
----------------------
* :meth:`WorkflowRun.from_definition` builds one PENDING step per spec, each with
  a first :class:`~director.domain.shared.value_objects.Attempt` sized to the
  step's retry policy, and starts the run in :data:`RunStatus.CREATED`.
* Functional updaters return new instances and never mutate the original.
* :meth:`WorkflowRun.get_step` / :meth:`replace_step` raise
  :class:`StepNotInRunError` for unknown steps.
* :attr:`WorkflowRun.is_terminal` is ``True`` iff the status is terminal.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import Enum
from types import MappingProxyType

from core.errors import DesignDirectorError

from director.domain.shared.ids import ProjectId, RunId, SectionId, StepId
from director.domain.shared.value_objects import (
    Attempt,
    ExecutionMode,
    Priority,
    WorkflowType,
)
from director.domain.state.step_state import StepState
from director.domain.workflow.definition import WorkflowDefinition

__all__ = [
    "RunStatus",
    "StepNotInRunError",
    "WorkflowRun",
    "WorkflowStep",
]


class RunStatus(str, Enum):
    """The coarse, run-level lifecycle, distinct from per-step :class:`StepState`.

    * ``CREATED``   — instantiated, not yet started.
    * ``RUNNING``   — actively being driven by the Director.
    * ``PAUSED``    — halted awaiting external input or a human approval.
    * ``COMPLETED`` — terminal success (all steps completed).
    * ``FAILED``    — terminal failure.
    * ``CANCELLED`` — terminal; cancelled by request.
    """

    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        """Whether the run can no longer progress."""
        return self in _TERMINAL_RUN_STATES


_TERMINAL_RUN_STATES: frozenset[RunStatus] = frozenset(
    {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}
)


class StepNotInRunError(DesignDirectorError):
    """Raised when a step is addressed that is not part of the run."""

    code = "step_not_in_run"
    http_status = 404


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    """The live instance of a single workflow step.

    Attributes:
        id: Unique identity of this step instance.
        key: The step's position — the ``key`` of the owning
            :class:`~director.domain.workflow.definition.WorkflowStepSpec`.
        state: The step's current lifecycle state.
        attempt: The current attempt, bounded by the step's retry policy.
        rejection_notes: Notes from the most recent rejection, if any.
        output_summary: Short human summary of the last produced output.
    """

    id: StepId
    key: str
    attempt: Attempt
    state: StepState = StepState.PENDING
    rejection_notes: tuple[str, ...] = ()
    output_summary: str = ""

    @property
    def is_terminal(self) -> bool:
        """Whether this step has reached a terminal state."""
        return self.state.is_terminal

    def with_state(self, state: StepState) -> WorkflowStep:
        """Return a copy of this step in ``state``. Does not itself validate the
        transition — legality is enforced by the State Engine before this is
        called."""
        return replace(self, state=state)

    def with_attempt(self, attempt: Attempt) -> WorkflowStep:
        """Return a copy with the given attempt."""
        return replace(self, attempt=attempt)

    def with_rejection_notes(self, notes: tuple[str, ...]) -> WorkflowStep:
        """Return a copy carrying the given rejection notes."""
        return replace(self, rejection_notes=tuple(notes))

    def with_output_summary(self, summary: str) -> WorkflowStep:
        """Return a copy carrying the given output summary."""
        return replace(self, output_summary=summary)


@dataclass(frozen=True, slots=True)
class WorkflowRun:
    """An immutable aggregate: one execution of a workflow definition.

    Holds the current, consistent state of a run — its steps, overall status, and
    the pointer to the step currently in focus. The append-only audit trail
    (transitions and decisions) is recorded separately by the application/
    infrastructure layers; this aggregate carries only what is needed to resume.

    Attributes:
        id: Run identity.
        project_id: Owning project.
        section_id: The section this run designs.
        workflow_key: Key of the definition being executed.
        workflow_version: Version of that definition.
        workflow_type: PAGE or SECTION.
        status: The run-level :class:`RunStatus`.
        steps: The live steps, in definition order.
        status: The run-level :class:`RunStatus`.
        current_step_key: The step currently in focus, or ``None``.
        priority: Scheduling priority.
        execution_mode: How the run is executed.
        brief: The design brief / requirements for this run (read-only). Persisted
            so a resumed run can rebuild agent inputs without the original request.
        artifacts: Outputs accumulated across steps, keyed by step key (read-only).
        redesign_count: How many times the run has been rolled back; drives the
            Director's guard rail against infinite redesign loops.
    """

    id: RunId
    project_id: ProjectId
    section_id: SectionId
    workflow_key: str
    workflow_version: int
    workflow_type: WorkflowType
    steps: tuple[WorkflowStep, ...]
    status: RunStatus = RunStatus.CREATED
    current_step_key: str | None = None
    priority: Priority = Priority.NORMAL
    execution_mode: ExecutionMode = ExecutionMode.ASYNCHRONOUS
    brief: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    artifacts: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    redesign_count: int = 0

    # -- construction ------------------------------------------------------ #
    @classmethod
    def from_definition(
        cls,
        definition: WorkflowDefinition,
        *,
        run_id: RunId,
        project_id: ProjectId,
        section_id: SectionId,
        brief: Mapping[str, object] | None = None,
        priority: Priority = Priority.NORMAL,
        execution_mode: ExecutionMode = ExecutionMode.ASYNCHRONOUS,
    ) -> WorkflowRun:
        """Instantiate a run from a definition, with every step PENDING.

        Each step is given a fresh identity and a first attempt sized to that
        step's retry policy. The run starts in :data:`RunStatus.CREATED` with no
        current step; the Director advances it from there.
        """
        steps = tuple(
            WorkflowStep(
                id=StepId.new(),
                key=spec.key,
                attempt=Attempt.first(spec.retry.max_attempts),
                state=StepState.PENDING,
            )
            for spec in definition.steps
        )
        return cls(
            id=run_id,
            project_id=project_id,
            section_id=section_id,
            workflow_key=definition.key,
            workflow_version=definition.version,
            workflow_type=definition.workflow_type,
            steps=steps,
            status=RunStatus.CREATED,
            current_step_key=None,
            priority=priority,
            execution_mode=execution_mode,
            brief=brief or {},
        )

    def __post_init__(self) -> None:
        if not isinstance(self.steps, tuple):
            object.__setattr__(self, "steps", tuple(self.steps))
        if self.redesign_count < 0:
            raise DesignDirectorError(
                "WorkflowRun.redesign_count must be >= 0.", code="invalid_run"
            )
        if not isinstance(self.brief, MappingProxyType):
            object.__setattr__(self, "brief", MappingProxyType(dict(self.brief)))
        if not isinstance(self.artifacts, MappingProxyType):
            object.__setattr__(self, "artifacts", MappingProxyType(dict(self.artifacts)))

    # -- queries ----------------------------------------------------------- #
    def __len__(self) -> int:
        return len(self.steps)

    @property
    def is_terminal(self) -> bool:
        """Whether the run has reached a terminal status."""
        return self.status.is_terminal

    def has_step(self, key: str) -> bool:
        """Whether a step with ``key`` exists in the run."""
        return any(step.key == key for step in self.steps)

    def get_step(self, key: str) -> WorkflowStep:
        """Return the step with ``key``.

        Raises:
            StepNotInRunError: If no such step exists.
        """
        for step in self.steps:
            if step.key == key:
                return step
        raise StepNotInRunError(
            f"Step {key!r} is not part of run {self.id}.",
            details={"run_id": str(self.id), "step": key},
        )

    @property
    def current_step(self) -> WorkflowStep | None:
        """The step currently in focus, or ``None`` if none is set."""
        if self.current_step_key is None:
            return None
        return self.get_step(self.current_step_key)

    def steps_in_state(self, state: StepState) -> tuple[WorkflowStep, ...]:
        """All steps currently in ``state``, in order."""
        return tuple(step for step in self.steps if step.state is state)

    # -- functional updaters ---------------------------------------------- #
    def replace_step(self, step: WorkflowStep) -> WorkflowRun:
        """Return a copy with ``step`` substituted for the one sharing its key.

        Raises:
            StepNotInRunError: If no step with that key exists.
        """
        if not self.has_step(step.key):
            raise StepNotInRunError(
                f"Cannot replace unknown step {step.key!r} in run {self.id}.",
                details={"run_id": str(self.id), "step": step.key},
            )
        new_steps = tuple(step if s.key == step.key else s for s in self.steps)
        return replace(self, steps=new_steps)

    def with_status(self, status: RunStatus) -> WorkflowRun:
        """Return a copy with the given run status."""
        return replace(self, status=status)

    def with_current_step(self, key: str | None) -> WorkflowRun:
        """Return a copy pointing at ``key`` as the current step.

        Raises:
            StepNotInRunError: If ``key`` is not ``None`` and does not exist.
        """
        if key is not None and not self.has_step(key):
            raise StepNotInRunError(
                f"Cannot focus unknown step {key!r} in run {self.id}.",
                details={"run_id": str(self.id), "step": key},
            )
        return replace(self, current_step_key=key)

    def with_brief(self, brief: Mapping[str, object]) -> WorkflowRun:
        """Return a copy with the brief replaced."""
        return replace(self, brief=MappingProxyType(dict(brief)))

    def merge_brief(self, extra: Mapping[str, object]) -> WorkflowRun:
        """Return a copy with ``extra`` merged into the brief (e.g. input that
        unblocks a step)."""
        return replace(self, brief=MappingProxyType({**self.brief, **extra}))

    def with_artifact(self, step_key: str, artifact: Mapping[str, object]) -> WorkflowRun:
        """Return a copy recording ``step_key``'s output artifact."""
        merged = {**self.artifacts, step_key: dict(artifact)}
        return replace(self, artifacts=MappingProxyType(merged))

    def with_redesign_incremented(self) -> WorkflowRun:
        """Return a copy with the redesign counter incremented by one."""
        return replace(self, redesign_count=self.redesign_count + 1)
