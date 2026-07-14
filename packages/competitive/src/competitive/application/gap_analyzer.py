"""GapAnalyzer — measures the client against the category benchmark.

For each benchmarked dimension it computes the client's gap to the category
benchmark, bands its severity, and — for material gaps — grounds the recommended
action in Knowledge evidence. Deterministic.
"""

from __future__ import annotations

from collections.abc import Mapping

from competitive.domain.evidence.evidence import EvidenceRef
from competitive.domain.matrix.benchmark import BenchmarkMatrix
from competitive.domain.matrix.gap import Gap, GapAnalysis
from competitive.domain.shared.value_objects import (
    CompetitorDimension as Dim,
    RecommendationAction,
    Severity,
)

__all__ = ["GapAnalyzer"]


def _severity(size: float) -> Severity:
    if size >= 40.0:
        return Severity.CRITICAL
    if size >= 25.0:
        return Severity.HIGH
    if size >= 10.0:
        return Severity.MEDIUM
    return Severity.LOW


class GapAnalyzer:
    """Builds a :class:`GapAnalysis` from the benchmark matrix."""

    def analyze(
        self,
        benchmark: BenchmarkMatrix,
        evidence_by_dimension: Mapping[Dim, tuple[EvidenceRef, ...]],
    ) -> GapAnalysis:
        gaps: list[Gap] = []
        for dimension in benchmark.dimensions():
            client = benchmark.client_score(dimension)
            category = benchmark.category_benchmark(dimension)
            size = max(0.0, category.value - client.value)
            if size > 0.0:
                action = RecommendationAction.ADOPT
                evidence_ids = [e.id for e in evidence_by_dimension.get(dimension, ())]
            else:
                action = RecommendationAction.MONITOR
                evidence_ids = []
            gaps.append(
                Gap(
                    dimension=dimension,
                    client_score=client,
                    benchmark_score=category,
                    severity=_severity(size),
                    recommended_action=action,
                    evidence_ids=evidence_ids,
                )
            )
        return GapAnalysis(gaps=tuple(gaps))
