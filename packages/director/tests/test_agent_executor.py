"""The Phase-1 agent-executor bridge.

Verifies that :class:`Phase1AgentExecutor` maps an application execution request
onto a Phase-1 ``AgentInput``, runs the agent via the Phase-1 registry, and maps
the ``AgentOutput`` back — the seam that keeps the Director independent of the
agent runtime (Principle P12 / ADR-0014).
"""

from __future__ import annotations

import uuid

from core.contracts.agent import AgentInput, AgentOutput, AgentRole, AgentStatus, BaseAgent
from orchestration.registry import AgentRegistry

from director.application.ports.agent_executor_port import (
    AgentExecutionRequest,
    ExecutionStatus,
)
from director.domain.shared.ids import RunId, SectionId
from director.infrastructure.orchestration.agent_executor import Phase1AgentExecutor


class _RecordingResearchAgent(BaseAgent):
    role = AgentRole.RESEARCH

    def __init__(self, context=None) -> None:
        super().__init__(context)
        self.seen: AgentInput | None = None

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        self.seen = agent_input
        return AgentOutput(
            role=self.role,
            status=AgentStatus.OK,
            artifact={"findings": ["a", "b"]},
            summary="did research",
            tokens_input=10,
            tokens_output=20,
        )


async def test_bridge_maps_request_and_result() -> None:
    registry = AgentRegistry()
    registry.register(_RecordingResearchAgent)
    executor = Phase1AgentExecutor(registry)

    request = AgentExecutionRequest(
        run_id=RunId.new(),
        tenant_id=uuid.uuid4(),
        section_id=SectionId.new(),
        section="hero",
        step_key="research",
        agent_role=AgentRole.RESEARCH,
        attempt=1,
        brief={"goal": "convert"},
    )
    result = await executor.execute(request)

    assert result.status is ExecutionStatus.OK
    assert result.artifact["findings"] == ["a", "b"]
    assert result.tokens_input == 10 and result.tokens_output == 20

    # The request was faithfully mapped onto the Phase-1 AgentInput.
    agent = registry.get(AgentRole.RESEARCH)
    assert agent.seen is not None
    assert agent.seen.section == "hero"
    assert agent.seen.brief == {"goal": "convert"}
    assert agent.seen.state.value == "research"  # step key mapped to WorkflowState
