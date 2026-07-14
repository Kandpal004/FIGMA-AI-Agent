"""Ecommerce AI Design Director — the Design Language Engine (Phase 14).

The engine that defines HOW the product should visually communicate — the visual source of
truth every future Design System, Component Library, and UI composition inherits from. It
generates NO UI, NO Figma, and NO concrete pixels: it *consumes* the Business Strategy (P7),
Brand Strategy (P8), Customer Psychology (P9), the Creative Director's approval (P13), and the
platform's evidence (Knowledge P3, Research P6, Competitor P5) through ports, and *designs the
visual language* — synthesising a cited, deterministic, versioned
:class:`~design_language.domain.report.report.DesignLanguageSpecification`: the Visual DNA
(style, luxury and minimalism levels, density, weight, contrast, rhythm, essence, distinctive
traits), the abstract token system (spacing/type/radius/elevation/motion scales, colour
philosophy, contrast targets), the eleven philosophies and four personalities, the grid and
responsive systems, the language selection (with considered-and-rejected alternatives), the
consistency/composition/constraint rules, the two graphs (visual, language), and the articulated
explanation of why this language wins and the others lose.

It selects among nineteen supported design languages (Apple, Polaris, Material 3, Stripe,
Linear, Aesop, Nike, luxury fashion/beauty, …) across twelve industry presets, and it is
engineered to prevent AI-generated-looking design: every visual choice is grounded (never
arbitrary), the selection records deliberate rejected alternatives, and hard visual constraints
enforce restraint and timelessness (accent/decoration limits, spacing floors, motion ceilings,
trend avoidance, a generic-pattern ban). Every recommendation references its evidence, enforced
structurally: a specification cannot be constructed with an ungrounded decision, and the graphs
are acyclic.

Layers (dependencies point inward only):

* ``domain``         — the specification aggregate, evidence graph, Visual DNA, token system,
  philosophies, personalities, grid/responsive systems, language selection, the rule sets, the
  graph primitive + the two graphs, the quality metrics, and the explanation.
* ``application``    — the neutral input/synthesis contracts, the pipeline (assemble →
  consolidate → design → validate grounding → build rules → build graphs → explain → score),
  the DesignLanguageEngine orchestrator, and the ports the infrastructure implements.
* ``infrastructure`` — the deterministic rule-based designer over a codified archetype +
  industry-preset knowledge base, real Phase-13/9/8/7/3 input adapters, in-memory and SQLAlchemy
  stores, and the composition roots.
* ``interfaces``     — the facade and serializable view DTOs.

Entry points:
:func:`design_language.infrastructure.container.build_in_memory_environment` for local/testing,
and :func:`design_language.infrastructure.persistence.wiring.build_sqlalchemy_environment` for a
database-backed deployment over the real adapters. It emits a neutral
:class:`~design_language.domain.report.bundle.DesignSystemBundle` a future Design System phase
consumes through a port it owns.
"""

__all__: list[str] = []
