"""Stage — Quality scoring.

Computes the plan's calibrated quality picture deterministically:

* **coverage** — how many of the required planning outputs the plan produced (pages,
  sections, blocks, components, criteria, checklists, requirements, approvals, graphs).
* **grounding** — the fraction of decisions whose citations resolve (``1.0`` by construction,
  surfaced here so the metric is auditable).
* **completeness** — the fraction of required sections that are execution-ready (carry a
  required component, success criteria, and a review checklist).
* **confidence** — the aggregate confidence, anchored on how richly the sections are
  specified.
"""

from __future__ import annotations

from wireframe.domain.approval.approval import ApprovalPlan
from wireframe.domain.graph.graphs import WireframeGraphs
from wireframe.domain.plan.blueprint import PlanBlueprint
from wireframe.domain.quality.quality import WireframeQualityMetrics
from wireframe.domain.shared.value_objects import Confidence, Percentage

__all__ = ["QualityScorer"]


class QualityScorer:
    """Scores the plan's coverage, grounding, completeness, and confidence."""

    def score(
        self,
        blueprint: PlanBlueprint,
        approval_plan: ApprovalPlan,
        graphs: WireframeGraphs,
    ) -> WireframeQualityMetrics:
        return WireframeQualityMetrics(
            coverage=Percentage.ratio(*self._coverage(blueprint, approval_plan)),
            grounding=Percentage.ratio(*self._grounding(blueprint, approval_plan, graphs)),
            completeness=Percentage.ratio(*self._completeness(blueprint)),
            confidence=self._confidence(blueprint),
        )

    @staticmethod
    def _coverage(blueprint: PlanBlueprint, approval_plan: ApprovalPlan) -> tuple[int, int]:
        sections = blueprint.sections()
        checklist = (
            bool(blueprint.pages),
            all(p.required_sections() for p in blueprint.pages),
            any(s.blocks for s in sections),
            any(s.required_components for s in sections),
            any(s.required_data for s in sections),
            any(s.interaction_requirements for s in sections),
            any(s.responsive_behaviour.rules for s in sections),
            any(s.accessibility_requirements for s in sections),
            any(s.seo_requirements for s in sections),
            any(s.performance_considerations for s in sections),
            any(s.success_criteria for s in sections),
            any(s.failure_criteria for s in sections),
            any(s.review_checklist for s in sections),
            any(s.dependencies for s in sections),
            bool(len(approval_plan)),
        )
        return sum(1 for present in checklist if present), len(checklist)

    @staticmethod
    def _grounding(
        blueprint: PlanBlueprint, approval_plan: ApprovalPlan, graphs: WireframeGraphs
    ) -> tuple[int, int]:
        # Grounding over the citable leaf decisions: sections, blocks, components, approval
        # requirements, and graph nodes.
        citable: list[tuple] = []
        for section in blueprint.sections():
            citable.append(section.all_evidence_ids())
            for block in section.blocks:
                citable.append(block.all_evidence_ids())
            for comp in section.all_components():
                citable.append(comp.all_evidence_ids())
        for req in approval_plan:
            citable.append(req.all_evidence_ids())
        for graph in graphs.all():
            for node in graph:
                citable.append(node.evidence_ids)
        if not citable:
            return 0, 1
        grounded = sum(1 for ev in citable if ev)
        return grounded, len(citable)

    @staticmethod
    def _completeness(blueprint: PlanBlueprint) -> tuple[int, int]:
        required = [s for p in blueprint.pages for s in p.required_sections()]
        if not required:
            return 0, 1
        ready = sum(
            1
            for s in required
            if s.required_components and s.success_criteria and s.review_checklist
        )
        return ready, len(required)

    @staticmethod
    def _confidence(blueprint: PlanBlueprint) -> Confidence:
        sections = blueprint.sections()
        if not sections:
            return Confidence.of(0.0)
        detailed = sum(
            1
            for s in sections
            if s.blocks and s.required_components and s.success_criteria and s.review_checklist
        )
        return Confidence.clamp(0.5 + 0.5 * (detailed / len(sections)))
