# Architecture Overview

> Phase 1 — Architecture Foundation. This document is the map. Read it first.
> Then read the binding [Engineering Principles](PRINCIPLES.md) — the constitution
> every decision here answers to.

## What we are building

An **AI Operating System for Ecommerce Design** — a commercial SaaS platform that
produces world-class Shopify Plus and Adobe Commerce (Magento) storefront designs.
Twenty specialist agents — Research, UX, UI, Creative Director, Accessibility,
Performance, and the rest — collaborate through a **persisted, auditable workflow**
in which the **Creative Director holds final veto authority** over every design
section.

This is **not** a Figma tool — Figma is one output adapter among several (HTML,
React, Shopify theme, Magento theme). It is not a chatbot and not a single agent.
It is a coordinated fleet driven by an explicit state machine, architected so that
the fast-moving edges (prompts, knowledge, tools, output targets) never force a
change in the stable core.

## The three invariants

Everything in Phase 1 exists to enforce three invariants that keep a 20-agent
system tractable:

1. **Agents never call agents.** Each agent implements one coroutine,
   `run(AgentInput) -> AgentOutput`, and returns a result. The **mediator**
   decides what happens next. This kills the dependency-graph explosion that
   sinks most multi-agent systems.

2. **Every workflow transition is persisted.** A design run is an append-only
   audit trail of state transitions. We can always reconstruct *why* the
   Creative Director rejected a section — the rejection and its notes are a row.

3. **The Creative Director is a first-class gate, not an `if` statement.** Its
   `REJECT` is a modeled transition that loops the run back to UI for redesign,
   bounded by a guard rail so it cannot loop forever.

## Layered view

```
┌──────────────────────────────────────────────────────────────┐
│  apps/web — React Design Console                              │
└───────────────────────────────┬──────────────────────────────┘
                                │ REST + (SSE streaming, later)
┌───────────────────────────────▼──────────────────────────────┐
│  apps/api — FastAPI                                           │
│  auth · tenancy · run lifecycle · health · error surface     │
└───────────────────────────────┬──────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────┐
│  packages/orchestration — the "Design Director"              │
│  StateMachine (pure) · Mediator (the loop) · AgentRegistry   │
└──────────────┬──────────────────────────────┬────────────────┘
               │                              │
┌──────────────▼─────────────┐   ┌────────────▼──────────────────┐
│  Agent Runtime (later)     │   │  Tool Layer (later)           │
│  BaseAgent + 20 agents     │   │  MCP/Figma · Shopify · Magento│
│                            │   │  · Qdrant memory              │
└──────────────┬─────────────┘   └────────────┬──────────────────┘
               │                              │
┌──────────────▼──────────────────────────────▼────────────────┐
│  packages/core — contracts · config · llm client · errors    │
└───────────────────────────────┬──────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────┐
│  Postgres (audit + state) · Redis (queue) · Qdrant (memory)  │
└──────────────────────────────────────────────────────────────┘
```

## Import direction (kept acyclic)

```
apps/*  ──►  orchestration  ──►  core
```

`core` imports nothing internal. `orchestration` imports only `core`. `apps`
import both. This one-way rule is what lets any agent be built and tested in
isolation, and it is enforced by the module layout, not by convention alone.

## The pieces of the foundation

| Component | File | Responsibility |
|-----------|------|----------------|
| Config | `core/config.py` | Typed, validated settings from the environment. |
| Agent contract | `core/contracts/agent.py` | `AgentInput`, `AgentOutput`, `BaseAgent` — the interface all 20 agents obey. |
| Workflow contract | `core/contracts/workflow.py` | States, the transition graph, `RunRecord`. |
| LLM client | `core/llm/client.py` | Claude access with retries, routing, token accounting. |
| State machine | `orchestration/state_machine.py` | Pure transition logic + audit records. |
| Mediator | `orchestration/mediator.py` | The loop that invokes agents and advances runs. |
| Registry | `orchestration/registry.py` | role → agent-class mapping. |
| Persistence | `apps/api/db/models.py` | Tenants, runs, transitions (multi-tenant). |
| API | `apps/api/main.py` | Bootable FastAPI with health/readiness. |

## What Phase 1 deliberately does NOT include

- No agent business logic (the 20 agents are empty until later phases).
- No real MCP/Figma, Shopify, or Magento calls (the Tool Layer is a seam).
- No Alembic migrations yet (`init_models()` covers local bring-up).
- No auth provider integration (tenancy columns exist; enforcement comes later).

Each is a named seam, not an omission — the interfaces they plug into are already
defined here.

## Where to go next

- The decision record: [`ADRs/`](ADRs/)
- The agent contract in depth: [`01-agent-contract.md`](01-agent-contract.md)
- Orchestration: [`02-orchestration.md`](02-orchestration.md)
- The state machine: [`03-workflow-state-machine.md`](03-workflow-state-machine.md)
- The data model: [`04-data-model.md`](04-data-model.md)
