"""ConfidenceCalculator — a deterministic measure of how sound a strategy is.

Confidence is computed, never guessed. Per dimension it is the mean confidence of
the evidence cited for that dimension, damped when coverage is thin; a dimension
left as a knowledge gap scores a fixed low floor. The overall score is a
stance-weighted mean of the scored dimensions, with a small penalty per gap. Same
inputs → same score, always.

Pure application logic: no I/O, no randomness, no clock.
"""

from __future__ import annotations

from collections.abc import Sequence

from reasoning.domain.confidence.confidence import ConfidenceScore, StrategyConfidence
from reasoning.domain.evidence.evidence import EvidenceGraph
from reasoning.domain.strategy.gap import KnowledgeGap
from reasoning.domain.shared.value_objects import ReasoningDimension, StrategyStance, Weight

__all__ = ["ConfidenceCalculator"]

# Confidence floor assigned to a dimension that is an explicit knowledge gap.
_GAP_FLOOR = 0.2
# The number of evidence items at which a dimension is considered fully covered.
_FULL_COVERAGE = 2
# Penalty applied to the overall score per knowledge gap.
_GAP_PENALTY = 0.05

# Dimensions a stance emphasises (given extra weight in the overall mean).
_STANCE_EMPHASIS: dict[StrategyStance, tuple[ReasoningDimension, ...]] = {
    StrategyStance.CONVERSION_FIRST: (ReasoningDimension.CONVERSION,),
    StrategyStance.BRAND_FIRST: (
        ReasoningDimension.DESIGN_SYSTEM,
        ReasoningDimension.TYPOGRAPHY,
        ReasoningDimension.CREATIVE_REVIEW,
    ),
    StrategyStance.ACCESSIBILITY_FIRST: (ReasoningDimension.ACCESSIBILITY,),
    StrategyStance.TRUST_FIRST: (ReasoningDimension.TRUST_MECHANISMS,),
    StrategyStance.PERFORMANCE_FIRST: (ReasoningDimension.STRUCTURE,),
}
_BASE_WEIGHT = 1.0
_EMPHASIS_WEIGHT = 2.0


class ConfidenceCalculator:
    """Computes a :class:`StrategyConfidence` from the assembled evidence + gaps."""

    def calculate(
        self,
        evidence_graph: EvidenceGraph,
        gaps: Sequence[KnowledgeGap],
        stance: StrategyStance,
    ) -> StrategyConfidence:
        """Return the per-dimension and overall confidence for a strategy."""
        gap_dimensions = {gap.dimension for gap in gaps}
        per_dimension: dict[ReasoningDimension, ConfidenceScore] = {}

        for dimension in ReasoningDimension:
            evidence = evidence_graph.by_dimension(dimension)
            if evidence:
                mean = sum(e.confidence for e in evidence) / len(evidence)
                coverage = min(1.0, len(evidence) / _FULL_COVERAGE)
                # Blend mean confidence with coverage (thin coverage damps a
                # high mean toward moderate).
                score = mean * (0.5 + 0.5 * coverage)
                per_dimension[dimension] = ConfidenceScore.clamp(score)
            elif dimension in gap_dimensions:
                per_dimension[dimension] = ConfidenceScore.of(_GAP_FLOOR)

        overall = self._overall(per_dimension, stance, len(gaps))
        return StrategyConfidence(overall=overall, by_dimension=per_dimension)

    def _overall(
        self,
        per_dimension: dict[ReasoningDimension, ConfidenceScore],
        stance: StrategyStance,
        gap_count: int,
    ) -> ConfidenceScore:
        if not per_dimension:
            return ConfidenceScore.of(0.0)
        emphasised = set(_STANCE_EMPHASIS.get(stance, ()))
        weighted_sum = 0.0
        total_weight = 0.0
        for dimension, score in per_dimension.items():
            weight = _EMPHASIS_WEIGHT if dimension in emphasised else _BASE_WEIGHT
            weighted_sum += score.value * weight
            total_weight += weight
        base = weighted_sum / total_weight
        penalty = _GAP_PENALTY * gap_count
        return ConfidenceScore.clamp(base - penalty)

    @staticmethod
    def dimension_weight(stance: StrategyStance, dimension: ReasoningDimension) -> Weight:
        """The weight a stance gives a dimension (exposed for callers/tests)."""
        emphasised = set(_STANCE_EMPHASIS.get(stance, ()))
        raw = _EMPHASIS_WEIGHT if dimension in emphasised else _BASE_WEIGHT
        return Weight.of(min(1.0, raw / _EMPHASIS_WEIGHT))
