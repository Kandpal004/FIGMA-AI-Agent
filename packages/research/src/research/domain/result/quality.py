"""Quality metrics — the calibrated measures attached to every result and report.

:class:`QualityMetrics` bundles the four measures the mission requires: a
:class:`QualityScore` (0–100), :class:`Freshness`, :class:`Completeness`, and
:class:`Confidence`. The values are *computed* by the engine (deterministically);
this is the value model they populate.

Pure domain: standard library, the shared-kernel error base, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from core.errors import DesignDirectorError

from research.domain.shared.value_objects import (
    Completeness,
    Confidence,
    Freshness,
    QualityScore,
)

__all__ = ["InvalidQualityError", "QualityMetrics"]


class InvalidQualityError(DesignDirectorError):
    """Raised when quality metrics are constructed inconsistently."""

    code = "invalid_quality"
    http_status = 422


@dataclass(frozen=True, slots=True)
class QualityMetrics:
    """The quality picture of a result or report.

    Attributes:
        quality_score: The overall 0–100 quality score.
        freshness: How fresh the underlying data is.
        completeness: How complete the result is.
        confidence: The aggregate confidence.
    """

    quality_score: QualityScore
    freshness: Freshness
    completeness: Completeness
    confidence: Confidence

    @classmethod
    def aggregate(cls, parts: Sequence[QualityMetrics]) -> QualityMetrics:
        """Combine several metrics by averaging each measure (empty → zeros)."""
        if not parts:
            return cls(
                quality_score=QualityScore.of(0.0),
                freshness=Freshness(0.0),
                completeness=Completeness(0.0),
                confidence=Confidence.of(0.0),
            )
        n = len(parts)
        return cls(
            quality_score=QualityScore.clamp(sum(p.quality_score.value for p in parts) / n),
            freshness=Freshness(sum(p.freshness.value for p in parts) / n),
            completeness=Completeness(sum(p.completeness.value for p in parts) / n),
            confidence=Confidence.clamp(sum(p.confidence.value for p in parts) / n),
        )
