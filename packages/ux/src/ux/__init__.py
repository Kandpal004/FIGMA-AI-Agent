"""Ecommerce AI Design Director — the UX Strategy Engine (Phase 10).

The experience-architecture layer that transforms Business Strategy, Brand Strategy, and
Customer Psychology into a structured UX strategy — before any wireframe or screen is
designed. It is not a scraper, browser automation, MCP integration, or LLM wrapper: it
*consumes* the Customer Psychology (Phase 9), Brand Strategy (Phase 8), and Business
Strategy (Phase 7) and the platform's evidence (Research P6, Knowledge P3, Competitor P5,
Reasoning P4) through ports, and *architects the experience* — synthesising a cited,
deterministic, versioned :class:`~ux.domain.report.report.UXStrategyReport` (goals and
mental model, per-page strategies, the seven journeys, the flows, the six strategies, the
friction/drop-off analyses, the UX-law lens, and the five UX graphs).

It NEVER generates wireframes, UI, or Figma; it produces *UX decisions* only — it defines
WHY a page exists before anything decides HOW it looks, and it is the single source of
truth every future screen must originate from. Every decision references its evidence,
enforced structurally: a report cannot be constructed with an ungrounded decision. It is
upstream-independent of design — it imports nothing from later phases, emitting a neutral
:class:`~ux.domain.report.bundle.DesignBriefBundle` those phases pull through ports they
own.

Layers (dependencies point inward only):

* ``domain``         — the report aggregate, evidence graph, goals/mental model, page
  strategies, the journey primitive + map, flows, the six strategies, the friction/
  drop-off analyses, the UX-law lens, and the five graphs.
* ``application``    — the neutral input/synthesis contracts, the pipeline (assemble →
  consolidate → validate → analyse → apply laws → build graphs → score), the UXEngine
  orchestrator, and the ports the infrastructure implements.
* ``infrastructure`` — the deterministic rule-based UX strategist (the default brain) over
  a codified NN/g/Baymard/Shopify page knowledge base, in-memory + real Phase-9/8/7/3
  input adapters, in-memory and SQLAlchemy stores, and the composition roots.
* ``interfaces``     — the facade and serializable view DTOs.

Entry points:
:func:`ux.infrastructure.container.build_in_memory_environment` for local/testing, and
:func:`ux.infrastructure.persistence.wiring.build_sqlalchemy_environment` for a
database-backed deployment over the real adapters.
"""

__all__: list[str] = []
