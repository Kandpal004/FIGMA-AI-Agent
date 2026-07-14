"""Ecommerce AI Design Director — the Information Architecture Engine (Phase 11).

The structural-architecture layer that transforms the UX Strategy into a concrete
information architecture — the structural blueprint every future wireframe and screen must
originate from. It does NOT generate wireframes, UI, or Figma: it *consumes* the UX Strategy
(Phase 10), Business Strategy (Phase 7), Brand Strategy (Phase 8), and Customer Psychology
(Phase 9), plus the platform's evidence (Knowledge P3, Reasoning P4, Competitor P5, Research
P6) through ports, and *architects the structure* — synthesising a cited, deterministic,
versioned :class:`~ia.domain.report.report.IAReport`: the site map (which pages exist, why,
and how required each is), each page's blueprint (purpose, business + user goals, required
and optional sections with priority, primary/secondary actions, trust + conversion
placement, and the five priority dimensions), the navigation (global nav, mega menu, footer,
breadcrumbs), the page relationships and internal-linking strategy, the discovery strategy
(search, faceted filtering, sorting), and the six information-architecture graphs (site map,
navigation, page-flow, section, relationship, content tree).

It NEVER decides HOW a page looks — only WHAT it contains and WHY, and how the pages connect;
it is the single source of truth every future page structure the platform generates must
originate from. Every recommendation references its evidence, enforced structurally: a report
cannot be constructed with an ungrounded element, and every navigation target and
relationship endpoint must resolve to a page in the site map. It is upstream-independent of
design — it imports nothing from later phases, emitting a neutral
:class:`~ia.domain.report.bundle.WireframeBriefBundle` those phases pull through ports they
own.

Layers (dependencies point inward only):

* ``domain``         — the report aggregate, evidence graph, site map + page blueprints,
  sections + content blocks, navigation, relationships + internal linking, discovery, the
  shared graph primitive + the six graphs, and the quality metrics.
* ``application``    — the neutral input/synthesis contracts, the pipeline (assemble →
  consolidate → validate grounding → build graphs → score), the IAEngine orchestrator, and
  the ports the infrastructure implements.
* ``infrastructure`` — the deterministic rule-based IA architect (the default brain) over a
  codified Shopify/Adobe-Commerce page knowledge base, in-memory + real Phase-10/9/8/7/3
  input adapters, in-memory and SQLAlchemy stores, and the composition roots.
* ``interfaces``     — the facade and serializable view DTOs.

Entry points:
:func:`ia.infrastructure.container.build_in_memory_environment` for local/testing, and
:func:`ia.infrastructure.persistence.wiring.build_sqlalchemy_environment` for a
database-backed deployment over the real adapters.
"""

__all__: list[str] = []
