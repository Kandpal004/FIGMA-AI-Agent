# ADR-0003: Mediator orchestration — agents never call agents

**Status:** Accepted · **Date:** 2026-07-13

## Context

The most common failure mode of multi-agent systems is agents invoking each
other directly. The result is an implicit, ever-growing dependency graph that
nobody can reason about, test in isolation, or reorder without breakage.

## Decision

Adopt the **mediator pattern**. A single `Mediator` owns the run loop and is the
only component that invokes agents. Agents return an `AgentOutput`; the mediator
translates its status into a workflow event, applies the transition, persists,
and moves on. No agent imports or calls another agent.

## Consequences

- **+** The workflow lives in exactly one place (the transition graph + the
  loop), so it can be read, tested, and changed centrally.
- **+** Agents stay pure and independently testable.
- **+** Reordering the pipeline is a data change to the graph, not a code change
  across agents.
- **−** The mediator is a central component that must stay simple; complexity
  creep here would be costly. Kept small on purpose (~one loop).

## Alternatives considered

- **Direct agent-to-agent calls.** Rejected — the failure mode above.
- **Event bus / choreography.** Rejected for now: powerful but harder to audit
  and reason about than an explicit central loop; revisit if we need
  fan-out/parallel agent execution at scale.
