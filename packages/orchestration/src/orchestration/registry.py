"""The agent registry.

Maps each :class:`~core.contracts.agent.AgentRole` to the concrete
:class:`~core.contracts.agent.BaseAgent` subclass that fills it, and constructs
instances on demand with a shared :class:`~core.contracts.agent.AgentContext`.

This is the seam that makes agents pluggable: the mediator asks the registry for
"the agent that owns role X" and never names a concrete class. Swapping an
implementation, or A/B-testing two Creative Directors, is a registry change —
nothing in the orchestration loop moves.

In Phase 1 the registry is empty of real agents (they arrive in later phases).
It is fully functional now so the wiring is proven end-to-end.
"""

from __future__ import annotations

from core.contracts.agent import AgentContext, AgentRole, BaseAgent
from core.errors import UnknownAgentError
from core.logging import get_logger

log = get_logger(__name__)


class AgentRegistry:
    """A role → agent-class map with lazy, context-injected instantiation."""

    def __init__(self, context: AgentContext | None = None) -> None:
        self._context = context or AgentContext()
        self._classes: dict[AgentRole, type[BaseAgent]] = {}
        self._instances: dict[AgentRole, BaseAgent] = {}

    def register(self, agent_cls: type[BaseAgent]) -> type[BaseAgent]:
        """Register an agent class under its declared role.

        Usable as a decorator::

            @registry.register
            class ResearchAgent(BaseAgent):
                role = AgentRole.RESEARCH
                ...

        Raises:
            TypeError: if the class does not declare a `role`.
            ValueError: if the role is already registered.
        """
        role = getattr(agent_cls, "role", None)
        if not isinstance(role, AgentRole):
            raise TypeError(
                f"{agent_cls.__name__} must declare `role: AgentRole` to be registered."
            )
        if role in self._classes:
            raise ValueError(
                f"Role {role.value!r} already registered to "
                f"{self._classes[role].__name__}."
            )
        self._classes[role] = agent_cls
        log.info("agent registered", extra={"role": role.value, "cls": agent_cls.__name__})
        return agent_cls

    def is_registered(self, role: AgentRole) -> bool:
        return role in self._classes

    def get(self, role: AgentRole) -> BaseAgent:
        """Return a (cached) agent instance for `role`.

        Raises:
            UnknownAgentError: if no class is registered for the role.
        """
        if role not in self._classes:
            raise UnknownAgentError(
                f"No agent registered for role {role.value!r}.",
                details={"role": role.value, "known": [r.value for r in self._classes]},
            )
        if role not in self._instances:
            self._instances[role] = self._classes[role](self._context)
        return self._instances[role]

    def registered_roles(self) -> frozenset[AgentRole]:
        return frozenset(self._classes)
