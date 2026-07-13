"""The canonical step-state transition table and its deterministic engine.

This module encodes *which* :class:`~director.domain.state.step_state.StepState`
changes are legal and provides a pure, stateless engine to validate and perform
them. It is the beating heart of the platform's control flow: the Director
Engine, Workflow Engine, Creative-Director gate, human-approval flow, retry
engine, rollback engine, and any future MCP orchestration all move steps *only*
through this table. Any move not in the table is illegal and raises a domain
exception — there is no other way to change a step's state.

Design guarantees
-----------------
* **Deterministic.** Legality depends solely on ``(source, target)`` and the
  constant table; it never consults a clock, randomness, or external state.
* **No hidden state, no side effects.** The engine holds no mutable state and
  performs no I/O. The table is exposed read-only via a
  :class:`types.MappingProxyType`.
* **Injectable.** :class:`StepStateMachine` is a stateless service — construct
  and inject it wherever transition logic is needed; two instances are
  interchangeable. It is not a singleton and owns no global mutable state.
* **Self-verifying.** :meth:`StepStateMachine.verify_integrity` proves the table
  is internally consistent (total coverage, correct terminals, no self-loops),
  so structural mistakes are caught by a test rather than in production.

The legal graph
---------------
::

    PENDING              → RUNNING, BLOCKED, CANCELLED
    RUNNING              → COMPLETED, WAITING_FOR_APPROVAL, BLOCKED,
                           FAILED, PENDING (retry re-queue), CANCELLED
    BLOCKED              → RUNNING (resume), PENDING (re-queue), FAILED, CANCELLED
    WAITING_FOR_APPROVAL → APPROVED, REJECTED, CANCELLED
    APPROVED             → COMPLETED, CANCELLED
    REJECTED             → PENDING (rollback/redesign), FAILED, CANCELLED
    COMPLETED            → (terminal)
    FAILED               → (terminal)
    CANCELLED            → (terminal)

Two modelling decisions worth noting:

* **Gate outcomes always route through ``WAITING_FOR_APPROVAL``.** A gate step
  goes ``RUNNING → WAITING_FOR_APPROVAL`` and is then resolved to ``APPROVED`` or
  ``REJECTED``. For an automatic gate the system resolves it immediately; for a
  manual gate it pauses for a human. One uniform path serves both, so
  ``RUNNING`` never jumps straight to ``APPROVED``/``REJECTED``.
* **Retry is ``RUNNING → PENDING``.** A failed-but-retryable attempt re-queues to
  ``PENDING``; ``FAILED`` is reserved for the terminal, retries-exhausted outcome.
  The state machine permits both moves; *which* one to take is a policy decision
  owned by the retry engine, not by this table.

Testing considerations
----------------------
* :meth:`StepStateMachine.verify_integrity` passes.
* Every legal edge above validates; a representative set of illegal edges
  (e.g. ``PENDING → COMPLETED``, ``COMPLETED → RUNNING``, ``APPROVED → REJECTED``,
  ``RUNNING → APPROVED``, ``FAILED → PENDING``) raises
  :class:`IllegalStateTransitionError`.
* :class:`Transition` validates on construction and is immutable.
* The exposed :data:`LEGAL_TRANSITIONS` mapping is read-only.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from core.errors import DesignDirectorError

from director.domain.state.step_state import TERMINAL_STATES, StepState

__all__ = [
    "LEGAL_TRANSITIONS",
    "IllegalStateTransitionError",
    "StateMachineIntegrityError",
    "StepStateMachine",
    "Transition",
]


# --------------------------------------------------------------------------- #
# Domain exceptions
# --------------------------------------------------------------------------- #
class IllegalStateTransitionError(DesignDirectorError):
    """Raised when a step-state transition is not permitted by the table.

    Carries the offending ``source``/``target`` and the set of targets that
    *would* have been legal, so callers and logs get an actionable message.
    """

    code = "illegal_state_transition"
    http_status = 409

    def __init__(self, source: StepState, target: StepState) -> None:
        self.source = source
        self.target = target
        super().__init__(
            f"Illegal step-state transition: {source.value} -> {target.value}.",
            details={
                "source": source.value,
                "target": target.value,
                "allowed": sorted(s.value for s in _TRANSITION_TABLE[source]),
            },
        )


class StateMachineIntegrityError(DesignDirectorError):
    """Raised by :meth:`StepStateMachine.verify_integrity` when the transition
    table is structurally inconsistent. This indicates a programming error in
    the table definition, not a runtime condition."""

    code = "state_machine_integrity"
    http_status = 500


# --------------------------------------------------------------------------- #
# The canonical table (immutable constant, exposed read-only)
# --------------------------------------------------------------------------- #
_TRANSITION_TABLE: dict[StepState, frozenset[StepState]] = {
    StepState.PENDING: frozenset(
        {StepState.RUNNING, StepState.BLOCKED, StepState.CANCELLED}
    ),
    StepState.RUNNING: frozenset(
        {
            StepState.COMPLETED,
            StepState.WAITING_FOR_APPROVAL,
            StepState.BLOCKED,
            StepState.FAILED,
            StepState.PENDING,  # retry re-queue
            StepState.CANCELLED,
        }
    ),
    StepState.BLOCKED: frozenset(
        {
            StepState.RUNNING,  # resume once unblocked
            StepState.PENDING,  # re-queue once unblocked
            StepState.FAILED,
            StepState.CANCELLED,
        }
    ),
    StepState.WAITING_FOR_APPROVAL: frozenset(
        {StepState.APPROVED, StepState.REJECTED, StepState.CANCELLED}
    ),
    StepState.APPROVED: frozenset({StepState.COMPLETED, StepState.CANCELLED}),
    StepState.REJECTED: frozenset(
        {
            StepState.PENDING,  # rollback / redesign
            StepState.FAILED,
            StepState.CANCELLED,
        }
    ),
    StepState.COMPLETED: frozenset(),
    StepState.FAILED: frozenset(),
    StepState.CANCELLED: frozenset(),
}

#: Read-only view of the canonical transition table. Attempting to mutate it
#: raises ``TypeError`` — the graph is a constant, not configurable state.
LEGAL_TRANSITIONS: Mapping[StepState, frozenset[StepState]] = MappingProxyType(
    _TRANSITION_TABLE
)


# --------------------------------------------------------------------------- #
# A validated transition value object
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class Transition:
    """An immutable, *already-validated* step-state move.

    Constructing a :class:`Transition` proves — at construction time — that the
    move is legal; an illegal pair raises :class:`IllegalStateTransitionError`.
    This makes a ``Transition`` a small carrier of proof: any code holding one
    can trust the move it describes is permitted.

    Attributes:
        source: The state moved from.
        target: The state moved to.
    """

    source: StepState
    target: StepState

    def __post_init__(self) -> None:
        if self.target not in _TRANSITION_TABLE[self.source]:
            raise IllegalStateTransitionError(self.source, self.target)


# --------------------------------------------------------------------------- #
# The engine
# --------------------------------------------------------------------------- #
class StepStateMachine:
    """A pure, stateless service for validating and performing step transitions.

    Holds no state of its own; every method is a deterministic function of its
    arguments and the constant table. Construct and inject it wherever
    transition logic is required::

        machine = StepStateMachine()
        machine.validate(StepState.PENDING, StepState.RUNNING)   # ok
        machine.validate(StepState.PENDING, StepState.COMPLETED) # raises
    """

    def allowed(self, source: StepState) -> frozenset[StepState]:
        """Return the set of states reachable from ``source`` in one step."""
        return _TRANSITION_TABLE[source]

    def is_legal(self, source: StepState, target: StepState) -> bool:
        """Whether ``source -> target`` is a permitted transition."""
        return target in _TRANSITION_TABLE[source]

    def validate(self, source: StepState, target: StepState) -> None:
        """Assert that ``source -> target`` is legal.

        Raises:
            IllegalStateTransitionError: If the transition is not permitted.
        """
        if not self.is_legal(source, target):
            raise IllegalStateTransitionError(source, target)

    def transition(self, source: StepState, target: StepState) -> Transition:
        """Validate and return the move as a :class:`Transition`.

        Args:
            source: The current state.
            target: The desired next state.

        Returns:
            A validated :class:`Transition` describing the move.

        Raises:
            IllegalStateTransitionError: If the transition is not permitted.
        """
        return Transition(source=source, target=target)

    def is_terminal(self, state: StepState) -> bool:
        """Whether ``state`` is terminal (has no outgoing transitions)."""
        return state.is_terminal

    @staticmethod
    def verify_integrity() -> None:
        """Prove the transition table is internally consistent.

        Intended to be called from tests and startup self-checks. Validates:

        1. every :class:`StepState` is a key in the table (total coverage);
        2. every listed target is a valid :class:`StepState`;
        3. no state transitions to itself (no self-loops);
        4. the states with no outgoing transitions are *exactly*
           :data:`~director.domain.state.step_state.TERMINAL_STATES`.

        Raises:
            StateMachineIntegrityError: If any invariant is violated.
        """
        # 1. total coverage
        missing = [s for s in StepState if s not in _TRANSITION_TABLE]
        if missing:
            raise StateMachineIntegrityError(
                "Transition table is missing states.",
                details={"missing": [s.value for s in missing]},
            )

        for source, targets in _TRANSITION_TABLE.items():
            # 2. valid targets
            for target in targets:
                if not isinstance(target, StepState):  # pragma: no cover - typing guard
                    raise StateMachineIntegrityError(
                        "Transition table contains a non-StepState target.",
                        details={"source": source.value, "target": repr(target)},
                    )
            # 3. no self-loops
            if source in targets:
                raise StateMachineIntegrityError(
                    "Transition table contains a self-loop.",
                    details={"state": source.value},
                )

        # 4. terminals are exactly the states with no outgoing transitions
        empty = frozenset(s for s, t in _TRANSITION_TABLE.items() if not t)
        if empty != TERMINAL_STATES:
            raise StateMachineIntegrityError(
                "States with no outgoing transitions do not match TERMINAL_STATES.",
                details={
                    "no_outgoing": sorted(s.value for s in empty),
                    "terminal_states": sorted(s.value for s in TERMINAL_STATES),
                },
            )
