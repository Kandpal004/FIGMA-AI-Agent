# ADR-0007: `tenant_id` on every row from day one

**Status:** Accepted · **Date:** 2026-07-13

## Context

This is a SaaS product intended to serve many customer organizations. Tenancy is
the kind of cross-cutting concern that is nearly free to add at the start and
brutally expensive to retrofit — it touches every table, every query, and every
access path.

## Decision

Introduce a `tenants` table now and carry a `tenant_id` foreign key on every
tenant-owned row (`runs`, and all future domain tables). Scope every query by
tenant. The `AgentInput` already carries `tenant_id` so agents can tag anything
they persist (e.g. vector memory) with the owning tenant.

## Consequences

- **+** Tenant isolation is a `WHERE tenant_id = ?` filter, never a migration.
- **+** A clean path to Postgres Row-Level Security policies later.
- **+** Memory/vector data is tenant-scoped from the first write.
- **−** Slight schema and query verbosity now — trivial next to the retrofit cost.

## Alternatives considered

- **Single-tenant now, add tenancy later.** Rejected — the retrofit is one of
  the most expensive migrations in SaaS and blocks go-to-market.
- **Schema-per-tenant / database-per-tenant.** Rejected for this stage —
  operationally heavy; a single shared schema with `tenant_id` scales well into
  the mid-market. Can revisit for enterprise isolation requirements.
