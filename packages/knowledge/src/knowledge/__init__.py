"""Ecommerce AI Design Director — the Knowledge Engine (Phase 3).

The reasoning foundation used by every AI agent: a curated, versioned, cited,
deterministic knowledge graph of ecommerce and design principles. Not RAG, not
vector search — the source of truth against which decisions are justified.

Layers (dependencies point inward only):

* ``domain``         — entries, the knowledge graph, applicability, the lifecycle
  status machine, and the reasoning value objects (query, context, rationale).
* ``application``    — the query service, the reasoning core, the authoring
  service, and the ports the infrastructure implements.
* ``infrastructure`` — in-memory and SQLAlchemy stores, a structured search
  adapter (the future-Qdrant seam), and the composition roots.
* ``interfaces``     — the facade and serializable view DTOs.

Entry points:
:func:`knowledge.infrastructure.container.build_in_memory_environment` for
local/testing, and
:func:`knowledge.infrastructure.persistence.wiring.build_sqlalchemy_environment`
for a database-backed deployment.
"""

__all__: list[str] = []
