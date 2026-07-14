"""Stage — Matrix construction.

Projects the review into its two read-model matrices: the :class:`QualityMatrix` (the
scorecard as an at-a-glance category grid) and the :class:`ImprovementMatrix` (every required
change the review demands, ranked into a remediation plan). Both are deterministic projections
of already-computed material.
"""

from __future__ import annotations

from collections.abc import Sequence

from creative_director.domain.finding.finding import RequiredChange
from creative_director.domain.matrix.improvement_matrix import ImprovementMatrix
from creative_director.domain.matrix.quality_matrix import QualityMatrix
from creative_director.domain.review.dimension_review import DimensionReview
from creative_director.domain.scoring.scorecard import Scorecard

__all__ = ["MatrixBuilder"]


class MatrixBuilder:
    """Builds the quality and improvement matrices."""

    def quality(self, scorecard: Scorecard) -> QualityMatrix:
        return QualityMatrix.from_scorecard(scorecard)

    def improvement(
        self, dimension_reviews: Sequence[DimensionReview]
    ) -> ImprovementMatrix:
        changes = self.collect_changes(dimension_reviews)
        return ImprovementMatrix.of(changes)

    @staticmethod
    def collect_changes(
        dimension_reviews: Sequence[DimensionReview],
    ) -> tuple[RequiredChange, ...]:
        return tuple(c for dr in dimension_reviews for c in dr.required_changes)
