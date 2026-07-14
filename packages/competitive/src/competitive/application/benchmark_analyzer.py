"""BenchmarkAnalyzer — builds the competitors × dimensions score grid.

Each cell is a competitor's profile score on a dimension. The category benchmark per
dimension is the deterministic top-quartile of competitor scores (the bar to clear);
the client's own scores come from the brief. Pure application logic.
"""

from __future__ import annotations

from collections.abc import Sequence

from competitive.domain.competitor.profile import CompetitorProfile
from competitive.domain.matrix.benchmark import BenchmarkCell, BenchmarkMatrix
from competitive.domain.report.brief import CompetitiveBrief
from competitive.domain.shared.value_objects import CompetitorDimension, Score

__all__ = ["BenchmarkAnalyzer"]


def _percentile(values: Sequence[float], pct: float) -> float:
    """The deterministic ``pct`` (0–1) percentile of ``values`` (nearest-rank)."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = round(pct * (len(ordered) - 1))
    return ordered[index]


class BenchmarkAnalyzer:
    """Builds a :class:`BenchmarkMatrix` from competitor profiles and the brief."""

    def build(
        self, profiles: tuple[CompetitorProfile, ...], brief: CompetitiveBrief
    ) -> BenchmarkMatrix:
        cells: list[BenchmarkCell] = []
        dimensions: list[CompetitorDimension] = []
        for profile in profiles:
            for assessment in profile.assessments:
                cells.append(
                    BenchmarkCell(profile.competitor_id, assessment.dimension, assessment.score)
                )
                if assessment.dimension not in dimensions:
                    dimensions.append(assessment.dimension)

        category_benchmarks: dict[CompetitorDimension, Score] = {}
        for dimension in dimensions:
            scores = [
                a.score.value
                for p in profiles
                for a in p.assessments
                if a.dimension is dimension
            ]
            category_benchmarks[dimension] = Score.clamp(_percentile(scores, 0.75))

        return BenchmarkMatrix.build(
            cells=cells,
            client_scores=dict(brief.client_baseline),
            category_benchmarks=category_benchmarks,
        )
