# Engineering Principles — The Constitution

> **Status: Permanent and binding.** This document governs every architectural
> decision in this repository. It sits **above** individual ADRs: an ADR may
> record *how* we satisfy a principle, but no ADR may contradict one. Changing a
> principle requires an explicit amendment here, reviewed as a first-class
> decision — not a code review side-effect.

## What this project is

This is **not** a Figma AI tool. Figma is one output adapter among several.

This is an **AI Operating System for Ecommerce Design** — a commercial SaaS
platform that runs a fleet of specialist AI agents through an auditable,
resumable design pipeline to produce world-class Shopify Plus and Adobe Commerce
(Magento) storefronts. Every decision below optimizes for that: a durable,
multi-tenant, extensible product — not a demo, not a script, not a wrapper around
one integration.

The prime directive that follows from this: **the core is stable; everything
volatile is an adapter or configuration at its edge.** Models, prompts, knowledge,
tools, and output targets all change often. The orchestration core, the agent
contract, and the workflow state machine change rarely. We architect so the fast-
moving parts never force a change in the slow-moving core.

---

## The 14 Principles

Each principle carries: the rule, why it exists, the concrete **mechanism** that
enforces it, and its current **status**:

- ✅ **Enforced** — implemented and in effect today.
- 🔩 **Seam defined** — the interface exists; the implementation lands in a named phase.
- 🏗 **To build** — requires new structure in an upcoming phase (tracked below).

### P1 — Every AI agent must be replaceable
Any agent can be swapped for a different implementation (new prompt, model,
tooling, or a wholesale rewrite) without touching orchestration or any other
agent.
**Mechanism:** the single `run(AgentInput) -> AgentOutput` contract
(`core/contracts/agent.py`) + the `AgentRegistry` seam. The orchestrator names
roles, never classes.
**Status:** ✅ Enforced. See [ADR-0002](ADRs/0002-agent-contract.md).

### P2 — Every agent communicates using typed JSON contracts
No agent exchanges free-form text or ad-hoc dicts across its boundary. Inputs and
outputs are versioned, validated schemas.
**Mechanism:** frozen Pydantic v2 models `AgentInput` / `AgentOutput`, validated
at the boundary; the mediator rejects mis-tagged output. Schema versioning is
added in the agent-runtime phase (a `schema_version` field).
**Status:** ✅ Enforced (typing + validation) · 🔩 versioning field pending.

### P3 — Every workflow is resumable
Any run can be stopped — crash, deploy, human pause — and resumed exactly where
it left off, on any worker.
**Mechanism:** the state machine is pure and persists **every** transition;
`Mediator.resume(run_id)` reloads and continues. Proven by the wiring tests.
**Status:** ✅ Enforced (in-memory + contract) · 🔩 Postgres-backed store pending (Phase 2).

### P4 — Every workflow is stored in PostgreSQL
Run state and history are durable in Postgres — never only in memory or a cache.
**Mechanism:** `RunModel` + `TransitionModel` (`apps/api/db/models.py`); the
`RunStore` protocol gets its Postgres implementation in Phase 2.
**Status:** 🔩 Seam defined (schema + protocol) · 🏗 Postgres `RunStore` in Phase 2.

### P5 — Every decision is auditable
For any run we can reconstruct *what* happened, *when*, *which agent* decided it,
and *why* — especially every Creative-Director rejection.
**Mechanism:** append-only `run_transitions` table; rows are never mutated or
deleted while a run lives. Each carries `from/to state`, `event`, `agent_role`,
`notes`, timestamp.
**Status:** ✅ Enforced (model + contract) · 🔩 persistence in Phase 2.

### P6 — Every design section has its own lifecycle
A storefront is composed of sections (hero, PDP, cart, …). Each section runs its
own independent instance of the full design pipeline.
**Mechanism:** a run is already scoped to one `section`. This is promoted to a
first-class **Section** aggregate (a project owns many sections; each section
owns its runs and artifacts) in Phase 2.
**Status:** 🔩 Partial (run-per-section) · 🏗 Section aggregate in Phase 2. See [ADR-0013](ADRs/0013-section-lifecycle.md).

### P7 — Every design section can be rejected independently
Rejecting or reworking one section never disturbs another. Sections advance,
fail, and ship on their own timelines.
**Mechanism:** each section has its own run + state + audit trail; there is no
shared mutable pipeline state across sections. The Creative-Director veto acts on
one section's run.
**Status:** 🔩 Follows from P6; enforced once the Section aggregate lands.

### P8 — Every design section stores its full dossier
Each section durably stores: **research, reasoning, design decisions, references,
screenshots, review notes, approvals.**
**Mechanism:** a typed **Section Artifact Store** — one durable, queryable dossier
per section, written by agents through the contract (not scattered in blobs).
Screenshots and binaries go to object storage, referenced by URI.
**Status:** 🏗 To build in Phase 2. See [ADR-0013](ADRs/0013-section-lifecycle.md).

