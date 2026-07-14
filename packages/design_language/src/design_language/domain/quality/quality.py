"""Design-language quality metrics — how complete, grounded, and consistent the language is.

:class:`DesignLanguageQualityMetrics` bundles four calibrated measures the engine computes:

* ``coverage`` — the fraction of the nineteen visual attributes actually determined.
* ``grounding`` — the fraction of decisions whose citations resolve (``1.0`` by construction,
  surfaced so it is auditable).
* ``consistency`` — how well the consistency rules and constraints cover the language's core
  dimensions (a language with no rules is inconsistent by omission).
* ``confidence`` — the aggregate confidence across the language.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from design_language.domain.shared.value_objects import (
    Confidence,
    Percentage,
    QualityBand,
    Score,
)

__all__ = ["DesignLanguageQualityMetrics"]

_W_COVERAGE = 0.3
_W_GROUNDING = 0.3
_W_CONSISTENCY = 0.25
_W_CONFIDENCE = 0.15


@dataclass(frozen=True, slots=True)
class DesignLanguageQualityMetrics:
    """The quality picture of a design-language specification.

    Attributes:
        coverage: Fraction of the nineteen visual attributes determined.
        grounding: Fraction of decisions with resolvable citations.
        consistency: How well rules and constraints cover the core dimensions.
        confidence: Aggregate confidence across the language.
    """

    coverage: Percentage
    grounding: Percentage
    consistency: Percentage
    confidence: Confidence

    @property
    def overall_score(self) -> Score:
        """The weighted 0–100 overall score."""
        raw = (
            _W_COVERAGE * self.coverage.value
            + _W_GROUNDING * self.grounding.value
            + _W_CONSISTENCY * self.consistency.value
            + _W_CONFIDENCE * self.confidence.value
        ) * 100.0
        return Score.clamp(raw)

    @property
    def band(self) -> QualityBand:
        return self.overall_score.band

    @property
    def is_fully_grounded(self) -> bool:
        return self.grounding.value >= 1.0
