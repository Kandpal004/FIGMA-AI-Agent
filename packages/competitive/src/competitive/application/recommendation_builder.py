"""RecommendationBuilder — the engine's actionable, evidence-backed output.

Turns adopt-recommended patterns and material, grounded gaps into
:class:`Recommendation` s. Because a recommendation *requires* evidence at
construction, only grounded findings become recommendations — enforcing "no
opinion-based recommendations". Priority is deterministic, boosted for dimensions
the (optional) strategy digest flags as priorities.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from competitive.domain.evidence.evidence import EvidenceRef
from competitive.domain.matrix.gap import GapAnalysis
from competitive.domain.matrix.recommendation import Recommendation, RecommendationMatrix
from competitive.domain.pattern.pattern import RecurringPattern
from competitive.domain.shared.ids import RecommendationId
from competitive.domain.shared.value_objects import (
    CompetitorDimension as Dim,
    Confidence,
    Prevalence,
    PrevalenceBand,
    RecommendationAction,
    Severity,
)

__all__ = ["RecommendationBuilder"]


def _priority(prevalence: Prevalence, is_priority: bool) -> Severity:
    if is_priority:
        return Severity.CRITICAL
    band = prevalence.band
    if band is PrevalenceBand.UBIQUITOUS:
        return Severity.HIGH
    if band is PrevalenceBand.COMMON:
        return Severity.MEDIUM
    return Severity.LOW


class RecommendationBuilder:
    """Builds a :class:`RecommendationMatrix` from patterns and gaps."""

    def build(
        self,
        patterns: tuple[RecurringPattern, ...],
        gap_analysis: GapAnalysis,
        evidence_by_dimension: Mapping[Dim, tuple[EvidenceRef, ...]],
        *,
        priority_dimensions: Sequence[Dim] = (),
    ) -> RecommendationMatrix:
        priority_set = set(priority_dimensions)
        recommendations: list[Recommendation] = []

        for pattern in patterns:
            if pattern.action is not RecommendationAction.ADOPT:
                continue
            recommendations.append(
                Recommendation(
                    id=RecommendationId.new(),
                    action=RecommendationAction.ADOPT,
                    dimension=pattern.dimension,
                    title=f"Adopt {pattern.name}",
                    rationale=(
                        f"{pattern.prevalence.band.value} across competitors "
                        f"({pattern.prevalence.count}/{pattern.prevalence.total})."
                    ),
                    priority=_priority(pattern.prevalence, pattern.dimension in priority_set),
                    confidence=pattern.confidence,
                    evidence_ids=list(pattern.evidence_ids),
                    pattern_id=pattern.id,
                )
            )

        for gap in gap_analysis.gaps:
            if not (gap.is_material and gap.evidence_ids and int(gap.severity) >= int(Severity.MEDIUM)):
                continue
            label = gap.dimension.value.replace("_", " ")
            priority = Severity.CRITICAL if gap.dimension in priority_set else gap.severity
            recommendations.append(
                Recommendation(
                    id=RecommendationId.new(),
                    action=RecommendationAction.ADOPT,
                    dimension=gap.dimension,
                    title=f"Close the gap on {label}",
                    rationale=f"Client trails the category benchmark by {gap.size:.0f} points.",
                    priority=priority,
                    confidence=Confidence.of(0.7),
                    evidence_ids=list(gap.evidence_ids),
                )
            )

        return RecommendationMatrix(recommendations=tuple(recommendations))
