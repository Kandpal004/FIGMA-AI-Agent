"""Stage — Quality scoring.

Computes the specification's calibrated quality picture deterministically:

* **coverage** — how many of the nineteen visual attributes the language determined.
* **grounding** — the fraction of decisions whose citations resolve (``1.0`` by construction,
  surfaced so it is auditable).
* **consistency** — how well the consistency rules and constraints cover the language's core
  dimensions (a language with no rules is inconsistent by omission).
* **confidence** — the aggregate confidence across the evidence.
"""

from __future__ import annotations

from design_language.application.contracts import LanguageDraft
from design_language.domain.evidence.evidence import EvidenceGraph
from design_language.domain.graph.graphs import DesignLanguageGraphs
from design_language.domain.quality.quality import DesignLanguageQualityMetrics
from design_language.domain.report.report import REQUIRED_PERSONALITIES, REQUIRED_PHILOSOPHIES
from design_language.domain.rules.composition import CompositionRuleSet
from design_language.domain.rules.consistency import ConsistencyRuleSet
from design_language.domain.rules.constraint import ConstraintSet
from design_language.domain.shared.value_objects import Confidence, Percentage

__all__ = ["QualityScorer"]

# The number of distinct core dimensions consistency rules + constraints are expected to cover.
_CORE_DIMENSIONS = 12


class QualityScorer:
    """Scores the language's coverage, grounding, consistency, and confidence."""

    def score(
        self,
        draft: LanguageDraft,
        consistency: ConsistencyRuleSet,
        composition: CompositionRuleSet,
        constraints: ConstraintSet,
        graphs: DesignLanguageGraphs,
        evidence: EvidenceGraph,
    ) -> DesignLanguageQualityMetrics:
        return DesignLanguageQualityMetrics(
            coverage=self._coverage(draft),
            grounding=self._grounding(draft, consistency, composition, constraints, graphs),
            consistency=self._consistency(consistency, constraints),
            confidence=self._confidence(evidence),
        )

    @staticmethod
    def _coverage(draft: LanguageDraft) -> Percentage:
        determined = (
            7
            + len(draft.philosophies.kinds() & REQUIRED_PHILOSOPHIES)
            + len(draft.personalities.kinds() & REQUIRED_PERSONALITIES)
        )
        return Percentage.ratio(determined, 19)

    @staticmethod
    def _grounding(
        draft: LanguageDraft,
        consistency: ConsistencyRuleSet,
        composition: CompositionRuleSet,
        constraints: ConstraintSet,
        graphs: DesignLanguageGraphs,
    ) -> Percentage:
        citable: list[tuple] = [
            draft.visual_dna.all_evidence_ids(),
            draft.tokens.all_evidence_ids(),
            draft.grid_system.all_evidence_ids(),
            draft.responsive_strategy.all_evidence_ids(),
            draft.language_selection.all_evidence_ids(),
        ]
        citable.extend(p.all_evidence_ids() for p in draft.philosophies)
        citable.extend(p.all_evidence_ids() for p in draft.personalities)
        citable.extend(r.all_evidence_ids() for r in consistency)
        citable.extend(r.all_evidence_ids() for r in composition)
        citable.extend(c.all_evidence_ids() for c in constraints)
        for graph in graphs.all():
            citable.extend(n.evidence_ids for n in graph)
        if not citable:
            return Percentage(0.0)
        grounded = sum(1 for ev in citable if ev)
        return Percentage.ratio(grounded, len(citable))

    @staticmethod
    def _consistency(
        consistency: ConsistencyRuleSet, constraints: ConstraintSet
    ) -> Percentage:
        return Percentage.ratio(len(consistency) + len(constraints), _CORE_DIMENSIONS)

    @staticmethod
    def _confidence(evidence: EvidenceGraph) -> Confidence:
        items = list(evidence)
        if not items:
            return Confidence.of(0.0)
        return Confidence.clamp(sum(e.confidence.value for e in items) / len(items))