### P9 — Business logic must NEVER live inside prompts
Control flow, gating rules, scoring thresholds, routing, and policy live in
**code and configuration** — never buried in prompt text. A prompt instructs a
model; it does not *decide the workflow*.
**Mechanism:** the state machine owns all control flow; agents own reasoning.
Prompts contain role, task framing, and output schema — not pipeline logic. Code
review rejects any prompt that encodes routing/gating.
**Status:** ✅ Enforced by architecture (control flow is in the state machine, not agents). See [ADR-0011](ADRs/0011-prompts-knowledge-as-config.md).

### P10 — Prompts are configuration
Prompts are versioned, environment-loadable configuration — not hardcoded string
literals compiled into agents. They can be edited, A/B-tested, and rolled back
without a code deploy.
**Mechanism:** a **Prompt Registry** loading versioned prompt templates from
config (files now; DB-backed, per-tenant overridable later). Agents request a
prompt by key + version, never inline it.
**Status:** 🏗 To build (agent-runtime phase). See [ADR-0011](ADRs/0011-prompts-knowledge-as-config.md).

### P11 — Knowledge is configuration
Domain knowledge (design heuristics, brand guidelines, CRO rules, accessibility
standards, platform constraints) is data the platform loads — not logic baked
into agents.
**Mechanism:** a **Knowledge Base** as configuration + retrieval (Qdrant vector
memory for semantic recall, structured config for rules), injected via the tool
layer. Updating a heuristic is a data change.
**Status:** 🔩 Seam defined (Qdrant in stack, Memory Agent role reserved) · 🏗 registry in a later phase.

### P12 — Agents are independent services (service-ready, not prematurely distributed)
**Interpretation (binding):** every agent is designed so it *can* be extracted
into its own independently deployable, independently scalable service with **zero
changes to its contract** — but we run agents in-process as a modular monolith
until measured scale demands extraction. Premature microservices would buy
distributed-systems cost with no product benefit.
**Mechanism:** transport-agnostic contracts (typed JSON in/out), no shared mutable
state between agents, dependencies injected via `AgentContext`, communication only
through the mediator. Extraction later = putting an HTTP/queue boundary around an
already-isolated `run()`.
**Status:** ✅ Enforced (isolation guarantees hold today) · extraction deferred by design. See [ADR-0014](ADRs/0014-agents-service-ready.md).

### P13 — MCP integrations are adapters
Model Context Protocol, Figma, Shopify, Magento — all external systems are behind
adapter interfaces in the Tool Layer. No protocol or vendor detail leaks into an
agent.
**Mechanism:** agents receive named tool adapters via `AgentContext.tools` and
call domain-shaped methods; the MCP/Figma/commerce specifics live in one package.
**Status:** 🔩 Seam defined. See [ADR-0008](ADRs/0008-figma-via-mcp.md).

### P14 — Figma is only one output; the platform is output-agnostic
A completed design is an abstract, structured artifact. Rendering it to a target
— **Figma, HTML, React, Shopify theme, Magento theme** — is a pluggable emitter.
Adding a new output target must not change the core.
**Mechanism:** an **Output Renderer** port. The pipeline produces a canonical
design representation; each target implements `render(design) -> artifact`.
Targets are registered, not hardcoded.
**Status:** 🏗 To build (output phase). See [ADR-0012](ADRs/0012-output-renderer-abstraction.md).

---

## The shape these principles force

```
        Configuration (fast-moving, no deploy)          Adapters (pluggable)
        ├─ Prompt Registry        (P10)                 ├─ MCP / Figma      (P13)
        ├─ Knowledge Base         (P11)                 ├─ Shopify / Magento(P13)
        └─ Policy / thresholds    (P9)                  └─ Output Renderers (P14)
                    │                                            │
                    ▼                                            ▼
   ┌───────────────────────────────────────────────────────────────────────┐
   │                    STABLE CORE (slow-moving)                           │
   │  Agent contract (P1,P2) · State machine (P3,P5,P6,P7) · Mediator       │
   │  Section aggregate + artifact store (P6,P7,P8) · Postgres (P4,P5)      │
   │  Agents: isolated, service-ready (P12)                                 │
   └───────────────────────────────────────────────────────────────────────┘
```

Everything on the top row changes weekly and must never require a core change.
Everything in the box changes rarely and is protected by the contracts.

## Governance

- **Every future ADR** must cite which principle(s) it serves and must not
  violate any. A PR that adds control flow to a prompt, hardcodes a prompt
  string, or lets an agent call a vendor SDK directly is rejected on principle,
  not preference.
- **Amendments** to this document are explicit, dated, and reviewed on their own
  — never bundled into a feature PR.

## Reconciliation with Phase 1 (honest status)

Phase 1 already satisfies **P1, P2, P9, P12** and defines the seams for **P3, P5,
P13**. It does **not** yet implement: the Postgres `RunStore` (**P4**), the
Section aggregate and dossier store (**P6, P7, P8**), the Prompt Registry
(**P10**), the Knowledge Base registry (**P11**), or the Output Renderer
(**P14**). Those are scheduled — none require reworking the core, which is the
proof the foundation was built correctly. The new ADRs 0011–0014 record how each
will be met.
