"""Agent executor adapter — bridges the Director to the Phase-1 agent runtime.

This is the concrete implementation of
:class:`~director.application.ports.agent_executor_port.AgentExecutorPort`. It is
the *only* place the Director's world meets the Phase-1 agent runtime: it maps an
application :class:`AgentExecutionRequest` onto a Phase-1 ``AgentInput``, invokes
the agent through the Phase-1 ``AgentRegistry`` (reused unmodified), and maps the
returned ``AgentOutput`` back into an application :class:`AgentExecutionResult`.

Because this mapping lives here — behind the port — the Director never imports
the agent runtime, an LLM SDK, or MCP. Extracting an agent into its own service
later (Principle P12 / ADR-0014) means writing a *different* adapter for this same
port; nothing in the application changes.

The Phase-1 ``AgentInput`` requires a ``WorkflowState`` for its ``state`` field.
The section-design workflow's step keys were deliberately chosen to equal the
Phase-1 ``WorkflowState`` values, so the mapping is a direct lookup; a step whose
key has no matching state (it would not be an agent step in the section pipeline)
falls back to ``WorkflowState.CREATED``.
"""

from __future__ import annotations

from core.contracts.agent import AgentInput, AgentStatus
from core.contracts.workflow import WorkflowState

from director.application.ports.agent_executor_port import (
    AgentExecutionRequest,
    AgentExecutionResult,
    ExecutionStatus,
)

__all__ = ["Phase1AgentExecutor"]

# Map the Phase-1 agent self-assessment onto the application's execution status.
_STATUS_MAP: dict[AgentStatus, ExecutionStatus] = {
    AgentStatus.OK: ExecutionStatus.OK,
    AgentStatus.REJECTED: ExecutionStatus.REJECTED,
    AgentStatus.NEEDS_INPUT: ExecutionStatus.NEEDS_INPUT,
    AgentStatus.FAILED: ExecutionStatus.FAILED,
}


class Phase1AgentExecutor:
    """Runs agents via the Phase-1 registry, behind the AgentExecutorPort.

    The registry is injected (it is the Phase-1
    ``orchestration.registry.AgentRegistry``), so which concrete agents exist is a
    wiring decision, not this adapter's concern.
    """

    def __init__(self, registry: object) -> None:
        # Typed as object to avoid a hard import of the Phase-1 registry class in
        # signatures; duck-typed usage is `registry.get(role) -> BaseAgent`.
        self._registry = registry

    async def execute(self, request: AgentExecutionRequest) -> AgentExecutionResult:
        """Run the requested step's agent and normalise the result."""
        agent = self._registry.get(request.agent_role)  # type: ignore[attr-defined]

        agent_input = AgentInput(
            run_id=request.run_id.value,
            tenant_id=request.tenant_id,
            section=request.section or str(request.section_id),
            state=self._to_workflow_state(request.step_key),
            brief=dict(request.brief),
            artifacts=dict(request.artifacts),
            revision_notes=list(request.revision_notes),
        )

        output = await agent.run(agent_input)

        return AgentExecutionResult(
            status=_STATUS_MAP[output.status],
            summary=output.summary,
            artifact=dict(output.artifact),
            revision_notes=tuple(output.revision_notes),
            error=output.error,
            model=output.model,
            tokens_input=output.tokens_input,
            tokens_output=output.tokens_output,
        )

    @staticmethod
    def _to_workflow_state(step_key: str) -> WorkflowState:
        """Map a step key to a Phase-1 ``WorkflowState``, defaulting to CREATED."""
        try:
            return WorkflowState(step_key)
        except ValueError:
            return WorkflowState.CREATED
