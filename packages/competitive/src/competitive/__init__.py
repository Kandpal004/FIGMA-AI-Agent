"""Ecommerce AI Design Director — the Competitor Intelligence Engine (Phase 5).

The intelligence layer that transforms competitor observations into structured
business knowledge — before any UX or UI work begins. It is not a scraper, browser
automation, MCP integration, or LLM wrapper: it *receives* structured observations
through a port and synthesises them into a cited, deterministic, versioned
Competitor Intelligence Report (classification, profiles, recurring patterns, and
the benchmark / SWOT / gap / best-practice / risk / recommendation matrices).

Every recommendation references Knowledge-Engine citations (no opinions), enforced
structurally: a report cannot be constructed with a dangling citation.

Layers (dependencies point inward only):

* ``domain``         — the report aggregate, competitors/observations/profiles,
  recurring patterns, the six matrices, and the evidence graph.
* ``application``    — the classifier, profile builder, and matrix analyzers, the
  IntelligenceEngine orchestrator, and the ports the infrastructure implements.
* ``infrastructure`` — adapters to the Phase-3 Knowledge Engine and (optional)
  Phase-4 Reasoning Engine, future data-source adapters behind one port, in-memory
  and SQLAlchemy stores, and the composition roots.
* ``interfaces``     — the facade and serializable view DTOs.

Entry points:
:func:`competitive.infrastructure.container.build_in_memory_environment` for
local/testing, and
:func:`competitive.infrastructure.persistence.wiring.build_sqlalchemy_environment`
for a database-backed deployment over the real adapters.
"""

__all__: list[str] = []
