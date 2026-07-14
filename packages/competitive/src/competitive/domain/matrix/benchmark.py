"""The Benchmark matrix — competitors × dimensions, scored 0–100.

Each :class:`BenchmarkCell` is one competitor's normalized score on one dimension.
The :class:`BenchmarkMatrix` holds every cell plus the client's own scores and the
category benchmark (the bar to clear) per dimension, so a competitor's standing can
be read as a :class:`BenchmarkBand` relative to that bar, and gaps compute directly.

Pure domain: standard library, the shared-kernel error base, competitive ids, and
shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from competitive.domain.shared.ids import CompetitorId
from competitive.domain.shared.value_objects import (
    BenchmarkBand,
    CompetitorDimension,
    Score,
)

__all__ = ["BenchmarkCell", "BenchmarkMatrix", "InvalidBenchmarkError"]


class InvalidBenchmarkError(DesignDirectorError):
    """Raised when a benchmark cell or matrix is constructed with invalid data."""

    code = "invalid_benchmark"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BenchmarkCell:
    """One competitor's score on one dimension.

    Attributes:
        competitor_id: The competitor.
        dimension: The dimension.
        score: The 0–100 benchmark score.
    """

    competitor_id: CompetitorId
    dimension: CompetitorDimension
    score: Score

    def band(self, benchmark: Score) -> BenchmarkBand:
        """This cell's band relative to a category benchmark."""
        return BenchmarkBand.from_relative(self.score, benchmark)


@dataclass(frozen=True, slots=True)
class BenchmarkMatrix:
    """The full benchmark grid plus client scores and category benchmarks.

    Attributes:
        cells: One cell per (competitor, dimension).
        client_scores: The client's own score per dimension.
        category_benchmarks: The category bar (e.g. top-quartile) per dimension.
    """

    cells: tuple[BenchmarkCell, ...] = ()
    client_scores: Mapping[CompetitorDimension, Score] = field(
        default_factory=lambda: MappingProxyType({})
    )
    category_benchmarks: Mapping[CompetitorDimension, Score] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "cells", tuple(self.cells))
        if not isinstance(self.client_scores, MappingProxyType):
            object.__setattr__(self, "client_scores", MappingProxyType(dict(self.client_scores)))
        if not isinstance(self.category_benchmarks, MappingProxyType):
            object.__setattr__(
                self, "category_benchmarks", MappingProxyType(dict(self.category_benchmarks))
            )

    def dimensions(self) -> tuple[CompetitorDimension, ...]:
        """The dimensions present, in first-seen order."""
        seen: list[CompetitorDimension] = []
        for cell in self.cells:
            if cell.dimension not in seen:
                seen.append(cell.dimension)
        return tuple(seen)

    def competitor_ids(self) -> tuple[CompetitorId, ...]:
        """The competitors present, in first-seen order."""
        seen: list[CompetitorId] = []
        for cell in self.cells:
            if cell.competitor_id not in seen:
                seen.append(cell.competitor_id)
        return tuple(seen)

    def score(
        self, competitor_id: CompetitorId, dimension: CompetitorDimension
    ) -> Score | None:
        """A competitor's score on a dimension, or ``None`` if absent."""
        for cell in self.cells:
            if cell.competitor_id == competitor_id and cell.dimension is dimension:
                return cell.score
        return None

    def category_benchmark(self, dimension: CompetitorDimension) -> Score:
        """The category benchmark for a dimension (``0`` if unknown)."""
        return self.category_benchmarks.get(dimension, Score.zero())

    def client_score(self, dimension: CompetitorDimension) -> Score:
        """The client's score on a dimension (``0`` if unknown)."""
        return self.client_scores.get(dimension, Score.zero())

    def band(
        self, competitor_id: CompetitorId, dimension: CompetitorDimension
    ) -> BenchmarkBand | None:
        """A competitor's band on a dimension relative to the category benchmark."""
        cell_score = self.score(competitor_id, dimension)
        if cell_score is None:
            return None
        return BenchmarkBand.from_relative(cell_score, self.category_benchmark(dimension))

    def client_band(self, dimension: CompetitorDimension) -> BenchmarkBand:
        """The client's band on a dimension relative to the category benchmark."""
        return BenchmarkBand.from_relative(
            self.client_score(dimension), self.category_benchmark(dimension)
        )

    @classmethod
    def build(
        cls,
        cells: Iterable[BenchmarkCell],
        *,
        client_scores: Mapping[CompetitorDimension, Score] | None = None,
        category_benchmarks: Mapping[CompetitorDimension, Score] | None = None,
    ) -> BenchmarkMatrix:
        return cls(
            cells=tuple(cells),
            client_scores=MappingProxyType(dict(client_scores or {})),
            category_benchmarks=MappingProxyType(dict(category_benchmarks or {})),
        )
