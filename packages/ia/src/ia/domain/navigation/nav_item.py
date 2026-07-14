"""Navigation items — the nodes of the navigation structure.

A :class:`NavItem` is one entry in a navigation surface: a label intent, an optional target
page, and optional children (for mega menus and footer groups). Cited.

Pure domain: standard library, the shared-kernel error base, IA ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from ia.domain.shared.ids import IAEvidenceId, NavItemId
from ia.domain.shared.value_objects import PageType

__all__ = ["InvalidNavItemError", "NavItem"]


class InvalidNavItemError(DesignDirectorError):
    """Raised when a navigation item is constructed with invalid data."""

    code = "invalid_nav_item"
    http_status = 422


@dataclass(frozen=True, slots=True)
class NavItem:
    """One cited navigation item.

    Attributes:
        id: Item identity.
        label_intent: The intent of the label (not the final copy).
        target: The page the item leads to, if any.
        children: Sub-items (for mega menus and footer groups).
        evidence_ids: The evidence supporting it.
    """

    id: NavItemId
    label_intent: str
    target: PageType | None = None
    children: tuple[NavItem, ...] = ()
    evidence_ids: tuple[IAEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.label_intent or not self.label_intent.strip():
            raise InvalidNavItemError("NavItem.label_intent must be non-empty.")
        object.__setattr__(self, "children", tuple(self.children))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @classmethod
    def leaf(
        cls, label_intent: str, target: PageType | None = None, evidence_ids: Iterable[IAEvidenceId] = ()
    ) -> NavItem:
        return cls(id=NavItemId.new(), label_intent=label_intent, target=target,
                   evidence_ids=tuple(evidence_ids))

    def targets(self) -> tuple[PageType, ...]:
        """All page-type targets reachable through this item and its children."""
        found: list[PageType] = []
        if self.target is not None:
            found.append(self.target)
        for child in self.children:
            found.extend(child.targets())
        return tuple(found)

    def all_evidence_ids(self) -> tuple[IAEvidenceId, ...]:
        return (*self.evidence_ids, *(eid for c in self.children for eid in c.all_evidence_ids()))
