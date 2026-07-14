"""Ecommerce AI Design Director — the Brand Strategy Engine (Phase 8).

The identity layer that transforms business strategy into a complete brand system —
before any UX, UI, copy, or Figma work begins. It is not a scraper, browser automation,
MCP integration, or LLM wrapper: it *consumes* the Business Strategy (Phase 7) and the
platform's evidence (Research P6, Knowledge P3, Competitor P5, Reasoning P4) through
ports, and *decides* — synthesising a cited, deterministic, versioned
:class:`~brand.domain.report.report.BrandStrategyReport` (classification, identity,
character, emotional strategy, visual direction, verbal system, decision graph, and the
consistency/governance/validation rule system).

It NEVER generates UI, Figma, tokens, or copy; it defines the *identity* every future
UX, UI, copywriting, and visual decision must follow. Every element references its
evidence, enforced structurally: a report cannot be constructed with an ungrounded brand
decision or a dangling citation. It is upstream-independent of design — it imports
nothing from later phases, emitting a neutral
:class:`~brand.domain.report.bundle.BrandGuidelinesBundle` those phases pull through
ports they own.

Layers (dependencies point inward only):

* ``domain``         — the report aggregate, evidence graph, the identity/character/
  emotional/visual/verbal models, the brand decision graph, and the governance rule
  system.
* ``application``    — the neutral input/synthesis contracts, the pipeline (assemble →
  consolidate → validate → build decision graph → derive governance → score), the
  BrandEngine orchestrator, and the ports the infrastructure implements.
* ``infrastructure`` — the deterministic rule-based brand strategist (the default brain)
  over a codified creative knowledge base, in-memory + real Phase-7/Phase-3 input
  adapters, in-memory and SQLAlchemy stores, and the composition roots.
* ``interfaces``     — the facade and serializable view DTOs.

Entry points:
:func:`brand.infrastructure.container.build_in_memory_environment` for local/testing,
and :func:`brand.infrastructure.persistence.wiring.build_sqlalchemy_environment` for a
database-backed deployment over the real adapters.
"""

__all__: list[str] = []
