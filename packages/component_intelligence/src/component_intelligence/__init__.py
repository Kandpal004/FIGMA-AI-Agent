"""Ecommerce AI Design Director — the Component Intelligence Engine (Phase 15).

The brain behind every future component. It is not a component library and not a design system:
it understands WHY components exist, decides WHICH should exist, WHEN to use them, WHY, and WHEN
NOT. It generates NO component code, NO Figma, and NO UI: it *consumes* the Business Strategy
(P7), Brand (P8), Customer Psychology (P9), UX (P10), Information Architecture (P11), Wireframe
Plan (P12), Creative Director (P13), Design Language (P14), and the platform evidence (Knowledge
P3, Research P6, Competitor P5) through ports, and *reasons about components* — producing a
cited, deterministic, versioned
:class:`~component_intelligence.domain.report.report.ComponentCompositionSpecification` over the
forty-one supported components.

For every component it determines the four purposes (business/user/conversion/trust), the SEO/
accessibility/performance impacts and the conversion/friction/trust effects, the mobile/
responsive/interaction/animation behaviour, the data contract and success/failure criteria, and
the usage guidance (where it belongs, when to use, when *not* to use, what it conflicts with),
plus its variants, states, and design-token references. It derives the composition/placement/
visibility/responsive/reuse rules and the compatibility web, and builds the component and
dependency graphs.

No component is ever chosen at random: a component may only be included because the evidence says
it improves a business outcome, and the coherence invariant makes incompatible components
structurally impossible to co-place while dependency closure makes dangling components
impossible. Every recommendation references its evidence, enforced structurally.

Layers (dependencies point inward only):

* ``domain``         — the specification aggregate, evidence graph, the component decision and
  its sub-models, the composition, the compatibility web, the five rule collections, the graph
  primitive + the two graphs, and the quality metrics.
* ``application``    — the neutral input/synthesis contracts, the pipeline (assemble →
  consolidate → decide → validate grounding → resolve coherence → build rules → build graphs →
  score), the ComponentIntelligenceEngine orchestrator, and the ports the infrastructure
  implements.
* ``infrastructure`` — the deterministic rule-based brain over a codified forty-one-component
  catalog, real Phase-14/13/12/11/10/9/8/7/3 input adapters, in-memory and SQLAlchemy stores, and
  the composition roots.
* ``interfaces``     — the facade and serializable view DTOs.

Entry points:
:func:`component_intelligence.infrastructure.container.build_in_memory_environment` for
local/testing, and
:func:`component_intelligence.infrastructure.persistence.wiring.build_sqlalchemy_environment` for
a database-backed deployment over the real adapters. It emits a neutral
:class:`~component_intelligence.domain.report.bundle.ComponentSpecBundle` a future Design System
phase consumes through a port it owns.
"""

__all__: list[str] = []
