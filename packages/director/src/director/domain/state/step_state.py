"""The canonical lifecycle states of a workflow step.

Every unit of work the Director tracks — an agent invocation, a review, a
human approval, a retry — is a *step*, and every step is, at any instant, in
exactly one :class:`StepState`. This enum is the single, authoritative
vocabulary of "how is this step doing" for the entire AI Operating System; the
Director Engine, Workflow Engine, Creative-Director gate, human-approval flow,
retry engine, rollback engine, and any future MCP orchestration all speak it.

Note the deliberate separation of concerns: :class:`StepState` answers *how a
step is doing* (its lifecycle). It is orthogonal to *which* step it is (the
step's position in a workflow, carried elsewhere). Keeping these two axes apart
is what lets one small state machine govern every step uniformly.

The **legal transitions** between these states are defined in the sibling module
:mod:`director.domain.state.transitions`; this module owns only the states
themselves and their terminal classification.

This module is pure domain: it imports only the standard library, performs no
I/O, holds no mutable module state, and has no side effects.

Testing considerations
----------------------
* There are exactly nine states, and ``StepState("pending")`` resolves by value.
* :attr:`StepState.is_terminal` is ``True`` for and only for
  :data:`TERMINAL_STATES` (``COMPLETED``, ``FAILED``, ``CANCELLED``).
* :data:`TERMINAL_STATES` is a ``frozenset`` and therefore immutable.
"""

from __future__ import annotations

from enum import Enum

__all__ = ["TERMINAL_STATES", "StepState"]


class StepState(str, Enum):
    """The nine canonical states a workflow step may occupy.

    States and their meaning:

    * ``PENDING`` — created and scheduled, not yet started.
    * ``RUNNING`` — actively executing (an agent is working).
    * ``BLOCKED`` — cannot proceed; awaiting external input or an unmet
      dependency. Resolvable back into execution.
    * ``WAITING_FOR_APPROVAL`` — work is done and paused at a gate, awaiting an
      approval decision (automatic resolution by the system, or a human
      sign-off).
    * ``APPROVED`` — the gate granted approval; the step is cleared to finalize.
    * ``REJECTED`` — the gate vetoed the work; the run must roll back, retry, or
      give up. **Not** terminal — a rejected step is reset for redesign or fails.
    * ``COMPLETED`` — terminal success; the step's work is final.
    * ``FAILED`` — terminal failure; retries (if any) were exhausted.
    * ``CANCELLED`` — terminal; the step was cancelled before completing.

    The string value is the stable identifier used in persistence, transport,
    and logs, so it must never change once released.
    """

    PENDING = "pending"
    RUNNING = "running"
    BLOCKED = "blocked"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        """Whether this state is terminal (no outgoing transitions exist).

        A terminal step has reached a final outcome and cannot transition
        further. The terminal states are exactly :data:`TERMINAL_STATES`.
        """
        return self in TERMINAL_STATES

    @classmethod
    def terminal(cls) -> frozenset[StepState]:
        """Return the set of terminal states."""
        return TERMINAL_STATES


#: The states from which no further transition is legal. Kept as a module-level
#: ``frozenset`` (immutable) and used as the single source of truth for terminal
#: classification, referenced by both :meth:`StepState.is_terminal` and the
#: transition engine's integrity checks.
TERMINAL_STATES: frozenset[StepState] = frozenset(
    {StepState.COMPLETED, StepState.FAILED, StepState.CANCELLED}
)
