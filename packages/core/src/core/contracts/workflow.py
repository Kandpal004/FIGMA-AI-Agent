"""The workflow contract: states, transitions, and the run record.

This module encodes the design pipeline as an explicit, data-defined state
machine. It contains **no execution logic** — just the shape of the graph and
the record we persist. The engine that walks this graph lives in
:mod:`orchestration.state_machine`; keeping the graph *definition* here in
`core` means both the API and the orchestrator agree on one source of truth.

The pipeline (from the product spec)::

    Research → Business Strategy → UX → Wireframe → Review ─┐
        ▲                                                    │ reject
        └────────────────────────────────────────────────────┘
                                                       accept
        → UI → Review ─┐
             ▲          │ reject
             └──────────┘
                  accept
        → Design-System Validation → Accessibility → Performance
        → Creative Director Gate ─┐
             ▲                     │ reject (final authority)
             └─────────────────────┘
                  approve
        → Section Complete

Two loops matter: the **Reviewer** can bounce a wireframe back to UX and a UI
back to UI-redesign, and the **Creative Director** — holding final authority —
can bounce an otherwise-passing section back to UI for a full redesign.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class WorkflowState(str, Enum):
    """Every state a design run for a single section can occupy.

    Ordering here mirrors the happy path but is not relied upon — the legal
    graph is defined by :data:`TRANSITIONS`, not by declaration order.
    """

    CREATED = "created"
    RESEARCH = "research"
    STRATEGY = "strategy"
    UX = "ux"
    WIREFRAME = "wireframe"
    WIREFRAME_REVIEW = "wireframe_review"
    UI = "ui"
    UI_REVIEW = "ui_review"
    DESIGN_SYSTEM_VALIDATION = "design_system_validation"
    ACCESSIBILITY_VALIDATION = "accessibility_validation"
    PERFORMANCE_VALIDATION = "performance_validation"
    CREATIVE_DIRECTOR_GATE = "creative_director_gate"
    SECTION_COMPLETE = "section_complete"
    FAILED = "failed"


class TransitionEvent(str, Enum):
    """The event that drives a transition.

    Derived by the mediator from an :class:`~core.contracts.agent.AgentOutput`
    status, then applied to the state machine.
    """

    ADVANCE = "advance"
    """Work passed; move to the next state."""

    REJECT = "reject"
    """A gatekeeper vetoed; loop back for revision."""

    FAIL = "fail"
    """Unrecoverable error; move to the terminal FAILED state."""


class RunStatus(str, Enum):
    """The lifecycle status of a run, orthogonal to its current WorkflowState.

    A run in state UI can have status RUNNING (an agent is executing) or PAUSED
    (awaiting human input / resources).
    """

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class Transition(BaseModel):
    """A single legal edge in the state machine graph."""

    source: WorkflowState
    event: TransitionEvent
    target: WorkflowState
    #: The agent role primarily responsible for producing the target state's
    #: work. `None` for bookkeeping transitions (e.g. into SECTION_COMPLETE).
    owner: str | None = None


# --------------------------------------------------------------------------- #
# The graph. This is the single source of truth for legal movement.
# Each ADVANCE edge names the agent role that owns the *target* state's work,
# so the mediator can look up which agent to invoke next.
# --------------------------------------------------------------------------- #
TRANSITIONS: tuple[Transition, ...] = (
    # Linear intake through UX.
    Transition(source=WorkflowState.CREATED, event=TransitionEvent.ADVANCE,
               target=WorkflowState.RESEARCH, owner="research"),
    Transition(source=WorkflowState.RESEARCH, event=TransitionEvent.ADVANCE,
               target=WorkflowState.STRATEGY, owner="business_analyst"),
    Transition(source=WorkflowState.STRATEGY, event=TransitionEvent.ADVANCE,
               target=WorkflowState.UX, owner="ux_architect"),
    Transition(source=WorkflowState.UX, event=TransitionEvent.ADVANCE,
               target=WorkflowState.WIREFRAME, owner="information_architect"),

    # Wireframe review loop.
    Transition(source=WorkflowState.WIREFRAME, event=TransitionEvent.ADVANCE,
               target=WorkflowState.WIREFRAME_REVIEW, owner="reviewer"),
    Transition(source=WorkflowState.WIREFRAME_REVIEW, event=TransitionEvent.REJECT,
               target=WorkflowState.UX, owner="ux_architect"),
    Transition(source=WorkflowState.WIREFRAME_REVIEW, event=TransitionEvent.ADVANCE,
               target=WorkflowState.UI, owner="senior_ui_designer"),

    # UI review loop.
    Transition(source=WorkflowState.UI, event=TransitionEvent.ADVANCE,
               target=WorkflowState.UI_REVIEW, owner="reviewer"),
    Transition(source=WorkflowState.UI_REVIEW, event=TransitionEvent.REJECT,
               target=WorkflowState.UI, owner="senior_ui_designer"),
    Transition(source=WorkflowState.UI_REVIEW, event=TransitionEvent.ADVANCE,
               target=WorkflowState.DESIGN_SYSTEM_VALIDATION,
               owner="design_system_architect"),

    # Validation chain.
    Transition(source=WorkflowState.DESIGN_SYSTEM_VALIDATION,
               event=TransitionEvent.ADVANCE,
               target=WorkflowState.ACCESSIBILITY_VALIDATION,
               owner="accessibility_expert"),
    Transition(source=WorkflowState.DESIGN_SYSTEM_VALIDATION,
               event=TransitionEvent.REJECT,
               target=WorkflowState.UI, owner="senior_ui_designer"),
    Transition(source=WorkflowState.ACCESSIBILITY_VALIDATION,
               event=TransitionEvent.ADVANCE,
               target=WorkflowState.PERFORMANCE_VALIDATION,
               owner="performance_expert"),
    Transition(source=WorkflowState.ACCESSIBILITY_VALIDATION,
               event=TransitionEvent.REJECT,
               target=WorkflowState.UI, owner="senior_ui_designer"),
    Transition(source=WorkflowState.PERFORMANCE_VALIDATION,
               event=TransitionEvent.ADVANCE,
               target=WorkflowState.CREATIVE_DIRECTOR_GATE,
               owner="creative_director"),
    Transition(source=WorkflowState.PERFORMANCE_VALIDATION,
               event=TransitionEvent.REJECT,
               target=WorkflowState.UI, owner="senior_ui_designer"),

    # Creative Director — final authority. Approval completes; rejection loops
    # the entire section back to UI for redesign.
    Transition(source=WorkflowState.CREATIVE_DIRECTOR_GATE,
               event=TransitionEvent.ADVANCE,
               target=WorkflowState.SECTION_COMPLETE, owner=None),
    Transition(source=WorkflowState.CREATIVE_DIRECTOR_GATE,
               event=TransitionEvent.REJECT,
               target=WorkflowState.UI, owner="senior_ui_designer"),
)

#: States from which no further transition is possible.
TERMINAL_STATES: frozenset[WorkflowState] = frozenset(
    {WorkflowState.SECTION_COMPLETE, WorkflowState.FAILED}
)


def next_states(source: WorkflowState) -> dict[TransitionEvent, Transition]:
    """Return the legal transitions out of `source`, keyed by event.

    A ``FAIL`` event is legal from *any* non-terminal state and is synthesized
    here rather than enumerated in :data:`TRANSITIONS`, since failure handling
    is uniform across the pipeline.
    """
    result: dict[TransitionEvent, Transition] = {
        t.event: t for t in TRANSITIONS if t.source is source
    }
    if source not in TERMINAL_STATES:
        result.setdefault(
            TransitionEvent.FAIL,
            Transition(
                source=source,
                event=TransitionEvent.FAIL,
                target=WorkflowState.FAILED,
                owner=None,
            ),
        )
    return result


# --------------------------------------------------------------------------- #
# The persisted run record (mirrored by the ORM model in apps/api/db/models.py).
# --------------------------------------------------------------------------- #
class TransitionRecord(BaseModel):
    """One immutable entry in a run's audit trail.

    The sequence of these is the answer to *"why did the Creative Director
    reject this?"* — each rejection is recorded with its notes.
    """

    from_state: WorkflowState
    event: TransitionEvent
    to_state: WorkflowState
    agent_role: str | None = None
    notes: list[str] = Field(default_factory=list)
    at: datetime | None = Field(
        default=None, description="Timestamp; set by the persistence layer."
    )


class RunRecord(BaseModel):
    """The full state of a design run for one section.

    This Pydantic model is the in-memory / API representation. The database
    stores the same fields (see the ORM model), and the state machine reads and
    writes instances of this type.
    """

    run_id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    section: str
    state: WorkflowState = WorkflowState.CREATED
    status: RunStatus = RunStatus.PENDING

    brief: dict[str, Any] = Field(default_factory=dict)
    #: Accumulated agent outputs, keyed by AgentRole value.
    artifacts: dict[str, Any] = Field(default_factory=dict)
    #: Full audit trail, append-only.
    history: list[TransitionRecord] = Field(default_factory=list)

    #: Count of Creative-Director rejections — surfaced for reporting and to let
    #: the orchestrator enforce a max-redesign guard rail in later phases.
    redesign_count: int = Field(default=0, ge=0)

    created_at: datetime | None = None
    updated_at: datetime | None = None

    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES
