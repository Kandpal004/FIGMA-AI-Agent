# ADR-0013: Section-level lifecycle and the section dossier

**Status:** Accepted · **Date:** 2026-07-13
**Serves principles:** P6 (per-section lifecycle), P7 (independent rejection),
P8 (full section dossier), P4/P5 (durable, auditable).

## Context

A storefront is not designed as one monolith; it is designed section by section —
hero, PDP, cart, collection, footer. Each section must progress, be reviewed,
be rejected, and ship on its **own** timeline without disturbing the others, and
must retain a complete record of how it was designed. Phase 1 scoped a run to a
`section` string, which is enough to prove the pipeline but not enough to model a
section as a first-class, independently-managed entity with a rich dossier.

## Decision

Promote sections to a first-class aggregate:

```
Project (a storefront design engagement)
  └── Section (hero, pdp, cart, …)         ← its own lifecycle (P6, P7)
        ├── Run(s)                          ← pipeline executions for this section
        │     └── Transitions               ← append-only audit trail (P5)
        └── Dossier                         ← the durable record (P8)
              ├── research
              ├── reasoning / design decisions
              ├── references
              ├── screenshots               (object storage, referenced by URI)
              ├── review notes
              └── approvals
```

Rules:
- Each **Section** owns its runs, state, and dossier. There is **no shared mutable
  pipeline state across sections** — so rejecting or reworking one section cannot
  affect another (P7).
- The **Dossier** is a typed, queryable store written by agents *through the
  contract* — not free-form blobs. Binaries (screenshots) live in object storage;
  the dossier holds structured metadata + URIs.
- Everything is Postgres-durable (P4) and auditable (P5).

## Consequences

- **+** Sections advance and ship independently — the natural unit of work and of
  the Creative-Director veto.
- **+** The dossier makes every section explainable and reusable (memory, reuse
  across projects, client-facing rationale).
- **+** Clean parallelism: N sections can run concurrently across workers.
- **−** More schema and a storage integration for binaries — accepted; it is core
  product value, not overhead.

## Alternatives considered

- **Keep run-per-section-string.** Rejected — no independent lifecycle, no home
  for the dossier, no project grouping.
- **One giant design document per project.** Rejected — couples sections, defeats
  independent rejection (P7).

> Scope: this ADR fixes the model. The `Project`/`Section`/`Dossier` schema and
> the artifact store land in Phase 2, alongside the Postgres `RunStore`.
