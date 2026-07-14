"""The Gap Analysis model — where the client stands versus the category.

A :class:`Gap` measures, for one dimension, the distance between the client's score
and the category benchmark, with a severity band and a grounded recommended action.
:class:`GapAnalysis` aggregates the gaps into an overall index and surfaces the
priority gaps. This is the bridge from "where we stand" to "what to do".

Pure domain: standard library, the shared-kernel error base, competitive ids, and
shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from competitive.domain.shared.ids import EvidenceId
from competitive.domain.shared.value_objects import (
    CompetitorDimension,
    RecommendationAction,
    Score,
    Severity,
)

__all__ = ["Gap", "GapAnalysis", "InvalidGapError"]


class InvalidGapError(DesignDirectorError):
    """Raised when a gap is constructed with invalid data."""

    code = "invalid_gap"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Gap:
    """The client's gap on one dimension against the category benchmark.

    Attributes:
        dimension: The dimension.
        client_score: The client's score.
        benchmark_score: The category benchmark to reach.
        severity: How material the gap is.
        recommended_action: What to do about it.
        evidence_ids: Knowledge citations grounding the action.
    """

    dimension: CompetitorDimension
    client_score: Score
    benchmark_score: Score
    severity: Severity
    recommended_action: RecommendationAction = RecommendationAction.MONITOR
    evidence_ids: tuple[EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def size(self) -> float:
        """The positive distance from the client to the benchmark (0 if ahead)."""
        return max(0.0, self.benchmark_score.value - self.client_score.value)

    @property
    def is_material(self) -> bool:
        """Whether the client trails the benchmark at all."""
        return self.size > 0.0


@dataclass(frozen=True, slots=True)
class GapAnalysis:
    """The client's gaps across all dimensions.

    Attributes:
        gaps: The per-dimension gaps.
    """

    gaps: tuple[Gap, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "gaps", tuple(self.gaps))

    def __len__(self) -> int:
        return len(self.gaps)

    @property
    def overall_gap_index(self) -> float:
        """The mean gap size across dimensions (0–100); higher = further behind."""
        if not self.gaps:
            return 0.0
        return sum(g.size for g in self.gaps) / len(self.gaps)

    def material_gaps(self) -> tuple[Gap, ...]:
        """Only the gaps where the client trails the benchmark."""
        return tuple(g for g in self.gaps if g.is_material)

    def priority_gaps(self, limit: int | None = None) -> tuple[Gap, ...]:
        """Material gaps ranked by severity then size (worst first)."""
        ranked = sorted(
            self.material_gaps(),
            key=lambda g: (int(g.severity), g.size),
            reverse=True,
        )
        return tuple(ranked[:limit] if limit is not None else ranked)

    def gap_for(self, dimension: CompetitorDimension) -> Gap | None:
        for gap in self.gaps:
            if gap.dimension is dimension:
                return gap
        return None
