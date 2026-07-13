"""Ecommerce AI Design Director — the Reasoning Engine (Phase 4).

The engine that thinks before any design. It transforms user intent + context into
a structured, cited, deterministic **Design Strategy** — it never generates designs.
Every recommendation references at least one Knowledge-Engine citation (pinned by
version), so the output is reproducible and free of hallucination; where the corpus
is silent it records an explicit knowledge gap rather than inventing an answer.

Layers (dependencies point inward only):

* ``domain``         — the DesignStrategy aggregate, the reason/decision/evidence
  graphs, and the risk/confidence/trade-off/alternative/request value objects.
* ``application``    — the pluggable dimension reasoners, the ReasoningEngine
  orchestrator, the risk analyzer, confidence calculator, trade-off deriver, and
  alternative generator, plus the ports the infrastructure implements.
* ``infrastructure`` — adapters to the Phase-3 Knowledge Engine and Phase-2
  Memory, in-memory and SQLAlchemy stores, and the composition roots.
* ``interfaces``     — the facade and serializable view DTOs.

Entry points:
:func:`reasoning.infrastructure.container.build_in_memory_environment` for
local/testing, and
:func:`reasoning.infrastructure.persistence.wiring.build_sqlalchemy_environment`
for a database-backed deployment over the real Knowledge/Memory adapters.
"""

__all__: list[str] = []
