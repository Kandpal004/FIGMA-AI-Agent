"""The contracts every agent and the orchestrator obey.

These types are the load-bearing interfaces of the whole platform. They are
deliberately small and framework-free so that:

* an agent can be unit-tested with plain dicts, no database, no HTTP;
* an agent can be swapped for another implementation without touching the
  orchestrator;
* the orchestrator can route between agents knowing only these shapes.
"""

from core.contracts.agent import (
    AgentContext,
    AgentInput,
    AgentOutput,
    AgentRole,
    AgentStatus,
    BaseAgent,
)
from core.contracts.workflow import (
    RunRecord,
    RunStatus,
    TERMINAL_STATES,
    TRANSITIONS,
    Transition,
    TransitionEvent,
    WorkflowState,
    next_states,
)

__all__ = [
    "TERMINAL_STATES",
    "TRANSITIONS",
    "AgentContext",
    "AgentInput",
    "AgentOutput",
    "AgentRole",
    "AgentStatus",
    "BaseAgent",
    "RunRecord",
    "RunStatus",
    "Transition",
    "TransitionEvent",
    "WorkflowState",
    "next_states",
]
