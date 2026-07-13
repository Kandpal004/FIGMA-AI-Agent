"""The State Engine — applies validated step-state transitions to a run.

The State Engine is the application-layer service that turns "move this step to
X" into a new, consistent :class:`WorkflowRun`. It is a thin, deterministic layer
over the domain :class:`~director.domain.state.transitions.StepStateMachine`:
the machine decides *legality*; the engine *applies* the legal move to the
aggregate (swapping in the updated step) and handles the small amount of
bookkeeping a transition carries (attempt increments, rejection notes).

It performs no I/O and holds no mutable state; the machine is injected, so the
engine is fully testable and swappable. Every method returns a new run and never
mutates its argument.

Testing considerations
----------------------
* Legal transitions produce the expected step state; illegal ones raise
  :class:`~director.domain.state.transitions.IllegalStateTransitionError` (via the
  machine) and leave no partial change.
* :meth:`retry` increments the attempt and re-queues the step to ``PENDING``;
  calling it past the retry limit raises
  :class:`~director.domain.shared.value_objects.AttemptsExhaustedError`.
* :meth:`reject` records the rejection notes on the step.
"""

from __future__ import annotations

from collections.abc import Sequence

from director.domain.shared.value_objects import Attempt
from director.domain.state.step_state import StepState
from director.domain.state.transitions import StepStateMachine
from director.domain.workflow.run import WorkflowRun, WorkflowStep

__all__ = ["StateEngine"]


class StateEngine:
    """Applies step-state transitions to :class:`WorkflowRun` aggregates."""

    def __init__(self, machine: StepStateMachine) -> None:
        self._machine = machine

    # -- core -------------------------------------------------------------- #
    def transition(
        self, run: WorkflowRun, step_key: str, target: StepState
    ) -> WorkflowRun:
        """Move ``step_key`` to ``target``, validating legality first.

        Args:
            run: The run to update.
            step_key: The step to transition.
            target: The desired next state.

        Returns:
            A new run with the step transitioned.

        Raises:
            IllegalStateTransitionError: If the move is not permitted.
            StepNotInRunError: If ``step_key`` is not part of the run.
        """
        step = run.get_step(step_key)
        self._machine.validate(step.state, target)
        return run.replace_step(step.with_state(target))

    # -- named convenience transitions ------------------------------------ #
    def start(self, run: WorkflowRun, step_key: str) -> WorkflowRun:
        """PENDING/BLOCKED → RUNNING (dispatch or resume)."""
        return self.transition(run, step_key, StepState.RUNNING)

    def complete(self, run: WorkflowRun, step_key: str) -> WorkflowRun:
        """→ COMPLETED."""
        return self.transition(run, step_key, StepState.COMPLETED)

    def block(self, run: WorkflowRun, step_key: str) -> WorkflowRun:
        """→ BLOCKED (awaiting external input)."""
        return self.transition(run, step_key, StepState.BLOCKED)

    def await_approval(self, run: WorkflowRun, step_key: str) -> WorkflowRun:
        """RUNNING → WAITING_FOR_APPROVAL (gate produced work)."""
        return self.transition(run, step_key, StepState.WAITING_FOR_APPROVAL)

    def approve(self, run: WorkflowRun, step_key: str) -> WorkflowRun:
        """WAITING_FOR_APPROVAL → APPROVED."""
        return self.transition(run, step_key, StepState.APPROVED)

    def finalize(self, run: WorkflowRun, step_key: str) -> WorkflowRun:
        """APPROVED → COMPLETED (finalize an approved gate)."""
        return self.transition(run, step_key, StepState.COMPLETED)

    def reject(
        self, run: WorkflowRun, step_key: str, notes: Sequence[str] = ()
    ) -> WorkflowRun:
        """WAITING_FOR_APPROVAL → REJECTED, recording rejection ``notes``."""
        run = self.transition(run, step_key, StepState.REJECTED)
        step = run.get_step(step_key)
        return run.replace_step(step.with_rejection_notes(tuple(notes)))

    def fail(self, run: WorkflowRun, step_key: str) -> WorkflowRun:
        """→ FAILED (terminal for the step)."""
        return self.transition(run, step_key, StepState.FAILED)

    def cancel(self, run: WorkflowRun, step_key: str) -> WorkflowRun:
        """→ CANCELLED (from any non-terminal state)."""
        return self.transition(run, step_key, StepState.CANCELLED)

    def retry(self, run: WorkflowRun, step_key: str) -> WorkflowRun:
        """Re-queue a step for another attempt: RUNNING/BLOCKED → PENDING with the
        attempt counter advanced.

        Raises:
            AttemptsExhaustedError: If the step has no attempts remaining.
            IllegalStateTransitionError: If the current state cannot re-queue.
        """
        step = run.get_step(step_key)
        self._machine.validate(step.state, StepState.PENDING)
        next_attempt = step.attempt.increment()
        return run.replace_step(
            step.with_attempt(next_attempt).with_state(StepState.PENDING)
        )

    def reset_to_pending(self, run: WorkflowRun, step_key: str) -> WorkflowRun:
        """Reset a step to PENDING to begin a fresh redesign pass.

        Used by rollback to re-run the rollback target and every step between it
        and the rejecting gate. A rejected/running/blocked step re-queues via a
        legal transition; an already-completed step has no edge back to PENDING
        (COMPLETED is terminal for the step), so a *fresh pass* is modelled by
        replacing it with a new PENDING step of the same identity and a renewed
        attempt budget — which is exactly what a redesign is.
        """
        step = run.get_step(step_key)
        if step.state is StepState.PENDING:
            return run
        if self._machine.is_legal(step.state, StepState.PENDING):
            return run.replace_step(step.with_state(StepState.PENDING))
        fresh = WorkflowStep(
            id=step.id,
            key=step.key,
            attempt=Attempt.first(step.attempt.limit),
            state=StepState.PENDING,
        )
        return run.replace_step(fresh)
