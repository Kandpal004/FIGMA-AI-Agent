"""UX goals — what the user and the business are trying to achieve.

A :class:`UserGoal` is a cited goal the user brings (primary or secondary); a
:class:`BusinessGoal` is a cited commercial objective the experience must serve. The
:class:`GoalSet` groups them and identifies the single primary user goal every page must
ultimately serve.

Pure domain: standard library, the shared-kernel error base, UX ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from ux.domain.shared.ids import BusinessGoalId, UserGoalId, UXEvidenceId
from ux.domain.shared.value_objects import Priority

__all__ = ["BusinessGoal", "GoalSet", "InvalidGoalError", "UserGoal"]


class InvalidGoalError(DesignDirectorError):
    """Raised when a goal is constructed with invalid data."""

    code = "invalid_ux_goal"
    http_status = 422


@dataclass(frozen=True, slots=True)
class UserGoal:
    """A cited user goal.

    Attributes:
        id: Goal identity.
        statement: The goal, in the user's terms.
        is_primary: Whether this is the single primary user goal.
        priority: Its priority relative to other user goals.
        evidence_ids: The evidence supporting it.
    """

    id: UserGoalId
    statement: str
    is_primary: bool = False
    priority: Priority = Priority(3)
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidGoalError("UserGoal.statement must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class BusinessGoal:
    """A cited business goal the experience must serve.

    Attributes:
        id: Goal identity.
        statement: The commercial objective.
        priority: Its priority.
        evidence_ids: The evidence supporting it.
    """

    id: BusinessGoalId
    statement: str
    priority: Priority = Priority(3)
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidGoalError("BusinessGoal.statement must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class GoalSet:
    """The cited set of user and business goals."""

    user_goals: tuple[UserGoal, ...] = ()
    business_goals: tuple[BusinessGoal, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "user_goals", tuple(self.user_goals))
        object.__setattr__(self, "business_goals", tuple(self.business_goals))

    @classmethod
    def of(
        cls,
        *,
        user_goals: Iterable[UserGoal] = (),
        business_goals: Iterable[BusinessGoal] = (),
    ) -> GoalSet:
        return cls(user_goals=tuple(user_goals), business_goals=tuple(business_goals))

    @property
    def primary_user_goal(self) -> UserGoal | None:
        return next((g for g in self.user_goals if g.is_primary), None)

    def secondary_user_goals(self) -> tuple[UserGoal, ...]:
        return tuple(g for g in self.user_goals if not g.is_primary)

    def evidence_ids(self) -> tuple[UXEvidenceId, ...]:
        return (
            *(eid for g in self.user_goals for eid in g.evidence_ids),
            *(eid for g in self.business_goals for eid in g.evidence_ids),
        )
