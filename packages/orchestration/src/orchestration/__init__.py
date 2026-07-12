"""The orchestration core — the platform's "Design Director".

Three collaborating pieces, each with one job:

* :mod:`orchestration.registry`      — knows which agent class fills each role.
* :mod:`orchestration.state_machine` — knows the legal moves and records every one.
* :mod:`orchestration.mediator`      — runs the loop: pick the owning agent for the
  current state, invoke it, translate its result into a transition, advance,
  repeat until the section completes or fails.

The mediator is the *only* component that invokes agents. Agents never invoke
each other; this is what keeps a 20-agent system comprehensible.
"""

from orchestration.mediator import InMemoryRunStore, Mediator, RunStore
from orchestration.registry import AgentRegistry
from orchestration.state_machine import StateMachine

__all__ = [
    "AgentRegistry",
    "InMemoryRunStore",
    "Mediator",
    "RunStore",
    "StateMachine",
]
