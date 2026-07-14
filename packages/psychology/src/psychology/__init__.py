"""Ecommerce AI Design Director — the Customer Psychology Engine (Phase 9).

The behavioral layer that transforms brand strategy into customer buying psychology —
before any UX, CRO, copywriting, or UI work begins. It is not a scraper, browser
automation, MCP integration, or LLM wrapper: it *consumes* the Brand Strategy (Phase 8)
and Business Strategy (Phase 7) and the platform's evidence (Research P6, Knowledge P3,
Competitor P5, Reasoning P4) through ports, and *models how the target human decides* —
synthesising a cited, deterministic, versioned
:class:`~psychology.domain.report.report.CustomerPsychologyReport` (the psychological
profile, personas, jobs, journeys, the nine matrices, the behavioral-framework lens, and
the six psychology graphs).

It NEVER generates UI, wireframes, or Figma; it produces *structured customer psychology
intelligence* only, and it is the foundation every UX and CRO decision must derive from.
Every determination references its evidence, enforced structurally: a report cannot be
constructed with an ungrounded claim. It is upstream-independent of design — it imports
nothing from later phases, emitting a neutral
:class:`~psychology.domain.report.bundle.UXDirectiveBundle` those phases pull through
ports they own.

Layers (dependencies point inward only):

* ``domain``         — the report aggregate, evidence graph, the psychological profile,
  personas and jobs, the buying/decision journeys, the nine matrices, the framework
  models (Maslow/Fogg/Hook/JTBD/behavioral economics), and the six graphs.
* ``application``    — the neutral input/synthesis contracts, the pipeline (assemble →
  consolidate → validate → build matrices → apply frameworks → build graphs → score),
  the PsychologyEngine orchestrator, and the ports the infrastructure implements.
* ``infrastructure`` — the deterministic rule-based psychologist (the default brain) over
  a codified behavioral-science knowledge base, in-memory + real Phase-8/7/3 input
  adapters, in-memory and SQLAlchemy stores, and the composition roots.
* ``interfaces``     — the facade and serializable view DTOs.

Entry points:
:func:`psychology.infrastructure.container.build_in_memory_environment` for
local/testing, and
:func:`psychology.infrastructure.persistence.wiring.build_sqlalchemy_environment` for a
database-backed deployment over the real adapters.
"""

__all__: list[str] = []
