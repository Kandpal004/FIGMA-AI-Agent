"""The agent contract.

Every specialist in the platform — Research Agent, UX Architect, Creative
Director, QA Agent, and the rest — is a subclass of :class:`BaseAgent` that
implements a single coroutine::

    async def run(self, agent_input: AgentInput) -> AgentOutput

That is the *entire* surface an agent exposes to the rest of the system. The
consequences of keeping it this small are the whole point:

* **Agents are pure with respect to orchestration.** They receive an
  :class:`AgentInput`, return an :class:`AgentOutput`, and never reach out to
  another agent. Coordination is the mediator's job, not theirs.
* **Agents are hot-swappable.** Because the orchestrator depends only on this
  contract, any agent can be reimplemented (different prompt, different model,
  different tooling) without touching a line of orchestration code.
* **Agents are trivially testable.** No FastAPI, no database — construct an
  :class:`AgentInput`, ``await agent.run(...)``, assert on the
  :class:`AgentOutput`.

Nothing in this module imports the LLM client, the database, or any tool. Those
are injected via :class:`AgentContext` so that the contract stays a pure data +
interface definition.
"""

from __future__ import annotations

import abc
from enum import Enum
from typing import Any, Protocol, runtime_checkable
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from core.contracts.workflow import WorkflowState


class AgentRole(str, Enum):
    """The canonical roster of specialist agents.

    The value is the stable identifier used in the registry, in persisted run
    records, and in logs. Adding an agent to the platform starts by adding a
    member here.
    """

    RESEARCH = "research"
    BUSINESS_ANALYST = "business_analyst"
    UX_ARCHITECT = "ux_architect"
    INFORMATION_ARCHITECT = "information_architect"
    SENIOR_UI_DESIGNER = "senior_ui_designer"
    CREATIVE_DIRECTOR = "creative_director"
    DESIGN_SYSTEM_ARCHITECT = "design_system_architect"
    TYPOGRAPHY_EXPERT = "typography_expert"
    COLOR_EXPERT = "color_expert"
    ACCESSIBILITY_EXPERT = "accessibility_expert"
    CRO_EXPERT = "cro_expert"
    PERFORMANCE_EXPERT = "performance_expert"
    SEO_EXPERT = "seo_expert"
    SHOPIFY_PLUS_ARCHITECT = "shopify_plus_architect"
    MAGENTO_ARCHITECT = "magento_architect"
    FRONTEND_ARCHITECT = "frontend_architect"
    REVIEWER = "reviewer"
    QA = "qa"
    MEMORY = "memory"


class AgentStatus(str, Enum):
    """Outcome of a single agent run, as reported by the agent itself.

    This is the agent's *self-assessment*. The mediator maps it onto a workflow
    :class:`~core.contracts.workflow.TransitionEvent` — e.g. a reviewer or the
    Creative Director returning ``REJECTED`` triggers a redesign loop.
    """

    OK = "ok"
    """Work completed; the pipeline may advance."""

    REJECTED = "rejected"
    """A gatekeeper (Reviewer / Creative Director) vetoed the current artifact.
    Carries `revision_notes` explaining what must change."""

    NEEDS_INPUT = "needs_input"
    """The agent cannot proceed without additional information (from a human or
    an upstream agent)."""

    FAILED = "failed"
    """The agent could not complete due to an error. `error` is populated."""


# --------------------------------------------------------------------------- #
# Data carried across the contract boundary
# --------------------------------------------------------------------------- #
class AgentInput(BaseModel):
    """Everything an agent needs to do its job, and nothing else.

    The `brief` and `artifacts` are the substance; the identifiers give the
    agent enough context to write good logs and to tag anything it persists to
    memory. Agents must treat this object as read-only.
    """

    model_config = ConfigDict(frozen=True)

    run_id: UUID = Field(description="The design run this invocation belongs to.")
    tenant_id: UUID = Field(description="Owning tenant — every artifact is scoped to it.")
    section: str = Field(
        description="The page section under design, e.g. 'hero', 'pdp', 'cart'."
    )
    state: WorkflowState = Field(
        description="The workflow state that triggered this agent."
    )

    brief: dict[str, Any] = Field(
        default_factory=dict,
        description="The design brief / requirements relevant to this section.",
    )
    artifacts: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Outputs from upstream agents this agent may consume, keyed by "
            "producing AgentRole value (e.g. {'ux_architect': {...}})."
        ),
    )
    revision_notes: list[str] = Field(
        default_factory=list,
        description=(
            "Present when re-running after a rejection: the specific changes the "
            "Reviewer or Creative Director demanded."
        ),
    )


