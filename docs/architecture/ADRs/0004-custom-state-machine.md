# ADR-0004: Custom persisted state machine (not LangGraph or Temporal)

**Status:** Accepted · **Date:** 2026-07-13

## Context

The design pipeline is long-running, has review loops, and must answer *"why did
the Creative Director reject this?"* with a full audit trail. It must survive
crashes and pauses. We evaluated building on LangGraph, Temporal, or a custom
state machine.

## Decision

Build a **small, explicit state machine** whose transition graph is data in
`core.contracts.workflow` and whose executor (`orchestration.state_machine`) is
pure and I/O-free. Persist every transition to Postgres. We own the whole thing.

## Consequences

- **+** Total control over the Creative-Director veto loop, the audit trail, and
  resumability — all first-class, not bent to fit a framework's model.
- **+** The transition logic is trivially unit-testable (no infrastructure).
- **+** No heavy dependency whose abstractions leak into our domain.
- **−** We maintain code a framework would give us — accepted; the surface is
  small (a graph + a pure `apply()` + a loop) and directly serves our needs.
- **−** No built-in distributed durability like Temporal's — mitigated by
  persist-every-transition + `resume()`; revisit Temporal at scale (see below).

## Alternatives considered

- **LangGraph.** Faster to start, but the framework owns control flow and our
  custom audit/tenancy/veto semantics would be awkward bolt-ons.
- **Temporal.** Gold-standard durability, but a Temporal cluster is significant
  operational weight — overkill for the foundation. A candidate for a future ADR
  if/when we need cross-node durable execution at scale.
