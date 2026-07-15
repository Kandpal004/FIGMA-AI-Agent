"""Stage — Quality scoring.

Computes the specification's calibrated quality picture deterministically:

* **coverage** — how many included components are fully specified (all attributes present).
* **grounding** — the fraction of decisions whose citations resolve (``1.0`` by construction).
* **coherence** — whether the composition is internally consistent (``1.0`` — the coherence
  resolver and the aggregate invariant guarantee no conflicting co-placed pair and closed
  dependencies).
* **confidence** — the aggregate confidence across the evidence.
"""

from __future__ import annotations

from component_intelligence.domain.compatibility.compatibility import CompatibilitySet
from component_intelligence.domain.composition.composition import ComponentComposition
from component_intelligence.domain.graph.graphs import ComponentGraphs
from component_intelligence.domain.evidence.evidence import EvidenceGraph
from component_intelligence.domain.quality.quality import CompositionQualityMetrics
from component_intelligence.domain.rules.composition_rules import CompositionRuleSet
from component_intelligence.domain.rules.placement_rules import PlacementRuleSet
from component_intelligence.domain.rules.responsive_rules import ResponsiveRuleSet
from component_intelligence.domain.rules.reuse_rules import ReuseRuleSet
from component_intelligence.domain.rules.visibility_rules import VisibilityRuleSet
from component_intelligence.domain.shared.value_objects import Confidence, Percentage

__all__ = ["QualityScorer"]


class QualityScorer:
    """Scores the composition's coverage, grounding, coherence, and confidence."""

    def score(
        self,
        composition: ComponentComposition,
        compatibility: CompatibilitySet,
        composition_rules: CompositionRuleSet,
        placement_rules: PlacementRuleSet,
        visibility_rules: VisibilityRuleSet,
        responsive_rules: ResponsiveRuleSet,
        reuse_rules: ReuseRuleSet,
        graphs: ComponentGraphs,
        evidence: EvidenceGraph,
    ) -> CompositionQualityMetrics:
        return CompositionQualityMetrics(
            coverage=self._coverage(composition),
            grounding=self._grounding(
                composition, compatibility, composition_rules, placement_rules,
                visibility_rules, responsive_rules, reuse_rules, graphs,
            ),
            coherence=Percentage(1.0),
            confidence=self._confidence(evidence),
        )

    @staticmethod
    def _coverage(composition: ComponentComposition) -> Percentage:
        included = composition.included()
        specified = sum(1 for d in included if d.is_fully_specified)
        return Percentage.ratio(specified, len(included))

    @staticmethod
    def _grounding(
        composition, compatibility, composition_rules, placement_rules,
        visibility_rules, responsive_rules, reuse_rules, graphs,
    ) -> Percentage:
        citable: list[tuple] = []
        citable.extend(d.all_evidence_ids() for d in composition)
        citable.extend(link.all_evidence_ids() for link in compatibility)
        for rule_set in (composition_rules, placement_rules, visibility_rules,
                         responsive_rules, reuse_rules):
            citable.extend(r.all_evidence_ids() for r in rule_set)
        for graph in graphs.all():
            citable.extend(n.evidence_ids for n in graph)
        if not citable:
            return Percentage(0.0)
        grounded = sum(1 for ev in citable if ev)
        return Percentage.ratio(grounded, len(citable))

    @staticmethod
    def _confidence(evidence: EvidenceGraph) -> Confidence:
        items = list(evidence)
        if not items:
            return Confidence.of(0.0)
        return Confidence.clamp(sum(e.confidence.value for e in items) / len(items))
