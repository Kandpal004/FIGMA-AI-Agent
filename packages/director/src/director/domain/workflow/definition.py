"""Immutable workflow *templates* — the plan, expressed as data.

A :class:`WorkflowDefinition` is a declarative, versioned description of *what*
steps a workflow contains, in *what* order, and with *what* policies (retry,
rollback, approval). It contains **no control-flow code**: it is pure data the
Workflow Engine interprets at run time. This is Principle P9/P10 made concrete —
business logic lives in the engine and in configuration like this, never buried
in prompts or scattered through imperative code.

The model is the approved **two-tier** design:

* A **SECTION** definition describes the inner design pipeline for a single
  section — a sequence of agent steps and review/approval gates (research → … →
  creative-director gate).
* A **PAGE** definition describes which sections a page comprises; its steps are
  *composite*, each spawning a section run.

Both tiers are the same shape (:class:`WorkflowDefinition`), which is why one
engine can drive both.

Relationship to the state machine
---------------------------------
This module owns the *position* graph — "which step comes after which". It is
orthogonal to :mod:`director.domain.state`, which owns each step's *lifecycle*
(pending → running → …). A running workflow combines the two: the definition
says where to go next; the state machine says whether a given step may move.

Concrete definitions (the actual section pipeline, the homepage page workflow,
…) are assembled in the workflow *catalog*; this module only provides the types
and their behaviour, holding no concrete instances and performing no I/O.

Testing considerations
----------------------
* Navigation (:meth:`WorkflowDefinition.next_step`, ``previous_step``,
  ``first_step``, ``index_of``, ``get_step``) is exact and raises
  :class:`StepNotFoundError` for unknown keys.
* Every construction-time invariant rejects bad input with
  :class:`InvalidWorkflowDefinitionError`: duplicate keys, empty step lists,
  version ``< 1``, page/section–page_type mismatch, an ``AGENT`` step without a
  role, a ``COMPOSITE`` step without a ``spawns`` target, a manual approval on a
  non-gate step, a rollback on a non-gate step, and any rollback that would
  rewind to a non-existent, later, or before-the-start step.
* :meth:`WorkflowDefinition.resolve_rollback` maps a gate's target-agnostic
  :class:`RollbackPolicy` onto a concrete earlier step.
* Definitions and step specs are frozen (immutable).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum

from core.contracts.agent import AgentRole
from core.errors import DesignDirectorError

from director.domain.shared.value_objects import (
    ApprovalPolicy,
    PageType,
    Priority,
    RetryPolicy,
    RollbackPolicy,
    RollbackStrategy,
    WorkflowType,
)

__all__ = [
    "InvalidWorkflowDefinitionError",
    "StepKind",
    "StepNotFoundError",
    "WorkflowDefinition",
    "WorkflowStepSpec",
]


# --------------------------------------------------------------------------- #
# Domain exceptions
# --------------------------------------------------------------------------- #
class InvalidWorkflowDefinitionError(DesignDirectorError):
    """Raised when a workflow definition or step spec is structurally invalid."""

    code = "invalid_workflow_definition"
    http_status = 422


class StepNotFoundError(DesignDirectorError):
    """Raised when a step is requested by a key not present in the definition."""

    code = "step_not_found"
    http_status = 404


# --------------------------------------------------------------------------- #
# Step kind
# --------------------------------------------------------------------------- #
class StepKind(str, Enum):
    """What a workflow step executes.

    * :data:`AGENT`     — a leaf step performed by a single agent (identified by
      its :class:`~core.contracts.agent.AgentRole`).
    * :data:`COMPOSITE` — a step that spawns a sub-workflow run (e.g. a page
      step that spawns a section design), identified by ``spawns`` — the key of
      the definition to run. This is the seam for the two-tier model.
    """

    AGENT = "agent"
    COMPOSITE = "composite"


# --------------------------------------------------------------------------- #
# Step spec
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class WorkflowStepSpec:
    """The immutable specification of one step in a workflow definition.

    Attributes:
        key: Stable, unique-within-definition identifier (e.g. ``"ui"``,
            ``"cd_gate"``). Non-empty.
        title: Human-readable label. Falls back to ``key`` via :attr:`label`.
        kind: :class:`StepKind` — an agent leaf or a composite sub-workflow.
        agent_role: The agent responsible; required iff ``kind is AGENT`` and
            forbidden otherwise.
        spawns: The definition key to run; required iff ``kind is COMPOSITE`` and
            forbidden otherwise.
        is_gate: Whether this step is an approval gate that can approve or reject.
        approval: How the gate is approved. Non-gate steps must use automatic
            approval (a non-gate cannot require a human sign-off).
        retry: The retry policy for this step's execution.
        rollback: What happens on rejection. Only gates may rewind; the policy is
            target-agnostic and resolved against the owning definition.
        priority: Scheduling priority.
        description: Optional free-text description.
    """

    key: str
    title: str = ""
    kind: StepKind = StepKind.AGENT
    agent_role: AgentRole | None = None
    spawns: str | None = None
    is_gate: bool = False
    approval: ApprovalPolicy = field(default_factory=ApprovalPolicy.automatic)
    retry: RetryPolicy = field(default_factory=RetryPolicy.none)
    rollback: RollbackPolicy = field(default_factory=RollbackPolicy.none)
    priority: Priority = Priority.NORMAL
    description: str = ""

    def __post_init__(self) -> None:
        if not self.key or not self.key.strip():
            raise InvalidWorkflowDefinitionError("WorkflowStepSpec.key must be non-empty.")

        if self.kind is StepKind.AGENT:
            if self.agent_role is None:
                raise InvalidWorkflowDefinitionError(
                    "An AGENT step requires an agent_role.",
                    details={"step": self.key},
                )
            if self.spawns is not None:
                raise InvalidWorkflowDefinitionError(
                    "An AGENT step must not set 'spawns'.",
                    details={"step": self.key},
                )
        else:  # COMPOSITE
            if not self.spawns:
                raise InvalidWorkflowDefinitionError(
                    "A COMPOSITE step requires a 'spawns' definition key.",
                    details={"step": self.key},
                )
            if self.agent_role is not None:
                raise InvalidWorkflowDefinitionError(
                    "A COMPOSITE step must not set an agent_role.",
                    details={"step": self.key},
                )

        if not self.is_gate and self.approval.requires_human:
            raise InvalidWorkflowDefinitionError(
                "A non-gate step cannot require human approval.",
                details={"step": self.key},
            )

        if self.rollback.rewinds and not self.is_gate:
            raise InvalidWorkflowDefinitionError(
                "Only gate steps may define a rewinding rollback policy.",
                details={"step": self.key},
            )

    @property
    def label(self) -> str:
        """The human label, falling back to :attr:`key` when ``title`` is empty."""
        return self.title or self.key


# --------------------------------------------------------------------------- #
# Workflow definition
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    """An immutable, versioned workflow template: an ordered plan of steps.

    The ``steps`` tuple is the linear happy path. Back-edges (a gate rejecting
    and rewinding) are expressed by each gate's :class:`RollbackPolicy` and
    resolved by :meth:`resolve_rollback`, so the definition stays a simple,
    declarative sequence rather than a hand-maintained graph.

    Definitions are **immutable and versioned**: a change is a new version (a new
    object), never a mutation — which is what makes prompts/plans-as-config
    safely rollback-able (Principle P10).

    Attributes:
        key: Stable identifier for this workflow (e.g. ``"section_design"``).
        name: Human-readable name.
        workflow_type: PAGE or SECTION (the two-tier model).
        steps: Ordered, non-empty tuple of :class:`WorkflowStepSpec`.
        version: Monotonic version (``>= 1``).
        page_type: The page this designs — required for PAGE workflows and
            forbidden for SECTION workflows.
        description: Optional free-text description.
    """

    key: str
    name: str
    workflow_type: WorkflowType
    steps: tuple[WorkflowStepSpec, ...]
    version: int = 1
    page_type: PageType | None = None
    description: str = ""

    def __post_init__(self) -> None:
        # Normalise any sequence of steps into a tuple (immutability).
        if not isinstance(self.steps, tuple):
            object.__setattr__(self, "steps", tuple(self.steps))

        if not self.key or not self.key.strip():
            raise InvalidWorkflowDefinitionError("WorkflowDefinition.key must be non-empty.")
        if not self.name or not self.name.strip():
            raise InvalidWorkflowDefinitionError("WorkflowDefinition.name must be non-empty.")
        if self.version < 1:
            raise InvalidWorkflowDefinitionError(
                "WorkflowDefinition.version must be >= 1.",
                details={"version": self.version},
            )
        if not self.steps:
            raise InvalidWorkflowDefinitionError(
                "WorkflowDefinition must contain at least one step.",
                details={"workflow": self.key},
            )

        # Unique step keys.
        seen: set[str] = set()
        for step in self.steps:
            if step.key in seen:
                raise InvalidWorkflowDefinitionError(
                    "Duplicate step key in workflow definition.",
                    details={"workflow": self.key, "step": step.key},
                )
            seen.add(step.key)

        # Page/section vs page_type consistency.
        if self.workflow_type is WorkflowType.PAGE and self.page_type is None:
            raise InvalidWorkflowDefinitionError(
                "A PAGE workflow must specify a page_type.",
                details={"workflow": self.key},
            )
        if self.workflow_type is WorkflowType.SECTION and self.page_type is not None:
            raise InvalidWorkflowDefinitionError(
                "A SECTION workflow must not specify a page_type.",
                details={"workflow": self.key},
            )

        self._validate_rollback_targets()

    # -- validation helper ------------------------------------------------- #
    def _validate_rollback_targets(self) -> None:
        """Ensure every rollback resolves to a real, earlier step."""
        index_by_key = {step.key: i for i, step in enumerate(self.steps)}
        for i, step in enumerate(self.steps):
            policy = step.rollback
            if not policy.rewinds:
                continue
            strategy = policy.strategy
            if strategy is RollbackStrategy.TO_TARGET:
                target = policy.target
                if target not in index_by_key:
                    raise InvalidWorkflowDefinitionError(
                        "Rollback target does not exist in the workflow.",
                        details={"workflow": self.key, "step": step.key, "target": target},
                    )
                if index_by_key[target] >= i:  # type: ignore[index]  # target is not None here
                    raise InvalidWorkflowDefinitionError(
                        "Rollback target must be an earlier step.",
                        details={"workflow": self.key, "step": step.key, "target": target},
                    )
            elif strategy is RollbackStrategy.STEPS_BACK:
                if policy.steps_back > i:
                    raise InvalidWorkflowDefinitionError(
                        "Rollback would rewind before the first step.",
                        details={
                            "workflow": self.key,
                            "step": step.key,
                            "steps_back": policy.steps_back,
                            "index": i,
                        },
                    )
            else:  # PREVIOUS or RESTART
                if i == 0:
                    raise InvalidWorkflowDefinitionError(
                        "The first step cannot define a rewinding rollback.",
                        details={"workflow": self.key, "step": step.key},
                    )

    # -- navigation -------------------------------------------------------- #
    def __len__(self) -> int:
        return len(self.steps)

    def step_keys(self) -> tuple[str, ...]:
        """The ordered tuple of step keys."""
        return tuple(step.key for step in self.steps)

    def has_step(self, key: str) -> bool:
        """Whether a step with ``key`` exists."""
        return any(step.key == key for step in self.steps)

    def get_step(self, key: str) -> WorkflowStepSpec:
        """Return the step with ``key``.

        Raises:
            StepNotFoundError: If no such step exists.
        """
        for step in self.steps:
            if step.key == key:
                return step
        raise StepNotFoundError(
            f"Step {key!r} not found in workflow {self.key!r}.",
            details={"workflow": self.key, "step": key},
        )

    def index_of(self, key: str) -> int:
        """Return the zero-based position of ``key``.

        Raises:
            StepNotFoundError: If no such step exists.
        """
        for i, step in enumerate(self.steps):
            if step.key == key:
                return i
        raise StepNotFoundError(
            f"Step {key!r} not found in workflow {self.key!r}.",
            details={"workflow": self.key, "step": key},
        )

    def step_at(self, index: int) -> WorkflowStepSpec:
        """Return the step at ``index``.

        Raises:
            StepNotFoundError: If ``index`` is out of range.
        """
        if not 0 <= index < len(self.steps):
            raise StepNotFoundError(
                f"Step index {index} out of range for workflow {self.key!r}.",
                details={"workflow": self.key, "index": index, "length": len(self.steps)},
            )
        return self.steps[index]

    @property
    def first_step(self) -> WorkflowStepSpec:
        """The first step in the plan."""
        return self.steps[0]

    @property
    def last_step(self) -> WorkflowStepSpec:
        """The last step in the plan."""
        return self.steps[-1]

    def is_last(self, key: str) -> bool:
        """Whether ``key`` is the final step."""
        return self.index_of(key) == len(self.steps) - 1

    def next_step(self, after_key: str) -> WorkflowStepSpec | None:
        """The step following ``after_key`` on the happy path, or ``None`` if it
        is the last step."""
        idx = self.index_of(after_key)
        if idx + 1 >= len(self.steps):
            return None
        return self.steps[idx + 1]

    def previous_step(self, before_key: str) -> WorkflowStepSpec | None:
        """The step preceding ``before_key``, or ``None`` if it is the first."""
        idx = self.index_of(before_key)
        if idx == 0:
            return None
        return self.steps[idx - 1]

    def gates(self) -> tuple[WorkflowStepSpec, ...]:
        """All gate steps, in order."""
        return tuple(step for step in self.steps if step.is_gate)

    def resolve_rollback(self, step_key: str) -> WorkflowStepSpec | None:
        """Resolve a gate's rollback policy to the concrete step to rewind to.

        Args:
            step_key: The gate step whose rollback policy to resolve.

        Returns:
            The earlier step to rewind to, or ``None`` if the step's policy does
            not rewind (:data:`RollbackStrategy.NONE`).

        Raises:
            StepNotFoundError: If ``step_key`` is unknown.

        The target is guaranteed to exist and precede the gate, because
        construction validated every rollback policy against the plan.
        """
        step = self.get_step(step_key)
        policy = step.rollback
        if not policy.rewinds:
            return None

        if policy.strategy is RollbackStrategy.TO_TARGET:
            # `target` verified present and earlier at construction time.
            assert policy.target is not None
            return self.get_step(policy.target)

        idx = self.index_of(step_key)
        if policy.strategy is RollbackStrategy.PREVIOUS:
            target_index = idx - 1
        elif policy.strategy is RollbackStrategy.STEPS_BACK:
            target_index = idx - policy.steps_back
        else:  # RESTART
            target_index = 0
        return self.steps[target_index]
