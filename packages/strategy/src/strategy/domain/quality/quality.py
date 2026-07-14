"""Strategy quality metrics — how good, and how grounded, the strategy is.

:class:`StrategyQualityMetrics` bundles four calibrated measures the engine computes:

* ``coverage`` — the fraction of the required strategic outputs actually produced.
* ``grounding`` — the fraction of strategic decisions whose citations resolve. By the
  report's construction invariant this is always ``1.0``; it is surfaced explicitly so
  the metric is auditable, not assumed.
* ``confidence`` — the aggregate confidence across decisions.
* ``completeness`` — how fully the customer/positioning/messaging picture is filled in.

The values are computed by the engine (deterministically); this is the value model
they populate, with a single 0–100 overall score.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from strategy.domain.shared.value_objects import (
    Confidence,
    Percentage,
    QualityBand,
    StrategyScore,
)

__all__ = ["StrategyQualityMetrics"]

# Weights for the overall score (sum to 1.0).
_W_COVERAGE = 0.3
_W_GROUNDING = 0.3
_W_CONFIDENCE = 0.25
_W_COMPLETENESS = 0.15


@dataclass(frozen=True, slots=True)
class StrategyQualityMetrics:
    """The quality picture of a strategy report.

    Attributes:
        coverage: Fraction of required outputs produced.
        grounding: Fraction of decisions with resolvable citations.
        confidence: Aggregate confidence across decisions.
        completeness: How fully the strategy picture is filled in.
    """

    coverage: Percentage
    grounding: Percentage
    confidence: Confidence
    completeness: Percentage

    @property
    def overall_score(self) -> StrategyScore:
        """The weighted 0–100 overall score."""
        raw = (
            _W_COVERAGE * self.coverage.value
            + _W_GROUNDING * self.grounding.value
            + _W_CONFIDENCE * self.confidence.value
            + _W_COMPLETENESS * self.completeness.value
        ) * 100.0
        return StrategyScore.clamp(raw)

    @property
    def band(self) -> QualityBand:
        return self.overall_score.band

    @property
    def is_fully_grounded(self) -> bool:
        return self.grounding.value >= 1.0
