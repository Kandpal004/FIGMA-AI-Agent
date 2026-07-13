"""The Director's reasoning log — one append-only decision at a time.

Principle P5 requires that *every decision is auditable*: for any run we must be
able to reconstruct what the Director decided, when, about which step, and why.
A :class:`DecisionRecord` is one immutable entry in that log. The Director emits
one whenever it makes a choice — selecting a workflow, dispatching a step,
advancing, retrying, rolling back, approving, rejecting, pausing, resuming,
cancelling, completing, or failing a run.

This is distinct from the *state* audit (which records how steps moved): the
decision log records the Director's **reasoning**, the state log records the
**mechanics**. Together they answer both "what happened" and "why".

The record carries an ``occurred_at`` timestamp, but this module never reads a
clock — the timestamp is supplied by the caller (the Director, via an injected
clock port), keeping the domain free of ambient time.

Testing considerations
----------------------
* :class:`DecisionRecord` is frozen and validates a non-empty ``summary``.
* ``data`` is exposed as a read-only mapping so a record cannot be mutated
  after creation.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType

from core.errors import DesignDirectorError

from director.domain.shared.ids import DecisionId, RunId

__all__ = ["DecisionKind", "DecisionRecord", "InvalidDecisionError"]


class InvalidDecisionError(DesignDirectorError):
    """Raised when a decision record is constructed with invalid attributes."""

    code = "invalid_decision"
    http_status = 422


class DecisionKind(str, Enum):
    """The kind of decision the Director made.

    A closed vocabulary so decisions can be filtered and analysed. The value is
    the stable identifier used in persistence.
    """

    SELECT_WORKFLOW = "select_workflow"
    DISPATCH_STEP = "dispatch_step"
    ADVANCE = "advance"
    RETRY = "retry"
    ROLLBACK = "rollback"
    REQUEST_APPROVAL = "request_approval"
    APPROVE = "approve"
    REJECT = "reject"
    BLOCK = "block"
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    COMPLETE = "complete"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    """One immutable entry in the Director's reasoning log.

    Attributes:
        id: Decision identity.
        run_id: The run this decision concerns.
        kind: The category of decision.
        summary: A human-readable statement of the reasoning ("why").
        occurred_at: When the decision was made (supplied by the caller).
        step_key: The step the decision concerns, if any.
        data: Optional structured context (read-only), e.g. the agent status
            observed, the rollback target chosen, or the attempt number.
    """

    id: DecisionId
    run_id: RunId
    kind: DecisionKind
    summary: str
    occurred_at: datetime
    step_key: str | None = None
    data: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.summary or not self.summary.strip():
            raise InvalidDecisionError(
                "DecisionRecord.summary must be non-empty.",
                details={"id": str(self.id)},
            )
        if not isinstance(self.data, MappingProxyType):
            object.__setattr__(self, "data", MappingProxyType(dict(self.data)))
