"""The Evidence model — the provenance backbone of the Research Engine.

Every finding the engine produces is an :class:`Evidence`: a claim with a
:class:`SourceRef` (the source and the exact locator it came from), a supporting
snippet, a confidence, and an optional link to a Knowledge-Engine entry attached by
the knowledge mapper. Nothing is unattributed — every piece of evidence traces to a
source and a place within it, so downstream reasoning is fully auditable.

The :class:`EvidenceGraph` is the immutable registry of all evidence in a report;
entities and relationships reference evidence by id.

Pure domain: standard library, the shared-kernel error base, research ids, source
locator, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from research.domain.shared.ids import EvidenceId, ResearchSourceId
from research.domain.shared.value_objects import (
    Confidence,
    ProviderKind,
    ResearchCategory,
    Tag,
)
from research.domain.source.source import SourceLocator

__all__ = [
    "Evidence",
    "EvidenceGraph",
    "EvidenceNotFoundError",
    "InvalidEvidenceError",
    "SourceRef",
]


class InvalidEvidenceError(DesignDirectorError):
    """Raised when evidence is constructed with invalid data."""

    code = "invalid_evidence"
    http_status = 422


class EvidenceNotFoundError(DesignDirectorError):
    """Raised when evidence is requested by an id absent from the graph."""

    code = "evidence_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class SourceRef:
    """A pointer to where evidence came from.

    Attributes:
        source_id: The source it came from.
        locator: The exact place within the source.
        provider: The provider that supplied it.
    """

    source_id: ResearchSourceId
    locator: SourceLocator
    provider: ProviderKind


@dataclass(frozen=True, slots=True)
class Evidence:
    """One provenance-tracked finding.

    Attributes:
        id: Evidence identity.
        claim: The finding.
        source_ref: Where it came from.
        confidence: Confidence in the finding.
        category: The research category.
        snippet: The raw excerpt supporting it.
        tags: Free-form tags.
        knowledge_id: An optional linked Knowledge-Engine lineage id (UUID string),
            attached by the knowledge mapper.
    """

    id: EvidenceId
    claim: str
    source_ref: SourceRef
    confidence: Confidence
    category: ResearchCategory
    snippet: str = ""
    tags: frozenset[Tag] = field(default_factory=frozenset)
    knowledge_id: str | None = None

    def __post_init__(self) -> None:
        if not self.claim or not self.claim.strip():
            raise InvalidEvidenceError("Evidence.claim must be non-empty.")
        object.__setattr__(self, "tags", frozenset(self.tags))

    @property
    def is_grounded(self) -> bool:
        """Whether this evidence is linked to a Knowledge-Engine entry."""
        return self.knowledge_id is not None

    def with_knowledge(self, knowledge_id: str) -> Evidence:
        """Return a copy linked to a Knowledge-Engine entry."""
        from dataclasses import replace

        return replace(self, knowledge_id=knowledge_id)


@dataclass(frozen=True, slots=True)
class EvidenceGraph:
    """An immutable registry of the evidence in a report."""

    items: Mapping[EvidenceId, Evidence] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.items, MappingProxyType):
            object.__setattr__(self, "items", MappingProxyType(dict(self.items)))

    @classmethod
    def empty(cls) -> EvidenceGraph:
        return cls()

    @classmethod
    def of(cls, evidence: Iterable[Evidence]) -> EvidenceGraph:
        """Build a graph from evidence.

        Raises:
            InvalidEvidenceError: If two items share an id.
        """
        mapping: dict[EvidenceId, Evidence] = {}
        for item in evidence:
            if item.id in mapping:
                raise InvalidEvidenceError(
                    "Duplicate evidence id in graph.", details={"id": str(item.id)}
                )
            mapping[item.id] = item
        return cls(items=MappingProxyType(mapping))

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items.values())

    def has(self, evidence_id: EvidenceId) -> bool:
        return evidence_id in self.items

    def get(self, evidence_id: EvidenceId) -> Evidence:
        """Return the evidence for ``evidence_id``.

        Raises:
            EvidenceNotFoundError: If no such evidence exists.
        """
        item = self.items.get(evidence_id)
        if item is None:
            raise EvidenceNotFoundError(
                f"Evidence {evidence_id} not found.",
                details={"evidence_id": str(evidence_id)},
            )
        return item

    def by_category(self, category: ResearchCategory) -> tuple[Evidence, ...]:
        return tuple(e for e in self.items.values() if e.category is category)

    def grounded(self) -> tuple[Evidence, ...]:
        """Evidence linked to a Knowledge-Engine entry."""
        return tuple(e for e in self.items.values() if e.is_grounded)
