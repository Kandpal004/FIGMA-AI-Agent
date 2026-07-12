# ADR-0002: A single `run(AgentInput) -> AgentOutput` agent contract

**Status:** Accepted · **Date:** 2026-07-13

## Context

Twenty specialist agents will be built over many phases, by different people, at
different times. If each agent has a bespoke shape, the orchestrator accretes
special cases and the system becomes unmaintainable by agent number six.

## Decision

Every agent subclasses `BaseAgent` and implements exactly one coroutine:

```python
async def run(self, agent_input: AgentInput) -> AgentOutput
```

`AgentInput` and `AgentOutput` are frozen Pydantic models. Dependencies (LLM,
tools) are injected via an `AgentContext` at construction, not passed per call.
The LLM dependency is a `Protocol`, so `core.contracts` has no provider import.

## Consequences

- **+** Agents are unit-testable with plain objects — no FastAPI, no DB.
- **+** Agents are hot-swappable; the orchestrator depends only on the contract.
- **+** A uniform shape means the mediator has zero per-agent branching.
- **−** Some agents will feel "boxed" by a generic input/output — accepted; the
  `brief`/`artifacts`/`artifact` dicts give escape hatches without breaking the
  contract.

## Alternatives considered

- **Function-based agents (no base class).** Rejected: no shared helpers, no
  enforced `role`, weaker discoverability.
- **Per-agent typed I/O models.** Rejected for the orchestration boundary: the
  mediator would need to know each agent's types. Agents may still validate their
  own `artifact` internally.
