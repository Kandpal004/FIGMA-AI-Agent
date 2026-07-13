"""Command objects — the authoring service's typed input contract.

Every mutation of the corpus is expressed as one of these immutable commands, so
the authoring surface is explicit, validatable, and stable as new operations are
added. They carry only plain domain data and perform no I/O.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from knowledge.domain.entry.applicability import Applicability
from knowledge.domain.entry.relation import RelationType
from knowledge.domain.entry.source import Reference, Source
from knowledge.domain.shared.ids import EntryVersionId, KnowledgeId
from knowledge.domain.shared.value_objects import (
    Confidence,
    KnowledgeScope,
    Priority,
    Tag,
)
from knowledge.domain.taxonomy.category import KnowledgeCategory, Subcategory

__all__ = [
    "ActivateEntry",
    "AddEntry",
    "AddRelation",
    "ArchiveEntry",
    "DeprecateEntry",
    "ProposeEntry",
    "ReinstateEntry",
    "RejectEntry",
    "ReviseEntry",
]


@dataclass(frozen=True, slots=True)
class AddEntry:
    """Author a brand-new v1 DRAFT entry."""

    category: KnowledgeCategory
    title: str
    statement: str
    description: str
    source: Source
    knowledge_id: KnowledgeId | None = None
    subcategory: Subcategory | None = None
    confidence: Confidence | None = None
    priority: Priority = Priority.NORMAL
    applicability: Applicability | None = None
    tags: tuple[Tag, ...] = ()
    references: tuple[Reference, ...] = ()
    scope: KnowledgeScope | None = None


@dataclass(frozen=True, slots=True)
class ReviseEntry:
    """Create the next DRAFT version of a lineage from an existing version."""

    from_entry_version_id: EntryVersionId
    title: str | None = None
    statement: str | None = None
    description: str | None = None
    confidence: Confidence | None = None
    priority: Priority | None = None
    applicability: Applicability | None = None
    subcategory: Subcategory | None = None
    tags: Sequence[Tag] | None = None
    references: Sequence[Reference] | None = None


@dataclass(frozen=True, slots=True)
class AddRelation:
    """Add a typed relationship edge from an entry to another lineage."""

    entry_version_id: EntryVersionId
    relation_type: RelationType
    target: KnowledgeId
    note: str = ""


@dataclass(frozen=True, slots=True)
class ProposeEntry:
    """Submit a DRAFT for the validation gate (DRAFT → PROPOSED)."""

    entry_version_id: EntryVersionId


@dataclass(frozen=True, slots=True)
class ActivateEntry:
    """Pass a PROPOSED entry through the validation gate (PROPOSED → ACTIVE).

    Activating supersedes any prior ACTIVE version of the same lineage, so a
    lineage has at most one ACTIVE version at a time.
    """

    entry_version_id: EntryVersionId
    approver: str = ""


@dataclass(frozen=True, slots=True)
class RejectEntry:
    """Reject a PROPOSED entry back to DRAFT (PROPOSED → DRAFT)."""

    entry_version_id: EntryVersionId
    reason: str = ""


@dataclass(frozen=True, slots=True)
class DeprecateEntry:
    """Mark an ACTIVE entry as no longer recommended (ACTIVE → DEPRECATED)."""

    entry_version_id: EntryVersionId
    reason: str = ""


@dataclass(frozen=True, slots=True)
class ReinstateEntry:
    """Return a DEPRECATED entry to service (DEPRECATED → ACTIVE)."""

    entry_version_id: EntryVersionId


@dataclass(frozen=True, slots=True)
class ArchiveEntry:
    """Archive an entry for history only (→ ARCHIVED)."""

    entry_version_id: EntryVersionId
    reason: str = ""
