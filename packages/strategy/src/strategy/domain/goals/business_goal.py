"""Business goals — what the company is trying to achieve.

A :class:`BusinessGoal` is a single, cited objective with a category, an optional
metric and target, a time horizon, and a priority. The :class:`GoalSet` is the
immutable collection produced by the goal-synthesis stage. Every goal cites the
evidence (research, competitor, knowledge, or reasoning) that motivated it.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import BusinessGoalId, StrategyEvidenceId
from strategy.domain.shared.value_objects import (
    GoalCategory,
    GoalHorizon,
    Priority,
)

__all__ = ["BusinessGoal", "GoalSet", "InvalidGoalError"]


class InvalidGoalError(DesignDirectorError):
    """Raised when a business goal is constructed with invalid data."""

    code = "invalid_business_goal"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BusinessGoal:
    """One cited business objective.

    Attributes:
        id: Goal identity.
        statement: The objective, in plain business language.
        category: The category of goal.
        horizon: Its time horizon.
        priority: Its priority.
        metric: The metric it moves (e.g. "conversion rate"), if any.
        target: The target value/description, if any.
        evidence_ids: The evidence supporting the goal.
    """

    id: BusinessGoalId
    statement: str
    category: GoalCategory
    horizon: GoalHorizon
    priority: Priority
    metric: str = ""
    target: str = ""
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidGoalError("BusinessGoal.statement must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class GoalSet:
    """An immutable set of business goals."""

    goals: tuple[BusinessGoal, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "goals", tuple(self.goals))

    @classmethod
    def of(cls, goals: Iterable[BusinessGoal]) -> GoalSet:
        return cls(goals=tuple(goals))

    def __len__(self) -> int:
        return len(self.goals)

    def __iter__(self):
        return iter(self.goals)

    def by_priority(self) -> tuple[BusinessGoal, ...]:
        return tuple(sorted(self.goals, key=lambda g: int(g.priority), reverse=True))

    def by_category(self, category: GoalCategory) -> tuple[BusinessGoal, ...]:
        return tuple(g for g in self.goals if g.category is category)

    def evidence_ids(self) -> tuple[StrategyEvidenceId, ...]:
        return tuple(eid for g in self.goals for eid in g.evidence_ids)
