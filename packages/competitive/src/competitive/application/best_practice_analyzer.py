"""BestPracticeAnalyzer — promotes adopt-recommended patterns to best practices.

A pattern the engine recommends adopting (which, by construction, is grounded in
Knowledge evidence) becomes a :class:`BestPractice`. Deterministic; carries the
pattern's citations forward.
"""

from __future__ import annotations

from competitive.domain.matrix.best_practice import BestPractice, BestPracticeMatrix
from competitive.domain.pattern.pattern import RecurringPattern
from competitive.domain.shared.value_objects import RecommendationAction

__all__ = ["BestPracticeAnalyzer"]


class BestPracticeAnalyzer:
    """Builds a :class:`BestPracticeMatrix` from adopt-recommended patterns."""

    def build(self, patterns: tuple[RecurringPattern, ...]) -> BestPracticeMatrix:
        practices = [
            BestPractice(
                pattern_id=pattern.id,
                kind=pattern.kind,
                dimension=pattern.dimension,
                name=pattern.name,
                description=pattern.description,
                prevalence=pattern.prevalence,
                confidence=pattern.confidence,
                evidence_ids=pattern.evidence_ids,
            )
            for pattern in patterns
            if pattern.action is RecommendationAction.ADOPT
        ]
        return BestPracticeMatrix(practices=tuple(practices))
