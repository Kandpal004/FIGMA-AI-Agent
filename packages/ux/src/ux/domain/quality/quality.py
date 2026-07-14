"""UX quality metrics — how complete, grounded, and principled the strategy is.

:class:`UXQualityMetrics` bundles four calibrated measures the engine computes:

* ``coverage`` — the fraction of the required outputs actually produced.
* ``grounding`` — the fraction of decisions whose citations resolve (``1.0`` by the
  report's construction invariant; surfaced explicitly so the metric is auditable).
* ``confidence`` — the aggregate confidence across the strategy.
* ``heuristic_validation`` — the fraction of the eleven UX laws/heuristics actually
  applied — the rigour check that keeps the strategy principled, not arbitrary.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from ux.domain.shared.value_objects import (
    Confidence,
    Percentage,
    QualityBand,
    UXScore,
)

__all__ = ["UXQualityMetrics"]

# Weights for the overall score (sum to 1.0).
_W_COVERAGE = 0.3
_W_GROUNDING = 0.3
_W_HEURISTIC = 0.25
_W_CONFIDENCE = 0.15


@dataclass(frozen=True, slots=True)
class UXQualityMetrics:
    """The quality picture of a UX strategy report.

    Attributes:
        coverage: Fraction of required outputs produced.
        grounding: Fraction of decisions with resolvable citations.
        heuristic_validation: Fraction of the eleven UX laws applied.
        confidence: Aggregate confidence across the strategy.
    """

    coverage: Percentage
    grounding: Percentage
    heuristic_validation: Percentage
    confidence: Confidence

    @property
    def overall_score(self) -> UXScore:
        """The weighted 0–100 overall score."""
        raw = (
            _W_COVERAGE * self.coverage.value
            + _W_GROUNDING * self.grounding.value
            + _W_HEURISTIC * self.heuristic_validation.value
            + _W_CONFIDENCE * self.confidence.value
        ) * 100.0
        return UXScore.clamp(raw)

    @property
    def band(self) -> QualityBand:
        return self.overall_score.band

    @property
    def is_fully_grounded(self) -> bool:
        return self.grounding.value >= 1.0
