"""Psychology quality metrics — how complete, grounded, and rigorous the model is.

:class:`PsychologyQualityMetrics` bundles four calibrated measures the engine computes:

* ``coverage`` — the fraction of the required outputs actually produced.
* ``grounding`` — the fraction of findings whose citations resolve (``1.0`` by the
  report's construction invariant; surfaced explicitly so the metric is auditable).
* ``confidence`` — the aggregate confidence across the model.
* ``framework_validation`` — the fraction of the required behavioral frameworks
  (Maslow / Fogg / Hook / JTBD / behavioral economics) actually applied — the rigour
  check that keeps the model scientific, not anecdotal.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from psychology.domain.shared.value_objects import (
    Confidence,
    Percentage,
    PsychScore,
    QualityBand,
)

__all__ = ["PsychologyQualityMetrics"]

# Weights for the overall score (sum to 1.0).
_W_COVERAGE = 0.3
_W_GROUNDING = 0.3
_W_FRAMEWORK = 0.25
_W_CONFIDENCE = 0.15


@dataclass(frozen=True, slots=True)
class PsychologyQualityMetrics:
    """The quality picture of a customer psychology report.

    Attributes:
        coverage: Fraction of required outputs produced.
        grounding: Fraction of findings with resolvable citations.
        framework_validation: Fraction of required frameworks applied.
        confidence: Aggregate confidence across the model.
    """

    coverage: Percentage
    grounding: Percentage
    framework_validation: Percentage
    confidence: Confidence

    @property
    def overall_score(self) -> PsychScore:
        """The weighted 0–100 overall score."""
        raw = (
            _W_COVERAGE * self.coverage.value
            + _W_GROUNDING * self.grounding.value
            + _W_FRAMEWORK * self.framework_validation.value
            + _W_CONFIDENCE * self.confidence.value
        ) * 100.0
        return PsychScore.clamp(raw)

    @property
    def band(self) -> QualityBand:
        return self.overall_score.band

    @property
    def is_fully_grounded(self) -> bool:
        return self.grounding.value >= 1.0
