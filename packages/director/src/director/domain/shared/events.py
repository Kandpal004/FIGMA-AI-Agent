"""Domain events — immutable facts about things that happened during a run.

A domain event is a record that *something occurred* — a step was dispatched, a
gate rejected work, a run completed. Events are the platform's observability and
extension vocabulary: the Director emits them as it drives a run, and they are
surfaced to callers (for a live timeline today, and for an event bus / future
MCP orchestration tomorrow) without coupling the Director to any consumer.

Events are pure, immutable value objects. Like :class:`DecisionRecord`, they
carry an ``occurred_at`` supplied by the caller — this module reads no clock.

All events share the :class:`DomainEvent` base (``run_id`` + ``occurred_at``);
concrete subclasses add whatever context that fact needs. The :attr:`DomainEvent.name`
property yields a stable event name for logging and serialization.

Testing considerations
----------------------
* Every event is frozen and reports its :attr:`name`.
* Subclasses carry their step/context fields and remain immutable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from director.domain.shared.ids import RunId

__all__ = [
    "DomainEvent",
    "RunCancelled",
    "RunCompleted",
    "RunFailed",
    "RunPaused",
    "RunResumed",
    "RunStarted",
    "StepApproved",
    "StepAwaitingApproval",
    "StepBlocked",
    "StepCompleted",
    "StepDispatched",
    "StepFailed",
    "StepRejected",
    "StepRetried",
    "StepRolledBack",
]


@dataclass(frozen=True, slots=True)
class DomainEvent:
    """Base for all domain events.

    Attributes:
        run_id: The run the event belongs to.
        occurred_at: When it happened (supplied by the emitter).
    """

    run_id: RunId
    occurred_at: datetime

    @property
    def name(self) -> str:
        """A stable event name (the concrete class name)."""
        return type(self).__name__


@dataclass(frozen=True, slots=True)
class RunStarted(DomainEvent):
    """A run began execution."""

    workflow_key: str = ""


@dataclass(frozen=True, slots=True)
class StepDispatched(DomainEvent):
    """A step was dispatched to its agent for execution."""

    step_key: str = ""
    agent_role: str | None = None
    attempt: int = 1


@dataclass(frozen=True, slots=True)
class StepCompleted(DomainEvent):
    """A step finished successfully."""

    step_key: str = ""


@dataclass(frozen=True, slots=True)
class StepBlocked(DomainEvent):
    """A step became blocked awaiting external input."""

    step_key: str = ""


@dataclass(frozen=True, slots=True)
class StepAwaitingApproval(DomainEvent):
    """A gate step is awaiting an approval decision."""

    step_key: str = ""


@dataclass(frozen=True, slots=True)
class StepApproved(DomainEvent):
    """A gate step was approved."""

    step_key: str = ""


@dataclass(frozen=True, slots=True)
class StepRejected(DomainEvent):
    """A gate step was rejected."""

    step_key: str = ""
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StepRetried(DomainEvent):
    """A failed step was re-queued for another attempt."""

    step_key: str = ""
    attempt: int = 1


@dataclass(frozen=True, slots=True)
class StepRolledBack(DomainEvent):
    """A rejection rewound the run to an earlier step."""

    from_step: str = ""
    to_step: str = ""


@dataclass(frozen=True, slots=True)
class StepFailed(DomainEvent):
    """A step failed terminally (retries exhausted or a hard failure)."""

    step_key: str = ""
    error: str | None = None


@dataclass(frozen=True, slots=True)
class RunPaused(DomainEvent):
    """The run paused (blocked or awaiting a human approval)."""

    reason: str = ""


@dataclass(frozen=True, slots=True)
class RunResumed(DomainEvent):
    """The run resumed after a pause."""


@dataclass(frozen=True, slots=True)
class RunCompleted(DomainEvent):
    """The run finished successfully."""


@dataclass(frozen=True, slots=True)
class RunFailed(DomainEvent):
    """The run terminated in failure."""

    reason: str = ""


@dataclass(frozen=True, slots=True)
class RunCancelled(DomainEvent):
    """The run was cancelled by request."""

    reason: str = ""
