"""Execution-plan quality metrics — how complete, grounded, and consistent the plan is.

:class:`ExecutionPlanQualityMetrics` bundles five calibrated measures the engine computes:

* ``coverage`` — the fraction of in-scope pages that received a plan.
* ``binding_integrity`` — the fraction of token/variant bindings that resolved against the live
  Design System (``1.0`` by construction, surfaced so it is auditable).
* ``sequencing`` — whether the execution graph is acyclic and totally ordered (``1.0`` by
  construction — the graph primitive and the aggregate invariant guarantee it).
* ``grounding`` — the fraction of decisions whose citations resolve (``1.0`` by construction).
* ``confidence`` — the aggregate confidence across the evidence.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from design_orchestrator.domain.shared.value_objects import (
    Confidence,
    Percentage,
    QualityBand,
    Score,
)

__all__ = ["ExecutionPlanQualityMetrics"]

_W_COVERAGE = 0.25
_W_BINDING = 0.30
_W_SEQUENCING = 0.15
_W_GROUNDING = 0.20
_W_CONFIDENCE = 0.10


@dataclass(frozen=True, slots=True)
class ExecutionPlanQualityMetrics:
    """The quality picture of a design-execution plan.

    Attributes:
        coverage: Fraction of in-scope pages planned.
        binding_integrity: Fraction of bindings resolved against the Design System.
        sequencing: Whether the execution graph is acyclic and totally ordered.
        grounding: Fraction of decisions with resolvable citations.
        confidence: Aggregate confidence across the evidence.
    """

    coverage: Percentage
    binding_integrity: Percentage
    sequencing: Percentage
    grounding: Percentage
    confidence: Confidence

    @property
    def overall_score(self) -> Score:
        """The weighted 0–100 overall score."""
        raw = (
            _W_COVERAGE * self.coverage.value
            + _W_BINDING * self.binding_integrity.value
            + _W_SEQUENCING * self.sequencing.value
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
    def has_binding_integrity(self) -> bool:
        return self.binding_integrity.value >= 1.0
