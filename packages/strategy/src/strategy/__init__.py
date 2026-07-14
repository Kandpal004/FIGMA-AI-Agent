"""Ecommerce AI Design Director — the Business Strategy Engine (Phase 7).

The decision layer that transforms research into business strategy — before any UX, UI,
or Figma work begins. It is not a scraper, browser automation, MCP integration, or LLM
wrapper: it *consumes* evidence (Research P6, Knowledge P3, Reasoning P4, Competitor
P5) and context (brand, project, goals) through ports, and *decides* — synthesising a
cited, deterministic, versioned :class:`~strategy.domain.report.report.BusinessStrategyReport`
(goals, customer model, the eight positioning pillars, the decision and strategy
graphs, the priority matrix, and the risk/opportunity registers).

It NEVER generates UI, Figma, wireframes, or copy; it produces *structured business
decisions* only, and it is the single source of truth every downstream design decision
must derive from. Every decision references its evidence, enforced structurally: a
report cannot be constructed with an ungrounded decision or a dangling citation. It is
upstream-independent of design — it imports nothing from later phases, emitting a
neutral :class:`~strategy.domain.report.bundle.DesignDirectiveBundle` those phases pull
through ports they own.

Layers (dependencies point inward only):

* ``domain``         — the report aggregate, evidence graph, the eight pillars, the
  decision and strategy graphs, the priority matrix, and the risk/opportunity
  registers.
* ``application``    — the neutral input/synthesis contracts, the pipeline stages
  (assemble → consolidate → validate → build graphs → prioritise → analyse → score),
  the StrategyEngine orchestrator, and the ports the infrastructure implements.
* ``infrastructure`` — the deterministic rule-based strategist (the default brain),
  in-memory input adapters, in-memory and SQLAlchemy stores, and the composition roots.
* ``interfaces``     — the facade and serializable view DTOs.

Entry points:
:func:`strategy.infrastructure.container.build_in_memory_environment` for
local/testing, and
:func:`strategy.infrastructure.persistence.wiring.build_sqlalchemy_environment` for a
database-backed deployment over the real Phase 3–6 adapters.
"""

__all__: list[str] = []
