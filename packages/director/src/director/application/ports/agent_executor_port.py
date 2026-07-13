"""Agent executor port — the single seam through which agents run.

The Director decides *what* to run; this port is *how* one step's agent is
actually executed. The infrastructure adapter behind it builds a Phase-1
``AgentInput``, invokes the agent via the Phase-1 registry, and maps the result
back into the application-owned :class:`AgentExecutionResult`. Because the
application depends only on this Protocol — never on the concrete agent runtime,
an LLM SDK, or MCP — an agent can later be extracted into its own service by
swapping the adapter, with zero change here (Principle P12 / ADR-0014).

The Director never sees a Phase-1 ``AgentOutput``; it sees an
:class:`AgentExecutionResult` and interprets its :class:`ExecutionStatus` into a
step-state transition.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from core.contracts.agent import AgentRole

from director.domain.project.entities import ProjectContext
from director.domain.shared.ids import RunId, SectionId

__all__ = [
    "AgentExecutionRequest",
    "AgentExecutionResult",
    "AgentExecutorPort",
    "ExecutionStatus",
]


class ExecutionStatus(str, Enum):
    """The outcome an agent reports for a single execution.

    Application-owned mirror of the agent runtime's status, so the Director does
    not depend on the runtime's own enum. The Director maps these onto step-state
    transitions:

    * ``OK``          → the step completes (or, for a gate, awaits approval).
    * ``REJECTED``    → the gate vetoed; roll back.
    * ``NEEDS_INPUT`` → the step blocks; the run pauses.
    * ``FAILED``      → retry if attempts remain, else fail.
    """

    OK = "ok"
    REJECTED = "rejected"
    NEEDS_INPUT = "needs_input"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class AgentExecutionRequest:
    """Everything the executor needs to run one step's agent.

    Assembled by the Director from the run, the step spec, and the project
    context. Immutable — the executor must not need to mutate it.

    Attributes:
        run_id: The run this execution belongs to.
        tenant_id: Owning tenant (for scoping anything the agent persists).
        section_id: The section under design.
        section: The section's human key (e.g. ``"hero"``); ``""`` if unresolved.
        step_key: The step being executed.
        agent_role: The agent responsible.
        attempt: The 1-based attempt number.
        brief: The design brief / requirements for this section.
        artifacts: Outputs from upstream steps, keyed by producing step/role.
        revision_notes: On a redesign, the changes a gate demanded.
        context: The memory snapshot the agent may reason over.
    """

    run_id: RunId
    tenant_id: uuid.UUID
    section_id: SectionId
    step_key: str
    agent_role: AgentRole
    attempt: int
    section: str = ""
    brief: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    artifacts: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    revision_notes: tuple[str, ...] = ()
    context: ProjectContext | None = None


@dataclass(frozen=True, slots=True)
class AgentExecutionResult:
    """The normalized outcome of an agent execution.

    Attributes:
        status: The reported :class:`ExecutionStatus`.
        summary: One-line human summary for the run timeline.
        artifact: The structured work product (read-only).
        revision_notes: On rejection, the concrete changes required.
        error: Populated only when ``status`` is ``FAILED``.
        model: The LLM model used, if any.
        tokens_input: Input tokens consumed (observability).
        tokens_output: Output tokens produced (observability).
    """

    status: ExecutionStatus
    summary: str = ""
    artifact: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))
    revision_notes: tuple[str, ...] = ()
    error: str | None = None
    model: str | None = None
    tokens_input: int = 0
    tokens_output: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.artifact, MappingProxyType):
            object.__setattr__(self, "artifact", MappingProxyType(dict(self.artifact)))
        if not isinstance(self.revision_notes, tuple):
            object.__setattr__(self, "revision_notes", tuple(self.revision_notes))


@runtime_checkable
class AgentExecutorPort(Protocol):
    """Executes a single agent step and returns its normalized result."""

    async def execute(self, request: AgentExecutionRequest) -> AgentExecutionResult:
        """Run the step's agent to completion and return the outcome.

        Implementations must not raise for *expected* agent failures — those are
        reported via ``status=FAILED`` with an ``error``. Raising is reserved for
        infrastructure faults (e.g. the agent runtime being unreachable).
        """
        ...
