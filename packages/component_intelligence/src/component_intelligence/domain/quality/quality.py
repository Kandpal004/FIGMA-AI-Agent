"""Component-intelligence quality metrics — how complete, grounded, and coherent the spec is.

:class:`CompositionQualityMetrics` bundles four calibrated measures the engine computes:

* ``coverage`` — the fraction of included components that are fully specified (all attributes).
* ``grounding`` — the fraction of decisions whose citations resolve (``1.0`` by construction,
  surfaced so it is auditable).
* ``coherence`` — whether the composition is internally consistent (no conflicting co-placed
  pair, dependencies closed) — ``1.0`` by construction, surfaced for auditability.
* ``confidence`` — the aggregate confidence across the evidence.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from component_intelligence.domain.shared.value_objects import (
    Confidence,
    Percentage,
    QualityBand,
    Score,
)

__all__ = ["CompositionQualityMetrics"]

_W_COVERAGE = 0.3
_W_GROUNDING = 0.3
_W_COHERENCE = 0.25
_W_CONFIDENCE = 0.15


@dataclass(frozen=True, slots=True)
class CompositionQualityMetrics:
    """The quality picture of a component-composition specification.

    Attributes:
        coverage: Fraction of included components that are fully specified.
        grounding: Fraction of decisions with resolvable citations.
        coherence: Whether the composition is internally consistent.
        confidence: Aggregate confidence across the evidence.
    """

    coverage: Percentage
    grounding: Percentage
    coherence: Percentage
    confidence: Confidence

    @property
    def overall_score(self) -> Score:
        """The weighted 0–100 overall score."""
        raw = (
            _W_COVERAGE * self.coverage.value
            + _W_GROUNDING * self.grounding.value
            + _W_COHERENCE * self.coherence.value
            + _W_CONFIDENCE * self.confidence.value
        ) * 100.0
        return Score.clamp(raw)

    @property
    def band(self) -> QualityBand:
        return self.overall_score.band

    @property
    def is_fully_grounded(self) -> bool:
        return self.grounding.value >= 1.0
