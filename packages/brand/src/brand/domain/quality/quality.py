"""Brand quality metrics — how complete, grounded, and coherent the brand is.

:class:`BrandQualityMetrics` bundles four calibrated measures the engine computes:

* ``coverage`` — the fraction of the required brand outputs actually produced.
* ``grounding`` — the fraction of brand decisions whose citations resolve (``1.0`` by
  the report's construction invariant; surfaced explicitly so the metric is auditable).
* ``confidence`` — the aggregate confidence across decisions.
* ``coherence`` — how well the brand's parts align with one another (does the visual
  direction express the archetype? does the voice match the classification?). This is
  the Interbrand "coherence" lens, computed deterministically.

The values are computed by the engine; this is the value model they populate, with a
single 0–100 overall score.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from brand.domain.shared.value_objects import (
    BrandScore,
    Confidence,
    Percentage,
    QualityBand,
)

__all__ = ["BrandQualityMetrics"]

# Weights for the overall score (sum to 1.0).
_W_COVERAGE = 0.3
_W_GROUNDING = 0.3
_W_COHERENCE = 0.25
_W_CONFIDENCE = 0.15


@dataclass(frozen=True, slots=True)
class BrandQualityMetrics:
    """The quality picture of a brand strategy report.

    Attributes:
        coverage: Fraction of required outputs produced.
        grounding: Fraction of decisions with resolvable citations.
        coherence: How well the brand's parts align.
        confidence: Aggregate confidence across decisions.
    """

    coverage: Percentage
    grounding: Percentage
    coherence: Percentage
    confidence: Confidence

    @property
    def overall_score(self) -> BrandScore:
        """The weighted 0–100 overall score."""
        raw = (
            _W_COVERAGE * self.coverage.value
            + _W_GROUNDING * self.grounding.value
            + _W_COHERENCE * self.coherence.value
            + _W_CONFIDENCE * self.confidence.value
        ) * 100.0
        return BrandScore.clamp(raw)

    @property
    def band(self) -> QualityBand:
        return self.overall_score.band

    @property
    def is_fully_grounded(self) -> bool:
        return self.grounding.value >= 1.0
