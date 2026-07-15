"""The Compatibility model — the typed relationships between components.

A :class:`CompatibilityLink` records that one component ``REQUIRES``, ``CONFLICTS_WITH``,
``ENHANCES``, or ``REPLACES`` another. The :class:`CompatibilitySet` is the immutable web of
those links — the engine's knowledge of which components need each other and which cannot
coexist. It is what the specification's coherence invariant enforces: two conflicting
components may not both be included and co-placed.

Pure domain: standard library, the shared-kernel error base, CI ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from component_intelligence.domain.shared.ids import CIEvidenceId, CompatibilityId
from component_intelligence.domain.shared.value_objects import CompatibilityKind, ComponentType

__all__ = ["CompatibilityLink", "CompatibilitySet", "InvalidCompatibilityError"]


class InvalidCompatibilityError(DesignDirectorError):
    """Raised when a compatibility link or set is constructed with invalid data."""

    code = "invalid_component_intelligence_compatibility"
    http_status = 422


@dataclass(frozen=True, slots=True)
class CompatibilityLink:
    """A typed relationship between two components.

    Attributes:
        id: Link identity.
        source: The component the relationship is from.
        target: The component the relationship is to.
        kind: The relationship kind.
        rationale: Why the relationship holds.
        evidence_ids: The evidence grounding it.
    """

    id: CompatibilityId
    source: ComponentType
    target: ComponentType
    kind: CompatibilityKind
    rationale: str = ""
    evidence_ids: tuple[CIEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if self.source is self.target:
            raise InvalidCompatibilityError(
                "A compatibility link cannot relate a component to itself.",
                details={"component": self.source.value},
            )
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        return self.evidence_ids


@dataclass(frozen=True, slots=True)
class CompatibilitySet:
    """The immutable web of compatibility links."""

    links: tuple[CompatibilityLink, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "links", tuple(self.links))

    @classmethod
    def of(cls, links: Iterable[CompatibilityLink]) -> CompatibilitySet:
        return cls(links=tuple(links))

    def __len__(self) -> int:
        return len(self.links)

    def __iter__(self):
        return iter(self.links)

    def by_kind(self, kind: CompatibilityKind) -> tuple[CompatibilityLink, ...]:
        return tuple(link for link in self.links if link.kind is kind)

    def conflicts(self) -> tuple[CompatibilityLink, ...]:
        return self.by_kind(CompatibilityKind.CONFLICTS_WITH)

    def requires_of(self, component: ComponentType) -> tuple[ComponentType, ...]:
        return tuple(
            link.target for link in self.links
            if link.source is component and link.kind is CompatibilityKind.REQUIRES
        )

    def conflicting_pairs(self) -> tuple[tuple[ComponentType, ComponentType], ...]:
        return tuple((link.source, link.target) for link in self.conflicts())

    def evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        return tuple(eid for link in self.links for eid in link.all_evidence_ids())
