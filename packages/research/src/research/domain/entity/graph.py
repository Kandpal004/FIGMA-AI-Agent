"""The Entity Graph — the queryable structure of extracted entities and edges.

An :class:`EntityGraph` holds the entities (keyed by id) and the relationships
between them, validating that every relationship's endpoints exist. It is the clean,
traversable structure downstream reasoning walks. Immutable; functional updates
return a new graph.

Pure domain: standard library, the shared-kernel error base, research ids, and the
entity/relationship value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from research.domain.entity.entity import Entity
from research.domain.entity.relationship import Relationship
from research.domain.shared.ids import EntityId
from research.domain.shared.value_objects import EntityType, RelationshipType

__all__ = ["EntityGraph", "EntityNotFoundError", "InvalidEntityGraphError"]


class InvalidEntityGraphError(DesignDirectorError):
    """Raised when the entity graph is structurally invalid (a dangling edge)."""

    code = "invalid_entity_graph"
    http_status = 422


class EntityNotFoundError(DesignDirectorError):
    """Raised when an entity is requested by an id absent from the graph."""

    code = "entity_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class EntityGraph:
    """An immutable graph of entities and their relationships."""

    entities: Mapping[EntityId, Entity] = field(
        default_factory=lambda: MappingProxyType({})
    )
    relationships: tuple[Relationship, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.entities, MappingProxyType):
            object.__setattr__(self, "entities", MappingProxyType(dict(self.entities)))
        object.__setattr__(self, "relationships", tuple(self.relationships))
        for relationship in self.relationships:
            if relationship.source not in self.entities:
                raise InvalidEntityGraphError(
                    "Relationship references a source entity not in the graph.",
                    details={"relationship": str(relationship.id)},
                )
            if relationship.target not in self.entities:
                raise InvalidEntityGraphError(
                    "Relationship references a target entity not in the graph.",
                    details={"relationship": str(relationship.id)},
                )

    @classmethod
    def empty(cls) -> EntityGraph:
        return cls()

    @classmethod
    def of(
        cls, entities: Iterable[Entity], relationships: Iterable[Relationship] = ()
    ) -> EntityGraph:
        """Build a graph from entities and relationships.

        Raises:
            InvalidEntityGraphError: On a duplicate entity id or a dangling edge.
        """
        mapping: dict[EntityId, Entity] = {}
        for entity in entities:
            if entity.id in mapping:
                raise InvalidEntityGraphError(
                    "Duplicate entity id in graph.", details={"id": str(entity.id)}
                )
            mapping[entity.id] = entity
        return cls(entities=MappingProxyType(mapping), relationships=tuple(relationships))

    def __len__(self) -> int:
        return len(self.entities)

    def __iter__(self):
        return iter(self.entities.values())

    def has(self, entity_id: EntityId) -> bool:
        return entity_id in self.entities

    def get(self, entity_id: EntityId) -> Entity:
        """Return the entity for ``entity_id``.

        Raises:
            EntityNotFoundError: If no such entity exists.
        """
        entity = self.entities.get(entity_id)
        if entity is None:
            raise EntityNotFoundError(
                f"Entity {entity_id} not found.", details={"entity_id": str(entity_id)}
            )
        return entity

    def by_type(self, entity_type: EntityType) -> tuple[Entity, ...]:
        return tuple(e for e in self.entities.values() if e.type is entity_type)

    def relationships_of(self, entity_id: EntityId) -> tuple[Relationship, ...]:
        """All relationships in which ``entity_id`` is the source or target."""
        return tuple(
            r for r in self.relationships if r.source == entity_id or r.target == entity_id
        )

    def relationships_by_type(
        self, relationship_type: RelationshipType
    ) -> tuple[Relationship, ...]:
        return tuple(r for r in self.relationships if r.type is relationship_type)
