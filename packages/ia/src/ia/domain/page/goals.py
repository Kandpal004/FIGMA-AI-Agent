"""Page goals — the business and user goals a page serves.

A :class:`PageGoals` names the business goal, the primary user goal, and the secondary user
goal a page exists to serve — carried and cited from the Business Strategy and UX Strategy
upstream. Every page's structure must trace to these.

Pure domain: standard library, the shared-kernel error base, IA ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from ia.domain.shared.ids import IAEvidenceId

__all__ = ["InvalidGoalsError", "PageGoals"]


class InvalidGoalsError(DesignDirectorError):
    """Raised when page goals are constructed with invalid data."""

    code = "invalid_page_goals"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PageGoals:
    """The cited goals a page serves.

    Attributes:
        business_goal: The commercial objective the page serves.
        primary_user_goal: The single primary goal the user brings to the page.
        secondary_user_goal: A secondary goal the page also serves.
        evidence_ids: The evidence supporting them.
    """

    business_goal: str
    primary_user_goal: str
    secondary_user_goal: str = ""
    evidence_ids: tuple[IAEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.business_goal or not self.business_goal.strip():
            raise InvalidGoalsError("PageGoals.business_goal must be non-empty.")
        if not self.primary_user_goal or not self.primary_user_goal.strip():
            raise InvalidGoalsError("PageGoals.primary_user_goal must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
