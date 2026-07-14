"""Information and content priority — what matters most on a page.

An :class:`InformationPriority` orders the information a page must convey by disclosure
level (primary → hidden), driving progressive disclosure and Miller's-Law chunking. A
:class:`ContentPriority` orders the content types the page leads with. Both cited.

Pure domain: standard library, the shared-kernel error base, UX ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from ux.domain.shared.ids import UXEvidenceId
from ux.domain.shared.value_objects import ContentType, InformationLevel

__all__ = [
    "ContentItem",
    "ContentPriority",
    "InformationItem",
    "InformationPriority",
    "InvalidPriorityError",
]


class InvalidPriorityError(DesignDirectorError):
    """Raised when a priority is constructed with invalid data."""

    code = "invalid_page_priority"
    http_status = 422


@dataclass(frozen=True, slots=True)
class InformationItem:
    """One piece of information at a disclosure level.

    Attributes:
        label: What the information is.
        level: Its disclosure level.
    """

    label: str
    level: InformationLevel

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidPriorityError("InformationItem.label must be non-empty.")


@dataclass(frozen=True, slots=True)
class ContentItem:
    """One content type at a rank.

    Attributes:
        content_type: The kind of content.
        rank: Its 1-based rank (1 = leads the page).
    """

    content_type: ContentType
    rank: int

    def __post_init__(self) -> None:
        if self.rank < 1:
            raise InvalidPriorityError("ContentItem.rank must be >= 1.")


@dataclass(frozen=True, slots=True)
class InformationPriority:
    """The cited, ordered information priority for a page."""

    items: tuple[InformationItem, ...] = ()
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def at_level(self, level: InformationLevel) -> tuple[InformationItem, ...]:
        return tuple(i for i in self.items if i.level is level)


@dataclass(frozen=True, slots=True)
class ContentPriority:
    """The cited, ranked content priority for a page."""

    items: tuple[ContentItem, ...] = ()
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(sorted(self.items, key=lambda i: i.rank)))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
