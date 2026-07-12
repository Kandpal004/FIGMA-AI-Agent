# ADR-0014: Agents are service-ready, run as a modular monolith

**Status:** Accepted · **Date:** 2026-07-13
**Serves principle:** P12 (agents are independent services), interpreted.

## Context

P12 states "agents are independent services." Taken literally as *"stand up 20
microservices now,"* that would impose network calls, serialization, service
discovery, distributed tracing, and independent deploy pipelines on a system that
has exactly zero measured need for them. That is textbook premature
distribution — paying the highest-cost architecture's tax with none of its
benefit, and slowing every early phase.

## Decision

Interpret P12 as **service-ready, not prematurely distributed**:

- **Design** every agent so it can be extracted into its own independently
  deployable, independently scalable service with **zero changes to its
  contract.**
- **Run** all agents in-process as a **modular monolith** until measured scale
  (throughput, isolation, or independent-scaling needs) justifies extraction.

The properties that make extraction a non-event are enforced now:

1. **Transport-agnostic contract** — typed JSON `AgentInput`/`AgentOutput`; the
   same bytes cross a function call today or an HTTP/queue boundary tomorrow.
2. **No shared mutable state** between agents; all data flows through the
   contract and the mediator.
3. **Dependencies injected** via `AgentContext` — an extracted agent gets its
   LLM/tools the same way.
4. **Communication only through the mediator** — never agent-to-agent, so there
   is never a hidden in-process call to sever.

Extraction later is: wrap an already-isolated `run()` in a thin HTTP/queue server,
point the registry at a remote proxy. No agent logic changes.

## Consequences

- **+** Full early velocity — no distributed-systems tax before it pays for itself.
- **+** Extraction is a mechanical, low-risk operation when the day comes.
- **+** We can extract *selectively* (e.g. only the GPU-heavy or slowest agent).
- **−** We forgo independent per-agent deploys until extraction — accepted; not a
  need at this stage.

## Revisit when

Any of: an agent needs independent scaling; an agent needs a runtime the monolith
can't host; team/deploy isolation becomes a bottleneck; or per-agent fault
isolation becomes a requirement. At that point, extract that agent — the contract
already permits it. This ADR is superseded per-agent, not wholesale.
