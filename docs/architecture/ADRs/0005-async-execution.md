# ADR-0005: Redis + ARQ workers for long agent runs

**Status:** Accepted · **Date:** 2026-07-13

## Context

A full design run spans many agent invocations, each an LLM call of seconds to
minutes. A single run can take many minutes. Holding this inside an HTTP request
is untenable — timeouts, no resumability, blocked workers.

## Decision

Run the mediator loop in **background workers** backed by **Redis** as the queue.
Use **ARQ** (asyncio-native, minimal) as the job runner. The API enqueues a run
and returns immediately; clients observe progress via polling or (later) SSE.
The mediator's persist-every-transition design means a worker can be killed and
the run resumed by another.

## Consequences

- **+** The API stays responsive; long work is decoupled from the request cycle.
- **+** Horizontal scale — add workers to raise run throughput.
- **+** Natural fit with `Mediator.resume(run_id)` for crash recovery.
- **−** Operational surface grows (a worker fleet + Redis) — accepted; Redis is
  already in the stack for caching.

## Alternatives considered

- **Celery.** Heavier, sync-first; ARQ is a cleaner fit for an async codebase.
- **In-request execution.** Rejected — the failure mode above.
- **Temporal workers.** See ADR-0004; deferred.

> Phase 1 scope: this ADR sets the direction. The worker entrypoint and ARQ
> wiring land in the phase that exposes run endpoints; the mediator is already
> written to run under it unchanged.