class AgentOutput(BaseModel):
    """The result of an agent run.

    The mediator inspects `status` to decide the next transition and merges
    `artifact` into the run's accumulating artifact set under the agent's role.
    """

    model_config = ConfigDict(frozen=True)

    output_id: UUID = Field(default_factory=uuid4)
    role: AgentRole = Field(description="Which agent produced this output.")
    status: AgentStatus = Field(description="The agent's self-assessed outcome.")

    artifact: dict[str, Any] = Field(
        default_factory=dict,
        description="The structured work product (spec, tokens, report, ...).",
    )
    summary: str = Field(
        default="",
        description="One-paragraph human-readable summary for the run timeline.",
    )
    revision_notes: list[str] = Field(
        default_factory=list,
        description=(
            "When status is REJECTED: the concrete changes required. When OK: "
            "optional advisory notes for downstream agents."
        ),
    )
    error: str | None = Field(
        default=None, description="Populated only when status is FAILED."
    )

    # Bookkeeping for cost/latency observability.
    model: str | None = Field(default=None, description="LLM model used, if any.")
    tokens_input: int = Field(default=0, ge=0)
    tokens_output: int = Field(default=0, ge=0)

    def is_terminal_failure(self) -> bool:
        return self.status is AgentStatus.FAILED


# --------------------------------------------------------------------------- #
# Dependency injection surface
# --------------------------------------------------------------------------- #
@runtime_checkable
class LLMPort(Protocol):
    """The slice of the LLM client an agent is allowed to use.

    Declaring a Protocol here (rather than importing the concrete client) keeps
    `core.contracts` free of provider dependencies and lets tests pass a fake.
    The concrete implementation lives in :mod:`core.llm.client`.
    """

    async def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        model: str | None = ...,
        max_tokens: int | None = ...,
    ) -> Any: ...


class AgentContext(BaseModel):
    """Injected capabilities an agent may use during a run.

    Passed to :class:`BaseAgent` at construction time — not part of the
    stateless input — because these are process-level dependencies (clients,
    tools) rather than per-invocation data. Kept as an explicit object so an
    agent's dependencies are visible and mockable.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    llm: LLMPort | None = Field(
        default=None, description="LLM client. None in tests that don't need it."
    )
    tools: dict[str, Any] = Field(
        default_factory=dict,
        description="Named tool adapters (MCP/Figma, Shopify, memory) by key.",
    )


# --------------------------------------------------------------------------- #
# The base class
# --------------------------------------------------------------------------- #
class BaseAgent(abc.ABC):
    """Abstract base for every specialist agent.

    Subclasses declare their :attr:`role` and implement :meth:`run`. The
    constructor takes an :class:`AgentContext` so dependencies are explicit and
    swappable::

        class ResearchAgent(BaseAgent):
            role = AgentRole.RESEARCH

            async def run(self, agent_input: AgentInput) -> AgentOutput:
                ...
    """

    #: The role this agent fills. Subclasses MUST override.
    role: AgentRole

    def __init__(self, context: AgentContext | None = None) -> None:
        if not hasattr(type(self), "role"):
            raise TypeError(
                f"{type(self).__name__} must set a class-level `role: AgentRole`."
            )
        self.context = context or AgentContext()

    @abc.abstractmethod
    async def run(self, agent_input: AgentInput) -> AgentOutput:
        """Execute this agent's work for a single invocation.

        Implementations must be idempotent with respect to `agent_input`
        (re-running with the same input should produce equivalent output) and
        must never mutate the input. They must return an :class:`AgentOutput`
        whose ``role`` equals :attr:`role`; raising is reserved for truly
        unexpected failures — expected problems should be reported via
        ``status=FAILED`` with a populated ``error``.
        """
        raise NotImplementedError

    # Convenience builders so subclasses report results consistently. -------- #
    def _ok(self, agent_input: AgentInput, artifact: dict[str, Any], summary: str = "") -> AgentOutput:
        return AgentOutput(
            role=self.role, status=AgentStatus.OK, artifact=artifact, summary=summary
        )

    def _rejected(self, revision_notes: list[str], summary: str = "") -> AgentOutput:
        return AgentOutput(
            role=self.role,
            status=AgentStatus.REJECTED,
            revision_notes=revision_notes,
            summary=summary,
        )

    def _failed(self, error: str) -> AgentOutput:
        return AgentOutput(role=self.role, status=AgentStatus.FAILED, error=error)
