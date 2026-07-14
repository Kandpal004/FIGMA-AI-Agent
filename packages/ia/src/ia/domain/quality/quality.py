"""IA quality metrics — how complete, grounded, and structurally sound the IA is.

:class:`IAQualityMetrics` bundles four calibrated measures the engine computes:

* ``coverage`` — the fraction of the required outputs actually produced.
* ``grounding`` — the fraction of decisions whose citations resolve (``1.0`` by the
  report's construction invariant; surfaced explicitly so the metric is auditable).
* ``confidence`` — the aggregate confidence across the architecture.
* ``completeness`` — the fraction of required pages that carry at least one required
  section — the structural-completeness check that keeps the blueprint buildable.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from ia.domain.shared.value_objects import (
    Confidence,
    IAScore,
    Percentage,
    QualityBand,
)

__all__ = ["IAQualityMetrics"]

# Weights for the overall score (sum to 1.0).
_W_COVERAGE = 0.3
_W_GROUNDING = 0.3
_W_COMPLETENESS = 0.25
_W_CONFIDENCE = 0.15


@dataclass(frozen=True, slots=True)
class IAQualityMetrics:
    """The quality picture of an IA report.

    Attributes:
        coverage: Fraction of required outputs produced.
        grounding: Fraction of decisions with resolvable citations.
        completeness: Fraction of required pages with a required section.
        confidence: Aggregate confidence across the architecture.
    """

    coverage: Percentage
    grounding: Percentage
    completeness: Percentage
    confidence: Confidence

    @property
    def overall_score(self) -> IAScore:
        """The weighted 0–100 overall score."""
        raw = (
            _W_COVERAGE * self.coverage.value
            + _W_GROUNDING * self.grounding.value
            + _W_COMPLETENESS * self.completeness.value
            + _W_CONFIDENCE * self.confidence.value
        ) * 100.0
        return IAScore.clamp(raw)

    @property
    def band(self) -> QualityBand:
        return self.overall_score.band

    @property
    def is_fully_grounded(self) -> bool:
        return self.grounding.value >= 1.0
