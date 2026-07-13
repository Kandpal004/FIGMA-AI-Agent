"""The Confidence model — a deterministic measure of how sound a strategy is.

Confidence is never a hunch. A :class:`ConfidenceScore` is a value in ``[0, 1]``
with a calibrated band; a :class:`StrategyConfidence` carries the overall score
plus a per-dimension breakdown, so a caller can see exactly where the strategy is
strong and where it rests on thin or absent evidence. The *computation* lives in
the application's confidence calculator; this module is the value model it fills.

Pure domain: standard library, the shared-kernel error base, and shared enums.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Self

from core.errors import DesignDirectorError

from reasoning.domain.shared.value_objects import ReasoningDimension

__all__ = [
    "ConfidenceBand",
    "ConfidenceScore",
    "InvalidConfidenceError",
    "StrategyConfidence",
]


class InvalidConfidenceError(DesignDirectorError):
    """Raised when a confidence value is out of range."""

    code = "invalid_confidence"
    http_status = 422


class ConfidenceBand(str, Enum):
    """The calibrated band a confidence score falls into."""

    VERY_HIGH = "very_high"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    VERY_LOW = "very_low"


@dataclass(frozen=True, slots=True, order=True)
class ConfidenceScore:
    """A confidence value in ``[0, 1]`` with a calibrated band.

    Orders by value, so scores are directly comparable.

    Attributes:
        value: A value in ``[0, 1]``.
    """

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidConfidenceError(
                "ConfidenceScore.value must be within [0, 1].",
                details={"value": self.value},
            )

    @property
    def band(self) -> ConfidenceBand:
        """The band this score falls into."""
        if self.value >= 0.85:
            return ConfidenceBand.VERY_HIGH
        if self.value >= 0.7:
            return ConfidenceBand.HIGH
        if self.value >= 0.5:
            return ConfidenceBand.MODERATE
        if self.value >= 0.3:
            return ConfidenceBand.LOW
        return ConfidenceBand.VERY_LOW

    @classmethod
    def of(cls, value: float) -> Self:
        """Construct from a numeric value."""
        return cls(value=value)

    @classmethod
    def clamp(cls, value: float) -> Self:
        """Construct from a value clamped into ``[0, 1]`` (never raises)."""
        return cls(value=min(1.0, max(0.0, value)))


@dataclass(frozen=True, slots=True)
class StrategyConfidence:
    """The confidence picture for a whole strategy.

    Attributes:
        overall: The overall confidence score.
        by_dimension: Per-dimension confidence (read-only).
    """

    overall: ConfidenceScore
    by_dimension: Mapping[ReasoningDimension, ConfidenceScore] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.by_dimension, MappingProxyType):
            object.__setattr__(
                self, "by_dimension", MappingProxyType(dict(self.by_dimension))
            )

    def for_dimension(self, dimension: ReasoningDimension) -> ConfidenceScore | None:
        """The confidence for a dimension, or ``None`` if not scored."""
        return self.by_dimension.get(dimension)

    def weakest(self) -> tuple[ReasoningDimension, ConfidenceScore] | None:
        """The lowest-confidence dimension, or ``None`` if none scored."""
        if not self.by_dimension:
            return None
        dimension = min(self.by_dimension, key=lambda d: self.by_dimension[d].value)
        return dimension, self.by_dimension[dimension]
