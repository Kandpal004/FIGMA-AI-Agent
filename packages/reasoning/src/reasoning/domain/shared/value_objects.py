"""Shared value objects for the Reasoning Engine.

These immutable, self-validating value objects define the *vocabulary* the engine
reasons in: the strategic lens a run adopts, the dimensions it reasons across, and
the calibrated scales it uses to weigh risk and importance. They carry no identity
and are interchangeable when their attributes match.

Everything here is pure domain: only the standard library and the shared-kernel
error base (:mod:`core.errors`). Crucially, this module does **not** import the
Knowledge Engine (Phase 3): the mapping from a :class:`ReasoningDimension` to a
knowledge category is an adapter concern, so the reasoning domain stays decoupled
and testable, per the ports-and-adapters decision.

Contents
--------
* :class:`StrategyStance`     — the strategic lens (also drives alternatives).
* :class:`ReasoningDimension` — the eighteen dimensions mapped to the questions.
* :class:`Severity` / :class:`Likelihood` — ordered risk scales.
* :class:`Weight`             — a normalized ``[0,1]`` importance weight.

Testing considerations
----------------------
* :class:`Severity` and :class:`Likelihood` compare by rank.
* :class:`Weight` validates ``[0,1]``, orders by value, and scales/combines
  without leaving the range.
* :class:`ReasoningDimension` has one member per strategic question the engine
  answers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Self

from core.errors import DesignDirectorError

__all__ = [
    "InvalidReasoningValueError",
    "Likelihood",
    "ReasoningDimension",
    "Severity",
    "StrategyStance",
    "Weight",
]


class InvalidReasoningValueError(DesignDirectorError):
    """Raised when a reasoning value object is constructed with invalid data."""

    code = "invalid_reasoning_value"
    http_status = 422


class StrategyStance(str, Enum):
    """The strategic lens a reasoning run adopts.

    The stance biases how competing dimensions are weighed when scoring decisions
    and resolving trade-offs, and it is the axis along which *alternative*
    strategies are generated — the same inputs reasoned under a different stance
    yield a different, still-cited strategy.
    """

    BALANCED = "balanced"
    CONVERSION_FIRST = "conversion_first"
    BRAND_FIRST = "brand_first"
    ACCESSIBILITY_FIRST = "accessibility_first"
    TRUST_FIRST = "trust_first"
    PERFORMANCE_FIRST = "performance_first"

    @classmethod
    def default(cls) -> StrategyStance:
        """The default stance when none is specified."""
        return cls.BALANCED


class ReasoningDimension(str, Enum):
    """A dimension of strategy the engine reasons about.

    There is one member per strategic question the engine must answer, so a
    :class:`ReasonNode`, :class:`DecisionNode`, or evidenced statement can be
    tagged precisely (which lets callers ask "show me the CRO reasoning" or "which
    accessibility rules applied"). The string value is the stable identifier used
    in persistence and views.
    """

    BUSINESS = "business"
    CUSTOMER = "customer"
    TARGET_MARKET = "target_market"
    CUSTOMER_PROBLEMS = "customer_problems"
    OBJECTIONS = "objections"
    EMOTIONAL_TRIGGERS = "emotional_triggers"
    TRUST_MECHANISMS = "trust_mechanisms"
    CONVERSION = "conversion"
    USER_EXPERIENCE = "user_experience"
    ACCESSIBILITY = "accessibility"
    PLATFORM_CONSTRAINTS = "platform_constraints"
    COMPETITIVE = "competitive"
    DESIGN_SYSTEM = "design_system"
    TYPOGRAPHY = "typography"
    SPACING = "spacing"
    VISUAL_HIERARCHY = "visual_hierarchy"
    STRUCTURE = "structure"
    CREATIVE_REVIEW = "creative_review"


class Severity(IntEnum):
    """How damaging a risk would be if it materialized (ordered)."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Likelihood(IntEnum):
    """How probable a risk is to materialize (ordered)."""

    RARE = 1
    POSSIBLE = 2
    LIKELY = 3
    ALMOST_CERTAIN = 4


@dataclass(frozen=True, slots=True, order=True)
class Weight:
    """A normalized importance weight in ``[0, 1]``.

    Used to weigh dimensions under a stance and to combine partial scores.
    Ordering is by value, so weights are directly comparable.

    Attributes:
        value: A value in ``[0, 1]``.
    """

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise InvalidReasoningValueError(
                "Weight.value must be within [0, 1].", details={"value": self.value}
            )

    @classmethod
    def of(cls, value: float) -> Self:
        """Construct from a numeric value."""
        return cls(value=value)

    @classmethod
    def full(cls) -> Self:
        """The maximum weight (``1.0``)."""
        return cls(value=1.0)

    @classmethod
    def zero(cls) -> Self:
        """The minimum weight (``0.0``)."""
        return cls(value=0.0)

    def scale(self, factor: float) -> Weight:
        """Return this weight scaled by ``factor``, clamped to ``[0, 1]``."""
        return Weight(value=min(1.0, max(0.0, self.value * factor)))

    def combine(self, other: Weight) -> Weight:
        """Return the average of two weights (stays within ``[0, 1]``)."""
        return Weight(value=(self.value + other.value) / 2.0)
