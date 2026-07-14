"""Wireframe quality metrics — how complete, grounded, and executable the plan is.

:class:`WireframeQualityMetrics` bundles four calibrated measures the engine computes:

* ``coverage`` — the fraction of the required planning outputs actually produced.
* ``grounding`` — the fraction of decisions whose citations resolve (``1.0`` by the plan's
  construction invariant; surfaced explicitly so the metric is auditable).
* ``completeness`` — the fraction of required sections that are execution-ready (carry a
  required component, success criteria, and a review checklist).
* ``confidence`` — the aggregate confidence across the plan.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from wireframe.domain.shared.value_objects import (
    Confidence,
    Percentage,
    QualityBand,
    WFScore,
)

__all__ = ["WireframeQualityMetrics"]

# Weights for the overall score (sum to 1.0).
_W_COVERAGE = 0.3
_W_GROUNDING = 0.3
_W_COMPLETENESS = 0.25
_W_CONFIDENCE = 0.15


@dataclass(frozen=True, slots=True)
class WireframeQualityMetrics:
    """The quality picture of a wireframe plan.

    Attributes:
        coverage: Fraction of required outputs produced.
        grounding: Fraction of decisions with resolvable citations.
        completeness: Fraction of required sections that are execution-ready.
        confidence: Aggregate confidence across the plan.
    """

    coverage: Percentage
    grounding: Percentage
    completeness: Percentage
    confidence: Confidence

    @property
    def overall_score(self) -> WFScore:
        """The weighted 0–100 overall score."""
        raw = (
            _W_COVERAGE * self.coverage.value
            + _W_GROUNDING * self.grounding.value
            + _W_COMPLETENESS * self.completeness.value
            + _W_CONFIDENCE * self.confidence.value
        ) * 100.0
        return WFScore.clamp(raw)

    @property
    def band(self) -> QualityBand:
        return self.overall_score.band

    @property
    def is_fully_grounded(self) -> bool:
        return self.grounding.value >= 1.0
