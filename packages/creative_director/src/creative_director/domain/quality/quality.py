"""Review quality metrics — how complete and grounded the *review itself* is.

Distinct from the scorecard (which judges the subject), :class:`ReviewQualityMetrics` judges
the review: how many of the sixteen dimensions were actually reviewed (coverage), the
fraction of rulings whose citations resolve (grounding — ``1.0`` by construction, surfaced so
it is auditable), and the engine's aggregate confidence. A review that skips dimensions or
rules without evidence is itself low-quality, and the platform can see that.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from creative_director.domain.shared.value_objects import (
    Confidence,
    Percentage,
    QualityBand,
    Score,
)

__all__ = ["ReviewQualityMetrics"]

_W_COVERAGE = 0.4
_W_GROUNDING = 0.4
_W_CONFIDENCE = 0.2


@dataclass(frozen=True, slots=True)
class ReviewQualityMetrics:
    """The meta-quality of a Creative Director review.

    Attributes:
        coverage: Fraction of the sixteen dimensions actually reviewed.
        grounding: Fraction of rulings with resolvable citations.
        confidence: Aggregate confidence across the review.
    """

    coverage: Percentage
    grounding: Percentage
    confidence: Confidence

    @property
    def overall_score(self) -> Score:
        """The weighted 0–100 meta-quality of the review."""
        raw = (
            _W_COVERAGE * self.coverage.value
            + _W_GROUNDING * self.grounding.value
            + _W_CONFIDENCE * self.confidence.value
        ) * 100.0
        return Score.clamp(raw)

    @property
    def band(self) -> QualityBand:
        return self.overall_score.band

    @property
    def is_fully_grounded(self) -> bool:
        return self.grounding.value >= 1.0
