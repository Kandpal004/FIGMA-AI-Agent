"""Figma-model quality metrics — how complete, grounded, and consistent the model is.

:class:`FigmaModelQualityMetrics` bundles five calibrated measures the engine computes:

* ``reference_integrity`` — the fraction of bindings/style-refs/instances that resolve against the
  declared variables/styles/component sets (``1.0`` by construction, surfaced for auditability).
* ``mode_parity`` — whether every variable values every mode of its collection (``1.0`` by
  construction — the collection invariant guarantees it).
* ``structure`` — whether every page tree is a valid acyclic rooted tree and the graphs resolve
  (``1.0`` by construction).
* ``grounding`` — the fraction of elements (nodes, component sets) whose citations resolve
  (``1.0`` by construction).
* ``confidence`` — the aggregate confidence across the evidence.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from figma_design.domain.shared.value_objects import (
    Confidence,
    Percentage,
    QualityBand,
    Score,
)

__all__ = ["FigmaModelQualityMetrics"]

_W_REFERENCE = 0.30
_W_MODE_PARITY = 0.20
_W_STRUCTURE = 0.15
_W_GROUNDING = 0.25
_W_CONFIDENCE = 0.10


@dataclass(frozen=True, slots=True)
class FigmaModelQualityMetrics:
    """The quality picture of a Figma design model.

    Attributes:
        reference_integrity: Fraction of bindings/refs/instances that resolve.
        mode_parity: Whether every variable values every mode.
        structure: Whether every page tree is valid and the graphs resolve.
        grounding: Fraction of elements with resolvable citations.
        confidence: Aggregate confidence across the evidence.
    """

    reference_integrity: Percentage
    mode_parity: Percentage
    structure: Percentage
    grounding: Percentage
    confidence: Confidence

    @property
    def overall_score(self) -> Score:
        """The weighted 0–100 overall score."""
        raw = (
            _W_REFERENCE * self.reference_integrity.value
            + _W_MODE_PARITY * self.mode_parity.value
            + _W_STRUCTURE * self.structure.value
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
    def has_reference_integrity(self) -> bool:
        return self.reference_integrity.value >= 1.0
