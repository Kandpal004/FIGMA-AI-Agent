"""SectionGoals — the four goals every section must serve.

A principal product designer never lays out a section without knowing why it exists on four
axes at once: the business goal it advances, the user goal it serves, the conversion goal it
drives, and the trust goal it reinforces. :class:`SectionGoals` bundles them so a section
cannot be planned goal-blind.

Pure domain: standard library, the shared-kernel error base, wireframe ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from wireframe.domain.shared.ids import WFEvidenceId

__all__ = ["InvalidGoalsError", "SectionGoals"]


class InvalidGoalsError(DesignDirectorError):
    """Raised when section goals are constructed with invalid data."""

    code = "invalid_wireframe_goals"
    http_status = 422


@dataclass(frozen=True, slots=True)
class SectionGoals:
    """The business, user, conversion, and trust goals a section serves.

    Attributes:
        purpose: Why the section exists on the page.
        business_goal: The commercial objective it advances.
        user_goal: The goal the user brings to it.
        conversion_goal: The conversion outcome it drives.
        trust_goal: The trust it reinforces.
        evidence_ids: The evidence grounding the goals.
    """

    purpose: str
    business_goal: str
    user_goal: str
    conversion_goal: str = ""
    trust_goal: str = ""
    evidence_ids: tuple[WFEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.purpose or not self.purpose.strip():
            raise InvalidGoalsError("SectionGoals.purpose must be non-empty.")
        if not self.business_goal or not self.business_goal.strip():
            raise InvalidGoalsError("SectionGoals.business_goal must be non-empty.")
        if not self.user_goal or not self.user_goal.strip():
            raise InvalidGoalsError("SectionGoals.user_goal must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
