"""The Priority Matrix — what to do first, and why.

Each :class:`PrioritizedItem` scores a strategic decision on reach, impact,
confidence, and effort, yielding a deterministic RICE-style score and an impact/effort
quadrant (quick win / major project / fill-in / thankless). The :class:`PriorityMatrix`
orders them so downstream execution has an evidence-backed sequence, not a guess.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import (
    PrioritizedItemId,
    StrategicDecisionId,
    StrategyEvidenceId,
)
from strategy.domain.shared.value_objects import (
    Confidence,
    EffortScore,
    ImpactScore,
    PriorityQuadrant,
    ReachScore,
)

__all__ = ["InvalidPriorityError", "PrioritizedItem", "PriorityMatrix"]


class InvalidPriorityError(DesignDirectorError):
    """Raised when a priority item is constructed with invalid data."""

    code = "invalid_priority_item"
    http_status = 422

# The midpoint of the 1–5 impact/effort scales, used to split the quadrants.
_MIDPOINT = 3


@dataclass(frozen=True, slots=True)
class PrioritizedItem:
    """One scored, quadranted initiative tied to a strategic decision.

    Attributes:
        id: Item identity.
        decision_id: The decision this initiative executes.
        title: A short label.
        reach: How many customers it touches (1–5).
        impact: How much it moves the needle (1–5).
        confidence: Confidence in the estimate.
        effort: How costly it is (1–5).
        evidence_ids: The evidence supporting the scoring.
    """

    id: PrioritizedItemId
    decision_id: StrategicDecisionId
    title: str
    reach: ReachScore
    impact: ImpactScore
    confidence: Confidence
    effort: EffortScore
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.title or not self.title.strip():
            raise InvalidPriorityError("PrioritizedItem.title must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def score(self) -> float:
        """The RICE-style score: reach × impact × confidence ÷ effort (rounded)."""
        raw = (
            int(self.reach) * int(self.impact) * self.confidence.value
        ) / int(self.effort)
        return round(raw, 3)

    @property
    def quadrant(self) -> PriorityQuadrant:
        """The impact/effort quadrant."""
        high_impact = int(self.impact) >= _MIDPOINT
        high_effort = int(self.effort) >= _MIDPOINT
        if high_impact and not high_effort:
            return PriorityQuadrant.QUICK_WIN
        if high_impact and high_effort:
            return PriorityQuadrant.MAJOR_PROJECT
        if not high_impact and not high_effort:
            return PriorityQuadrant.FILL_IN
        return PriorityQuadrant.THANKLESS


@dataclass(frozen=True, slots=True)
class PriorityMatrix:
    """An immutable, scored priority matrix."""

    items: tuple[PrioritizedItem, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))

    @classmethod
    def of(cls, items: Iterable[PrioritizedItem]) -> PriorityMatrix:
        return cls(items=tuple(items))

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    def ranked(self) -> tuple[PrioritizedItem, ...]:
        """Items in descending score order (highest priority first)."""
        return tuple(sorted(self.items, key=lambda i: i.score, reverse=True))

    def in_quadrant(self, quadrant: PriorityQuadrant) -> tuple[PrioritizedItem, ...]:
        return tuple(i for i in self.items if i.quadrant is quadrant)

    def quick_wins(self) -> tuple[PrioritizedItem, ...]:
        return self.in_quadrant(PriorityQuadrant.QUICK_WIN)

    def evidence_ids(self) -> tuple[StrategyEvidenceId, ...]:
        return tuple(eid for i in self.items for eid in i.evidence_ids)

    def decision_ids(self) -> tuple[StrategicDecisionId, ...]:
        return tuple(i.decision_id for i in self.items)
