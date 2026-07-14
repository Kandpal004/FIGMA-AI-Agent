"""Ecommerce AI Design Director — the Creative Director Engine (Phase 13).

The highest authority in the platform: a deterministic review-and-approval system — NOT an LLM
and NOT a prompt — through which no design, wireframe, UX, or business decision may proceed
without approval. It *consumes* all ten upstream engines (Business Strategy P7, Brand P8,
Customer Psychology P9, Knowledge P3, Reasoning P4, Research P6, Competitor P5, UX P10,
Information Architecture P11, and the Wireframe Plan P12 — the subject) through ports, and
*reviews the subject* across sixteen dimensions, producing a cited, deterministic, versioned
:class:`~creative_director.domain.report.report.CreativeDirectorReview`: a pass/fail verdict
per dimension with findings, blocking issues, warnings, recommendations, and required changes;
fifteen category scores rolled up to an overall; a binding approval decision with a full
decision history; a quality matrix and an improvement matrix; and the five review graphs
(review, decision, approval, quality matrix, improvement matrix).

It is built to *reject* AI-generated-looking work — generic layouts, weak typography and
spacing, weak hierarchy, poor CRO, low trust, and decorative designs with no business purpose —
deterministically, with cited reasons: a polished plan that cites no business, trust, or
conversion grounding fails its critical dimensions and is blocked. Every ruling references its
evidence, enforced structurally: an approval is impossible below the configured threshold, with
any failing hard gate, or with any blocking finding; a review cannot be constructed with an
ungrounded ruling. It supports six review profiles (Startup, Enterprise, Luxury, Marketplace,
D2C, B2B) that reweight and gate categories, a configurable threshold, and four review modes
(Automatic, Human-Assisted, Creative-Director-Override, Review-Committee) — the human retains
final veto authority through overrides recorded, never erased.

Layers (dependencies point inward only):

* ``domain``         — the review aggregate, evidence graph, findings, per-dimension reviews,
  scorecard, review policy/profile, the approval decision + decision history, the matrices,
  the shared graph primitive + the five graphs, and the review-quality metrics.
* ``application``    — the neutral input/synthesis contracts, the pipeline (assemble →
  consolidate → review → validate grounding → score → evaluate approval → build graphs and
  matrices), the CreativeDirectorEngine orchestrator, and the ports the infrastructure
  implements.
* ``infrastructure`` — the deterministic rule-based critic panel over a codified
  premium-ecommerce standards base, the six calibrated review profiles, real Phase-12/11/10/
  9/8/7/3 input adapters, in-memory and SQLAlchemy stores, and the composition roots.
* ``interfaces``     — the facade and serializable view DTOs.

Entry points:
:func:`creative_director.infrastructure.container.build_in_memory_environment` for
local/testing, and
:func:`creative_director.infrastructure.persistence.wiring.build_sqlalchemy_environment` for a
database-backed deployment over the real adapters. ``can_proceed`` is the platform's go/no-go
gate every downstream phase obeys.
"""

__all__: list[str] = []
