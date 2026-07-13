"""Mappers between the ORM row and the :class:`KnowledgeEntry` aggregate.

Pure translations that keep the domain free of SQLAlchemy — a :class:`KnowledgeEntry`
never inherits from ``Base`` or holds ORM state. Value objects and graph edges are
(de)serialized to/from JSON here, in one place.
"""

from __future__ import annotations

from knowledge.domain.entry.applicability import Applicability
from knowledge.domain.entry.entry import KnowledgeEntry
from knowledge.domain.entry.relation import KnowledgeRelation, RelationType
from knowledge.domain.entry.source import Reference, ReferenceKind, Source, SourceKind
from knowledge.domain.entry.status import KnowledgeStatus
from knowledge.domain.shared.ids import (
    EntryVersionId,
    KnowledgeId,
    ReferenceId,
    RelationId,
)
from knowledge.domain.shared.value_objects import (
    Confidence,
    KnowledgeScope,
    Platform,
    Priority,
    Tag,
)
from knowledge.domain.taxonomy.category import KnowledgeCategory, Subcategory
from knowledge.infrastructure.persistence.models import KnowledgeEntryModel

__all__ = ["apply_entry", "entry_to_model", "model_to_entry"]


# --------------------------- serialization ------------------------------ #
def _source_to_json(source: Source) -> dict:
    return {"name": source.name, "kind": source.kind.value, "url": source.url, "author": source.author}


def _applicability_to_json(app: Applicability) -> dict:
    return {
        "page_types": sorted(app.page_types),
        "component_types": sorted(app.component_types),
        "platforms": sorted(p.value for p in app.platforms),
        "contexts": sorted(t.value for t in app.contexts),
    }


def _relation_to_json(rel: KnowledgeRelation) -> dict:
    return {
        "id": str(rel.id),
        "relation_type": rel.relation_type.value,
        "target": str(rel.target),
        "note": rel.note,
    }


def _reference_to_json(ref: Reference) -> dict:
    return {
        "id": str(ref.id),
        "title": ref.title,
        "kind": ref.kind.value,
        "url": ref.url,
        "author": ref.author,
        "year": ref.year,
        "note": ref.note,
    }


def _fill_model(model: KnowledgeEntryModel, entry: KnowledgeEntry) -> None:
    model.knowledge_id = entry.knowledge_id.value
    model.version = entry.version
    model.tenant_id = entry.scope.tenant_id
    model.category = entry.category.value
    model.subcategory = entry.subcategory.value if entry.subcategory else None
    model.title = entry.title
    model.statement = entry.statement
    model.description = entry.description
    model.source = _source_to_json(entry.source)
    model.confidence = entry.confidence.score
    model.priority = int(entry.priority)
    model.status = entry.status.value
    model.applicability = _applicability_to_json(entry.applicability)
    model.tags = sorted(t.value for t in entry.tags)
    model.relations = [_relation_to_json(r) for r in entry.relations]
    model.references = [_reference_to_json(r) for r in entry.references]
    model.created_at = entry.created_at
    model.updated_at = entry.updated_at


def entry_to_model(entry: KnowledgeEntry) -> KnowledgeEntryModel:
    model = KnowledgeEntryModel(id=entry.id.value)
    _fill_model(model, entry)
    return model


def apply_entry(model: KnowledgeEntryModel, entry: KnowledgeEntry) -> None:
    """Update an existing ORM row in place from a domain entry."""
    _fill_model(model, entry)


# --------------------------- deserialization ---------------------------- #
def _json_to_source(raw: dict) -> Source:
    return Source(
        name=raw["name"],
        kind=SourceKind(raw.get("kind", "other")),
        url=raw.get("url"),
        author=raw.get("author"),
    )


def _json_to_applicability(raw: dict) -> Applicability:
    return Applicability.build(
        page_types=raw.get("page_types", ()),
        component_types=raw.get("component_types", ()),
        platforms=[Platform(p) for p in raw.get("platforms", ())],
        contexts=[Tag.of(t) for t in raw.get("contexts", ())],
    )


def _json_to_relation(raw: dict) -> KnowledgeRelation:
    return KnowledgeRelation(
        id=RelationId.from_string(raw["id"]),
        relation_type=RelationType(raw["relation_type"]),
        target=KnowledgeId.from_string(raw["target"]),
        note=raw.get("note", ""),
    )


def _json_to_reference(raw: dict) -> Reference:
    return Reference(
        id=ReferenceId.from_string(raw["id"]),
        title=raw["title"],
        kind=ReferenceKind(raw.get("kind", "other")),
        url=raw.get("url"),
        author=raw.get("author"),
        year=raw.get("year"),
        note=raw.get("note", ""),
    )


def model_to_entry(model: KnowledgeEntryModel) -> KnowledgeEntry:
    return KnowledgeEntry(
        id=EntryVersionId(model.id),
        knowledge_id=KnowledgeId(model.knowledge_id),
        version=model.version,
        scope=KnowledgeScope(tenant_id=model.tenant_id),
        category=KnowledgeCategory(model.category),
        title=model.title,
        statement=model.statement,
        description=model.description,
        source=_json_to_source(model.source),
        confidence=Confidence.of(model.confidence),
        priority=Priority(model.priority),
        status=KnowledgeStatus(model.status),
        applicability=_json_to_applicability(model.applicability),
        created_at=model.created_at,
        updated_at=model.updated_at,
        subcategory=Subcategory.of(model.subcategory) if model.subcategory else None,
        tags=frozenset(Tag.of(t) for t in model.tags),
        relations=tuple(_json_to_relation(r) for r in model.relations),
        references=tuple(_json_to_reference(r) for r in model.references),
    )
