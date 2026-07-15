"""Stage — Quality scoring.

Computes the plan's calibrated quality picture deterministically:

* **coverage** — the fraction of in-scope pages (from the brief) that received a plan.
* **binding_integrity** — passed through from the selection resolver (``1.0`` when every section
  binds the tokens its choices reference).
* **sequencing** — ``1.0`` when the execution graph yields a total topological order over all its
  nodes (guaranteed by the acyclic primitive).
* **grounding** — the fraction of decisions (sections + review checkpoints) that cite evidence
  (``1.0`` by construction).
* **confidence** — the aggregate confidence across the evidence.
"""

from __future__ import annotations

from collections.abc import Sequence

from design_orchestrator.domain.evidence.evidence import EvidenceGraph
from design_orchestrator.domain.graph.graphs import OrchestratorGraphs
from design_orchestrator.domain.plan.page import PagePlan
from design_orchestrator.domain.quality.quality import ExecutionPlanQualityMetrics
from design_orchestrator.domain.review.review_plan import ReviewPlan
from design_orchestrator.domain.shared.value_objects import (
    Confidence,
    PageType,
    Percentage,
)

__all__ = ["QualityScorer"]


class QualityScorer:
    """Scores the plan's coverage, binding integrity, sequencing, grounding, confidence."""

    def score(
        self,
        pages: Sequence[PagePlan],
        scoped_pages: Sequence[PageType],
        graphs: OrchestratorGraphs,
        review_plan: ReviewPlan,
        evidence: EvidenceGraph,
        binding_integrity: Percentage,
    ) -> ExecutionPlanQualityMetrics:
        return ExecutionPlanQualityMetrics(
            coverage=self._coverage(pages, scoped_pages),
            binding_integrity=binding_integrity,
            sequencing=self._sequencing(graphs),
            grounding=self._grounding(pages, review_plan),
            confidence=self._confidence(evidence),
        )

    @staticmethod
    def _coverage(
        pages: Sequence[PagePlan], scoped_pages: Sequence[PageType]
    ) -> Percentage:
        scoped = set(scoped_pages)
        if not scoped:
            return Percentage.of(1.0)
        planned = {p.page_type for p in pages}
        return Percentage.ratio(len(planned & scoped), len(scoped))

    @staticmethod
    def _sequencing(graphs: OrchestratorGraphs) -> Percentage:
        execution = graphs.execution
        ordered = execution.topological_order()
        return Percentage.ratio(len(ordered), len(execution))

    @staticmethod
    def _grounding(pages: Sequence[PagePlan], review_plan: ReviewPlan) -> Percentage:
        citable: list[tuple] = []
        for page in pages:
            for section in page.sections:
                citable.append(section.evidence_ids)
        for checkpoint in review_plan:
            citable.append(checkpoint.evidence_ids)
        if not citable:
            return Percentage.of(0.0)
        grounded = sum(1 for ev in citable if ev)
        return Percentage.ratio(grounded, len(citable))

    @staticmethod
    def _confidence(evidence: EvidenceGraph) -> Confidence:
        items = list(evidence)
        if not items:
            return Confidence.of(0.0)
        return Confidence.clamp(sum(e.confidence.value for e in items) / len(items))
