"""Sections — the structural regions of a page, and the content blocks within them.

A :class:`Section` is one region of a page (hero, buy box, reviews, …) with its purpose,
priority, placement, and the :class:`ContentBlock` s it contains. Content blocks are the
atomic leaves of the content tree. Both are cited — every structural choice traces to
evidence.

Pure domain: standard library, the shared-kernel error base, IA ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from ia.domain.shared.ids import ContentBlockId, IAEvidenceId, SectionId
from ia.domain.shared.value_objects import (
    ContentBlockKind,
    Placement,
    Priority,
    SectionType,
)

__all__ = ["ContentBlock", "InvalidSectionError", "Section"]


class InvalidSectionError(DesignDirectorError):
    """Raised when a section/content block is constructed with invalid data."""

    code = "invalid_section"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ContentBlock:
    """An atomic content unit within a section (a leaf of the content tree).

    Attributes:
        id: Content block identity.
        kind: The kind of content.
        label: What the content is (intent, not final copy).
        priority: Its priority within the section.
        evidence_ids: The evidence supporting it.
    """

    id: ContentBlockId
    kind: ContentBlockKind
    label: str
    priority: Priority = Priority(3)
    evidence_ids: tuple[IAEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidSectionError("ContentBlock.label must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class Section:
    """One cited structural region of a page.

    Attributes:
        id: Section identity.
        type: The kind of section.
        purpose: Why the section exists on the page.
        priority: Its priority relative to the page's other sections.
        placement: Where it sits in the page's vertical structure.
        is_required: Whether the section is required on the page.
        content_blocks: The content blocks it contains.
        evidence_ids: The evidence supporting it.
    """

    id: SectionId
    type: SectionType
    purpose: str
    priority: Priority = Priority(3)
    placement: Placement = Placement.MID
    is_required: bool = True
    content_blocks: tuple[ContentBlock, ...] = ()
    evidence_ids: tuple[IAEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.purpose or not self.purpose.strip():
            raise InvalidSectionError("Section.purpose must be non-empty.")
        object.__setattr__(self, "content_blocks", tuple(self.content_blocks))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def blocks_by_priority(self) -> tuple[ContentBlock, ...]:
        return tuple(sorted(self.content_blocks, key=lambda b: int(b.priority), reverse=True))

    def all_evidence_ids(self) -> tuple[IAEvidenceId, ...]:
        return (*self.evidence_ids, *(eid for b in self.content_blocks for eid in b.evidence_ids))
