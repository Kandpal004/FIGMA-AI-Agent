"""The persisted workflow state machine.

Pure, synchronous logic that answers exactly one question: *given a run in some
state and an event, what is the resulting run?* It validates the move against
the graph in :data:`core.contracts.workflow.TRANSITIONS`, applies it, and
appends an immutable audit record. It does **not** talk to a database, invoke
agents, or perform I/O — that separation is what makes the core pipeline logic
unit-testable without any infrastructure.

Persistence is the caller's concern (the mediator persists the returned
:class:`RunRecord` via a :class:`~orchestration.mediator.RunStore`). Keeping the
transition rules pure means the same code governs an in-memory test run and a
production run backed by Postgres.
"""

from __future__ import annotations

from core.contracts.workflow import (
    RunRecord,
    RunStatus,
    TransitionEvent,
    TransitionRecord,
    WorkflowState,
    next_states,
)
from core.errors import InvalidTransitionError
from core.logging import get_logger

log = get_logger(__name__)


class StateMachine:
    """Applies validated transitions to :class:`RunRecord` instances."""

    @staticmethod
    def can(state: WorkflowState, event: TransitionEvent) -> bool:
        """Whether `event` is legal from `state`."""
        return event in next_states(state)

    @staticmethod
    def apply(
        run: RunRecord,
        event: TransitionEvent,
        *,
        agent_role: str | None = None,
        notes: list[str] | None = None,
    ) -> RunRecord:
        """Return a new :class:`RunRecord` advanced by `event`.

        The input record is not mutated; a copy with the new state, refreshed
        status, and an appended :class:`TransitionRecord` is returned. This
        keeps transitions referentially transparent and makes optimistic
        persistence (compare-and-set on version) straightforward later.

        Raises:
            InvalidTransitionError: if `event` is not legal from the current
                state (e.g. trying to ADVANCE out of a terminal state).
        """
        legal = next_states(run.state)
        transition = legal.get(event)
        if transition is None:
            raise InvalidTransitionError(
                f"Event {event.value!r} is not legal from state {run.state.value!r}.",
                details={
                    "from_state": run.state.value,
                    "event": event.value,
                    "legal_events": [e.value for e in legal],
                },
            )

        record = TransitionRecord(
            from_state=run.state,
            event=event,
            to_state=transition.target,
            agent_role=agent_role or transition.owner,
            notes=notes or [],
        )

        # Derive the run-level lifecycle status from the destination state.
        if transition.target is WorkflowState.SECTION_COMPLETE:
            status = RunStatus.COMPLETED
        elif transition.target is WorkflowState.FAILED:
            status = RunStatus.FAILED
        else:
            status = RunStatus.RUNNING

        # A Creative-Director rejection is a full redesign — count it.
        redesign_count = run.redesign_count
        if (
            run.state is WorkflowState.CREATIVE_DIRECTOR_GATE
            and event is TransitionEvent.REJECT
        ):
            redesign_count += 1

        advanced = run.model_copy(
            update={
                "state": transition.target,
                "status": status,
                "history": [*run.history, record],
                "redesign_count": redesign_count,
            }
        )

        log.info(
            "run transition",
            extra={
                "run_id": str(run.run_id),
                "from_state": run.state.value,
                "event": event.value,
                "to_state": transition.target.value,
                "agent_role": record.agent_role,
            },
        )
        return advanced

    @staticmethod
    def owner_of_current_state(run: RunRecord) -> str | None:
        """The agent role whose work produces the run's *current* state.

        Found by locating the ADVANCE/REJECT transition that leads *into* the
        current state. Returns None for CREATED and terminal states, which have
        no owning agent to invoke.
        """
        from core.contracts.workflow import TRANSITIONS

        for transition in TRANSITIONS:
            if transition.target is run.state and transition.owner is not None:
                return transition.owner
        return None
