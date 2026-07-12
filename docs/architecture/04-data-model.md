# The Data Model

Two representations of the same truth, kept aligned:

- **Pydantic contracts** (`core/contracts/workflow.py`) — the in-memory and
  transport shape used by the state machine and API.
- **SQLAlchemy ORM** (`apps/api/db/models.py`) — the durable shape in Postgres.

Keeping them mirrored lets the pure state machine stay database-free while
everything is still persisted.

## Tables

### `tenants`
The root of every ownership chain — a customer of the SaaS.

| Column | Notes |
|--------|-------|
| `id` (uuid, pk) | |
| `name`, `slug` | `slug` unique + indexed |
| `created_at`, `updated_at` | DB-managed |

### `runs`
A design run for a single page section — the durable form of `RunRecord`.

| Column | Notes |
|--------|-------|
| `id` (uuid, pk) | |
| `tenant_id` (fk → tenants, cascade) | **indexed; every run is tenant-scoped** |
| `section` | e.g. `hero`, `pdp` |
| `state` | `WorkflowState`, indexed |
| `status` | `RunStatus`, indexed |
| `brief`, `artifacts` | JSON |
| `redesign_count` | Creative-Director rejection counter |
| `created_at`, `updated_at` | DB-managed |

### `run_transitions`
Append-only audit trail — the durable form of `TransitionRecord`.

| Column | Notes |
|--------|-------|
| `id` (uuid, pk) | |
| `run_id` (fk → runs, cascade) | indexed |
| `from_state`, `to_state` | `WorkflowState` |
| `event` | `TransitionEvent` |
| `agent_role` | which agent drove it |
| `notes` | JSON — rejection reasons live here |
| `created_at` | DB-managed |

Rows are **never** updated or deleted while a run lives. This table is the
literal record of why every decision — especially each Creative-Director
rejection — was made.

## Multi-tenancy from row zero (ADR-0007)

Every tenant-owned row carries `tenant_id`. This is deliberate and non-negotiable:
retrofitting tenancy onto a live SaaS is among the most expensive migrations
there is, and it touches every query. We pay the trivial cost now so that
row-level scoping (and later, row-level security policies) is a filter, not a
rewrite.

## Enums as portable strings

`WorkflowState`, `RunStatus`, and `TransitionEvent` are stored via
`native_enum=False` (string-backed) rather than Postgres `ENUM` types. Adding a
state then requires no `ALTER TYPE` migration — important while the pipeline is
still evolving. We can promote to native enums once the set stabilizes.

## Migrations

Schema is owned by **Alembic** from a later phase. For local bring-up,
`api.db.session.init_models()` creates the tables directly from ORM metadata —
convenient for a fresh database, never used in production.
