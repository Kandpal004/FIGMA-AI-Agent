"""Entities — the structured things the engine extracts from evidence.

An :class:`Entity` is one of the nineteen entity types (Brand, Product, CTA,
Typography, …), with its attributes, confidence, the source refs that observed it,
and the evidence ids that support it. Entities are immutable value objects; the
pipeline extracts and dedupes them from an artifact's extraction candidates.

Pure domain: standard library, the shared-kernel error base, research ids, source
ref, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from research.domain.evidence.evidence import SourceRef
from research.domain.shared.ids import EntityId, EvidenceId
from research.domain.shared.value_objects import Confidence, EntityType

__all__ = ["Entity", "InvalidEntityError"]


class InvalidEntityError(DesignDirectorError):
    """Raised when an entity is constructed with invalid data."""

    code = "invalid_entity"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Entity:
    """One extracted, typed entity.

    Attributes:
        id: Entity identity.
        type: The entity type (one of the nineteen).
        label: The entity's label.
        confidence: Confidence in the extraction.
        attributes: Structured attributes (read-only).
        source_refs: The source refs that observed it.
        evidence_ids: The evidence supporting it.
    """

    id: EntityId
    type: EntityType
    label: str
    confidence: Confidence
    attributes: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    source_refs: tuple[SourceRef, ...] = ()
    evidence_ids: tuple[EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidEntityError("Entity.label must be non-empty.")
        if not isinstance(self.attributes, MappingProxyType):
            object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))
        object.__setattr__(self, "source_refs", tuple(self.source_refs))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def dedup_key(self) -> tuple[str, str]:
        """A stable key for de-duplicating entities (type + normalized label)."""
        return (self.type.value, self.label.strip().lower())
