"""Page relationships — how pages connect (cross-sell, upsell, related, linking).

A :class:`PageRelationship` is a typed, directed connection between two pages
(cross-sell, upsell, related, recommended, internal link, parent-child, sequence). The
:class:`RelationshipSet` groups them, and an :class:`InternalLinkingStrategy` states the
principles for internal linking (SEO + discovery). All cited.

Pure domain: standard library, the shared-kernel error base, IA ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from ia.domain.shared.ids import IAEvidenceId, PageRelationshipId
from ia.domain.shared.value_objects import PageType, RelationshipKind

__all__ = [
    "InternalLinkingStrategy",
    "InvalidRelationshipError",
    "PageRelationship",
    "RelationshipSet",
]


class InvalidRelationshipError(DesignDirectorError):
    """Raised when a page relationship is constructed with invalid data."""

    code = "invalid_page_relationship"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PageRelationship:
    """A cited, typed connection between two pages.

    Attributes:
        id: Relationship identity.
        source: The page the relationship starts at.
        target: The page the relationship points to.
        kind: The kind of relationship.
        rationale: Why the relationship exists.
        evidence_ids: The evidence supporting it.
    """

    id: PageRelationshipId
    source: PageType
    target: PageType
    kind: RelationshipKind
    rationale: str = ""
    evidence_ids: tuple[IAEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class InternalLinkingStrategy:
    """The cited internal-linking strategy (SEO + discovery).

    Attributes:
        principles: The internal-linking principles.
        hub_pages: The page types that act as linking hubs.
        evidence_ids: The evidence supporting it.
    """

    principles: tuple[str, ...] = ()
    hub_pages: tuple[PageType, ...] = ()
    evidence_ids: tuple[IAEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "hub_pages", tuple(self.hub_pages))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class RelationshipSet:
    """An immutable set of page relationships plus the internal-linking strategy."""

    relationships: tuple[PageRelationship, ...] = ()
    internal_linking: InternalLinkingStrategy = InternalLinkingStrategy()

    def __post_init__(self) -> None:
        object.__setattr__(self, "relationships", tuple(self.relationships))

    @classmethod
    def of(
        cls,
        relationships: Iterable[PageRelationship],
        internal_linking: InternalLinkingStrategy | None = None,
    ) -> RelationshipSet:
        return cls(
            relationships=tuple(relationships),
            internal_linking=internal_linking or InternalLinkingStrategy(),
        )

    def __len__(self) -> int:
        return len(self.relationships)

    def __iter__(self):
        return iter(self.relationships)

    def by_kind(self, kind: RelationshipKind) -> tuple[PageRelationship, ...]:
        return tuple(r for r in self.relationships if r.kind is kind)

    def evidence_ids(self) -> tuple[IAEvidenceId, ...]:
        return (
            *(eid for r in self.relationships for eid in r.evidence_ids),
            *self.internal_linking.evidence_ids,
        )
