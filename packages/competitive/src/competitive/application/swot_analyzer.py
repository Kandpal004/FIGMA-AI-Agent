"""SwotAnalyzer — derives the client's SWOT from the benchmark and patterns.

Deterministic: strengths where the client leads the category, weaknesses where it
lags, opportunities in dominant patterns the client has not yet led on, threats
where category leaders outpace the client. Weakness/opportunity/threat items carry
Knowledge evidence where available.
"""

from __future__ import annotations

from collections.abc import Mapping

from competitive.domain.evidence.evidence import EvidenceRef
from competitive.domain.matrix.benchmark import BenchmarkMatrix
from competitive.domain.matrix.swot import SWOTItem, SWOTMatrix, SWOTQuadrant
from competitive.domain.pattern.pattern import RecurringPattern
from competitive.domain.shared.value_objects import (
    BenchmarkBand,
    CompetitorDimension as Dim,
    Confidence,
)

__all__ = ["SwotAnalyzer"]

_HIGH_BAR = 70.0


class SwotAnalyzer:
    """Builds a :class:`SWOTMatrix` from the benchmark and detected patterns."""

    def analyze(
        self,
        benchmark: BenchmarkMatrix,
        patterns: tuple[RecurringPattern, ...],
        evidence_by_dimension: Mapping[Dim, tuple[EvidenceRef, ...]],
    ) -> SWOTMatrix:
        items: list[SWOTItem] = []

        for dimension in benchmark.dimensions():
            label = dimension.value.replace("_", " ")
            band = benchmark.client_band(dimension)
            evidence_ids = [e.id for e in evidence_by_dimension.get(dimension, ())]
            if band is BenchmarkBand.LEADER:
                items.append(
                    SWOTItem(
                        quadrant=SWOTQuadrant.STRENGTH,
                        statement=f"Client leads the category on {label}.",
                        confidence=Confidence.of(0.7),
                        dimension=dimension,
                    )
                )
            elif band is BenchmarkBand.LAGGARD:
                items.append(
                    SWOTItem(
                        quadrant=SWOTQuadrant.WEAKNESS,
                        statement=f"Client trails the category on {label}.",
                        confidence=Confidence.of(0.75),
                        dimension=dimension,
                        evidence_ids=evidence_ids,
                    )
                )

        for pattern in patterns:
            if (
                pattern.prevalence.is_dominant
                and pattern.evidence_ids
                and benchmark.client_band(pattern.dimension) is not BenchmarkBand.LEADER
            ):
                items.append(
                    SWOTItem(
                        quadrant=SWOTQuadrant.OPPORTUNITY,
                        statement=f"Adopt the category pattern: {pattern.name}.",
                        confidence=pattern.confidence,
                        dimension=pattern.dimension,
                        evidence_ids=list(pattern.evidence_ids),
                    )
                )

        for dimension in benchmark.dimensions():
            if (
                benchmark.category_benchmark(dimension).value >= _HIGH_BAR
                and benchmark.client_band(dimension) is BenchmarkBand.LAGGARD
            ):
                label = dimension.value.replace("_", " ")
                items.append(
                    SWOTItem(
                        quadrant=SWOTQuadrant.THREAT,
                        statement=f"Category leaders outpace the client on {label}.",
                        confidence=Confidence.of(0.7),
                        dimension=dimension,
                        evidence_ids=[e.id for e in evidence_by_dimension.get(dimension, ())],
                    )
                )

        return SWOTMatrix(items=tuple(items))
