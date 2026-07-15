"""Stage — Quality scoring.

Computes the model's calibrated quality picture deterministically:

* **reference_integrity** — passed through from the binding resolver (``1.0`` when every binding,
  style ref, and instance resolves).
* **mode_parity** — ``1.0`` when every variable values every mode of its collection (guaranteed by
  the collection invariant; surfaced for auditability).
* **structure** — ``1.0`` when every page tree and all five graphs are well-formed (guaranteed by
  the respective models).
* **grounding** — the fraction of elements (nodes + component sets) that cite evidence (``1.0`` by
  construction).
* **confidence** — the aggregate confidence across the evidence.
"""

from __future__ import annotations

from collections.abc import Sequence

from figma_design.domain.component.component_set import ComponentSetCatalog
from figma_design.domain.evidence.evidence import EvidenceGraph
from figma_design.domain.page.page import FigmaPage
from figma_design.domain.quality.quality import FigmaModelQualityMetrics
from figma_design.domain.shared.value_objects import Confidence, Percentage
from figma_design.domain.variable.collection import VariableCollection

__all__ = ["QualityScorer"]


class QualityScorer:
    """Scores the model's reference integrity, mode parity, structure, grounding, confidence."""

    def score(
        self,
        pages: Sequence[FigmaPage],
        collections: Sequence[VariableCollection],
        component_sets: ComponentSetCatalog,
        evidence: EvidenceGraph,
        reference_integrity: Percentage,
    ) -> FigmaModelQualityMetrics:
        return FigmaModelQualityMetrics(
            reference_integrity=reference_integrity,
            mode_parity=self._mode_parity(collections),
            structure=Percentage.of(1.0),
            grounding=self._grounding(pages, component_sets),
            confidence=self._confidence(evidence),
        )

    @staticmethod
    def _mode_parity(collections: Sequence[VariableCollection]) -> Percentage:
        # Collections enforce mode parity at construction; surfaced here for auditability.
        return Percentage.of(1.0)

    @staticmethod
    def _grounding(
        pages: Sequence[FigmaPage], component_sets: ComponentSetCatalog
    ) -> Percentage:
        citable: list[tuple] = []
        for page in pages:
            for node in page.tree:
                citable.append(node.evidence_ids)
        for component_set in component_sets:
            citable.append(component_set.evidence_ids)
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
