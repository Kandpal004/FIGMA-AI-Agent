"""The ReviewProfile — how a category is weighted and gated for a kind of business.

A :class:`ReviewProfile` calibrates the Creative Director to a business model: it assigns each
scoring category a :class:`Weight` (its share of the overall score), a set of **hard gates**
(non-negotiable per-category minimum scores), and a default approval threshold. The *same*
critic outputs produce different overalls and pass/fail gates under different profiles — a
Luxury store and a Marketplace are held to the same evidence but different bars.

The concrete profile catalogue lives in the infrastructure layer; this is the immutable data
the domain reasons over.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from creative_director.domain.shared.value_objects import (
    ReviewProfileKind,
    Score,
    ScoreCategory,
    Weight,
)

__all__ = ["InvalidProfileError", "ReviewProfile"]


class InvalidProfileError(DesignDirectorError):
    """Raised when a review profile is constructed with invalid data."""

    code = "invalid_creative_director_profile"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ReviewProfile:
    """A calibrated set of category weights, hard gates, and a default threshold.

    Attributes:
        kind: Which business-model profile this is.
        weights: Each substantive category's share of the overall score.
        hard_gates: Per-category minimum scores that must hold to approve.
        default_threshold: The default overall approval threshold.
    """

    kind: ReviewProfileKind
    weights: Mapping[ScoreCategory, Weight]
    hard_gates: Mapping[ScoreCategory, Score] = field(
        default_factory=lambda: MappingProxyType({})
    )
    default_threshold: Score = Score(70.0)

    def __post_init__(self) -> None:
        if not self.weights:
            raise InvalidProfileError("ReviewProfile.weights must be non-empty.")
        if ScoreCategory.OVERALL in self.weights:
            raise InvalidProfileError("OVERALL is derived; it must not carry a weight.")
        total = sum(w.value for w in self.weights.values())
        if not 0.99 <= total <= 1.01:
            raise InvalidProfileError(
                "ReviewProfile.weights must sum to 1.0.", details={"total": total}
            )
        object.__setattr__(self, "weights", MappingProxyType(dict(self.weights)))
        object.__setattr__(self, "hard_gates", MappingProxyType(dict(self.hard_gates)))

    def weight_of(self, category: ScoreCategory) -> Weight:
        return self.weights.get(category, Weight(0.0))

    def gate_of(self, category: ScoreCategory) -> Score | None:
        return self.hard_gates.get(category)
