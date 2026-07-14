"""Calls to action — the strategic actions a page drives (never rendered buttons).

A :class:`CallToAction` states the *intent* of an action a page must drive: its
prominence tier, the action it represents, its target, and its priority. It names no
final copy, colour, or button — that is a later phase. Cited.

Pure domain: standard library, the shared-kernel error base, UX ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from ux.domain.shared.ids import CallToActionId, UXEvidenceId
from ux.domain.shared.value_objects import CTAType, PageKind, Priority

__all__ = ["CallToAction", "InvalidCTAError"]


class InvalidCTAError(DesignDirectorError):
    """Raised when a call to action is constructed with invalid data."""

    code = "invalid_call_to_action"
    http_status = 422


@dataclass(frozen=True, slots=True)
class CallToAction:
    """The cited strategic intent of a call to action.

    Attributes:
        id: CTA identity.
        type: The prominence tier (primary/secondary/tertiary).
        action: The action it drives (e.g. "add to cart", "start checkout").
        label_intent: The intent of the label (not the final copy).
        target: The page/state it leads to, if any.
        priority: Its priority on the page.
        evidence_ids: The evidence supporting it.
    """

    id: CallToActionId
    type: CTAType
    action: str
    label_intent: str = ""
    target: PageKind | None = None
    priority: Priority = Priority(3)
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.action or not self.action.strip():
            raise InvalidCTAError("CallToAction.action must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
