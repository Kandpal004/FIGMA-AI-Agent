"""Page actions — the primary and secondary actions a page drives (never buttons).

A :class:`PageAction` states an action a page must drive: its prominence tier, the action
and its target, and its placement. It names no copy, colour, or button — that is a later
phase. Cited from the UX Strategy's CTAs.

Pure domain: standard library, the shared-kernel error base, IA ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from ia.domain.shared.ids import IAEvidenceId, PageActionId
from ia.domain.shared.value_objects import ActionType, PageType, Placement

__all__ = ["InvalidActionError", "PageAction"]


class InvalidActionError(DesignDirectorError):
    """Raised when a page action is constructed with invalid data."""

    code = "invalid_page_action"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PageAction:
    """A cited action a page drives.

    Attributes:
        id: Action identity.
        type: The prominence tier (primary/secondary/tertiary).
        action: The action it drives (e.g. "add to cart").
        target: The page it leads to, if any.
        placement: Where the action sits on the page.
        evidence_ids: The evidence supporting it.
    """

    id: PageActionId
    type: ActionType
    action: str
    target: PageType | None = None
    placement: Placement = Placement.ABOVE_FOLD
    evidence_ids: tuple[IAEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.action or not self.action.strip():
            raise InvalidActionError("PageAction.action must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
