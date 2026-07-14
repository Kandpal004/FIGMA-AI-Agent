"""Ecommerce AI Design Director — the Research Engine (Phase 6).

The data-acquisition and evidence-collection layer upstream of all reasoning. It is
not a scraper, browser automation, MCP integration, or LLM wrapper: it *collects*
raw artifacts from registered sources through ports, then validates, normalises,
deduplicates, and extracts evidence, typed entities (the nineteen types), and their
relationships — synthesising a cited, deterministic, versioned
:class:`~research.domain.report.report.ResearchReport`.

It NEVER generates designs, UI, or business decisions; its sole job is high-quality,
provenance-tracked evidence. Every finding traces to a source and a place within it,
enforced structurally: a report cannot be constructed with a dangling reference. It is
upstream-independent — it imports nothing from the Reasoning (P4) or Competitor (P5)
engines, emitting a neutral :class:`~research.domain.report.bundle.ReasoningBundle`
those engines pull through ports they own.

Layers (dependencies point inward only):

* ``domain``         — the report aggregate, sources/requests, raw artifacts and
  extractions, the evidence graph, the entity graph, quality metrics, and validation.
* ``application``    — the nine pipeline stages, the source registry, the
  ResearchEngine orchestrator, and the ports the infrastructure implements.
* ``infrastructure`` — the structured/HTML extractors, in-memory / Knowledge-Engine
  (P3) / Project-Memory (P2) source adapters, the knowledge-link grounding adapter,
  in-memory and SQLAlchemy stores, and the composition roots.
* ``interfaces``     — the facade and serializable view DTOs.

Entry points:
:func:`research.infrastructure.container.build_in_memory_environment` for
local/testing, and
:func:`research.infrastructure.persistence.wiring.build_sqlalchemy_environment` for a
database-backed deployment over the real adapters.
"""

__all__: list[str] = []
