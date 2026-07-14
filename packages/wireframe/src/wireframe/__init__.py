"""Ecommerce AI Design Director — the Wireframe Planning Engine (Phase 12).

The master planning layer that transforms the Information Architecture into a structured
wireframe execution plan — the single source of truth every future Figma document derives
from. It generates NO UI, NO Figma, NO HTML, and NO visual layout: it *consumes* the
Information Architecture (Phase 11), UX Strategy (Phase 10), Business Strategy (Phase 7),
Brand Strategy (Phase 8), and Customer Psychology (Phase 9), plus the platform's evidence
(Knowledge P3, Reasoning P4, Competitor P5, Research P6) through ports, and *plans the build*
— synthesising a cited, deterministic, versioned
:class:`~wireframe.domain.report.report.WireframePlan`: the page/section blueprint (each
section's four goals, blocks, required and optional components, data/asset/interaction/
responsive/accessibility/SEO/performance requirements, inputs/outputs, dependencies, success/
failure criteria, and review checklist), the deterministic execution order, the approval
plan, and the six planning graphs (wireframe, section-dependency, content, component,
execution, approval).

It decides WHAT must be built, WHY, FROM WHAT, IN WHAT ORDER, and HOW it is approved — never
how anything looks. Every recommendation references its evidence, enforced structurally: a
plan cannot be constructed with an ungrounded element, every section reference resolves, and
the dependency, execution, component, and approval graphs are acyclic. It is
upstream-independent of design — it imports nothing from later phases, emitting a neutral
:class:`~wireframe.domain.report.bundle.FigmaPlanBundle` a future Figma engine pulls through a
port it owns.

Layers (dependencies point inward only):

* ``domain``         — the plan aggregate, evidence graph, page/section blueprint, blocks,
  component requirements, approval model, the shared graph primitive + the six graphs, and
  the quality metrics.
* ``application``    — the neutral input/synthesis contracts, the pipeline (assemble →
  consolidate → validate grounding → resolve execution order → plan approvals → build graphs
  → score), the WireframeEngine orchestrator, and the ports the infrastructure implements.
* ``infrastructure`` — the deterministic rule-based planner (the default brain) over a
  codified Shopify/Adobe-Commerce page/section knowledge base, in-memory + real
  Phase-11/10/9/8/7/3 input adapters, in-memory and SQLAlchemy stores, and the composition
  roots.
* ``interfaces``     — the facade and serializable view DTOs.

Entry points:
:func:`wireframe.infrastructure.container.build_in_memory_environment` for local/testing, and
:func:`wireframe.infrastructure.persistence.wiring.build_sqlalchemy_environment` for a
database-backed deployment over the real adapters.
"""

__all__: list[str] = []
