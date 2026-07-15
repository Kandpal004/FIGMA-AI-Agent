"""Design-system quality metrics — how complete, grounded, and coherent the spec is.

:class:`DesignSystemQualityMetrics` bundles five calibrated measures the engine computes:

* ``token_integrity`` — the fraction of token references that resolve to a real token with no
  dangling alias and no cycle (``1.0`` by construction, surfaced so it is auditable).
* ``component_coverage`` — the fraction of in-scope components that are fully specified (states,
  responsive, accessibility, and all three platform mappings present).
* ``theme_parity`` — whether light/dark theme the same semantic keys (``1.0`` when parity holds
  or dark mode is not required).
* ``grounding`` — the fraction of elements whose citations resolve (``1.0`` by construction,
  surfaced for auditability).
* ``confidence`` — the aggregate confidence across the evidence.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from design_system.domain.shared.value_objects import (
    Confidence,
    Percentage,
    QualityBand,
    Score,
)

__all__ = ["DesignSystemQualityMetrics"]

_W_TOKEN_INTEGRITY = 0.30
_W_COMPONENT_COVERAGE = 0.25
_W_THEME_PARITY = 0.15
_W_GROUNDING = 0.20
_W_CONFIDENCE = 0.10


@dataclass(frozen=True, slots=True)
class DesignSystemQualityMetrics:
    """The quality picture of a design-system specification.

    Attributes:
        token_integrity: Fraction of token references that resolve with no dangling alias/cycle.
        component_coverage: Fraction of in-scope components fully specified.
        theme_parity: Whether light/dark theme the same semantic keys.
        grounding: Fraction of elements with resolvable citations.
        confidence: Aggregate confidence across the evidence.
    """

    token_integrity: Percentage
    component_coverage: Percentage
    theme_parity: Percentage
    grounding: Percentage
    confidence: Confidence

    @property
    def overall_score(self) -> Score:
        """The weighted 0–100 overall score."""
        raw = (
            _W_TOKEN_INTEGRITY * self.token_integrity.value
            + _W_COMPONENT_COVERAGE * self.component_coverage.value
            + _W_THEME_PARITY * self.theme_parity.value
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

    @property
    def has_token_integrity(self) -> bool:
        return self.token_integrity.value >= 1.0
