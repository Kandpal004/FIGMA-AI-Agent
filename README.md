# Ecommerce AI Design Director

> An **AI Operating System for Ecommerce Design** — a commercial SaaS platform for creating world-class **Shopify Plus** and **Adobe Commerce (Magento)** experiences, from research and strategy through UX, UI, design-system validation, accessibility, performance, and a Creative-Director approval gate.

This is **not** a Figma tool — Figma is one output adapter among several (HTML, React, Shopify theme, Magento theme). It is not a chatbot and not a single agent. It is a coordinated fleet of specialist agents driven by a **persisted, auditable workflow state machine**, with a **Creative Director** holding final veto authority over every design section.

The repository is governed by a permanent [**Engineering Principles constitution**](docs/architecture/PRINCIPLES.md) — 14 binding rules every future decision answers to. Read it before contributing.

---

## Status

**Phase 1 — Architecture Foundation.** The skeleton is in place: the workspace, the agent contract, the orchestration core (state machine + mediator + registry), the data model, and a bootable API. Agent *brains* arrive in later phases; Phase 1 deliberately ships **zero business logic** so every one of the 20 agents inherits a correct foundation.

See [`docs/architecture/00-overview.md`](docs/architecture/00-overview.md) for the full design and [`docs/architecture/ADRs/`](docs/architecture/ADRs/) for the decision record.

---

## Architecture at a glance

```
React Console  ──►  FastAPI  ──►  Orchestration Core  ──►  Agent Runtime
                                   (state machine +          (BaseAgent, 20
                                    mediator + registry)      specialists)
                                        │                          │
                                        ▼                          ▼
                              Postgres · Redis · Qdrant      Tool Layer (MCP/Figma,
                              (audit trail, queue, memory)    Shopify, Magento)
```

**Three invariants the foundation enforces:**

1. **Agents never call agents.** They emit a typed `AgentOutput`; the *mediator* routes. No agent imports another agent.
2. **Every workflow transition is persisted.** A design run is a resumable, auditable record — we can always answer *"why did the Creative Director reject this?"*
3. **The Creative Director is a first-class gate**, not an `if` statement. Its `REJECT` transition loops the run back for redesign.

---

## Repository layout

```
.
├── packages/
│   ├── core/            # config, contracts (agent + workflow), llm client, errors, logging
│   └── orchestration/   # state machine, mediator, agent registry
├── apps/
│   ├── api/             # FastAPI app: db, routers, dependency wiring
│   └── web/             # React (Vite) design console
├── docs/architecture/   # overview + ADRs (the written record of every decision)
├── docker-compose.yml   # Postgres · Redis · Qdrant for local dev
├── Makefile             # dev commands
└── pyproject.toml       # uv workspace root
```

---

## Tech stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.12 |
| Backend | FastAPI (async) |
| Frontend | React + Vite + TypeScript |
| ORM | SQLAlchemy 2.0 (async, asyncpg) |
| Database | PostgreSQL |
| Cache / Queue | Redis (+ ARQ workers, later phases) |
| Vector memory | Qdrant |
| LLM | Anthropic Claude (Opus for reasoning, Haiku for mechanical work) |
| Figma | Model Context Protocol (MCP) |
| Tooling | uv workspace · Ruff · mypy (strict) · pytest |

---

## Getting started

Requires **Python 3.12+**, **[uv](https://docs.astral.sh/uv/)**, **Docker**, and **Node 20+**.

```bash
# 1. Configure
cp .env.example .env          # then fill in ANTHROPIC_API_KEY and secrets

# 2. Start infrastructure (Postgres, Redis, Qdrant)
make up

# 3. Install the Python workspace
make install

# 4. Run the API
make api                      # http://localhost:8000/health

# 5. Run the web console (separate terminal)
make web                      # http://localhost:5173
```

Run `make help` to see every command.

---

## The design workflow

```
Research → Business Strategy → UX → Wireframe → Review ⤺(reject → UX)
        → UI → Review → Design-System Validation → Accessibility → Performance
        → Creative Director Gate ⤺(reject → UI) → Section Done
```

Each arrow is a persisted state transition. The `⤺` loops are the review and Creative-Director veto paths. See [`docs/architecture/03-workflow-state-machine.md`](docs/architecture/03-workflow-state-machine.md).

---

## License

Proprietary — © Vasansi. All rights reserved.
