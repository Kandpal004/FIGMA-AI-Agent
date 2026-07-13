"""The KnowledgeEntry aggregate — one immutable, versioned unit of knowledge.

This is the heart of the corpus: a single, citable, applicable, versioned
principle. It gathers everything an entry needs to be a *source of truth* — its
classification, its crisp statement and prose, its provenance and citations, how
firmly it is held and how important it is, where it applies, its lifecycle status,
and its typed relationships to other knowledge.

It realises the approved **immutable, lineage-based versioning** model:

* ``knowledge_id`` (a :class:`KnowledgeId`) is the stable lineage — constant across
  every version, and what relationships point at.
* ``id`` (an :class:`EntryVersionId`) identifies this one immutable version.

The aggregate is frozen. Every change returns a *new* instance via a functional
updater; a *content* change (:meth:`revise`) mints a new version, while a
*lifecycle* change (:meth:`with_status`) evolves the same version. Timestamps are
supplied by the caller (the application layer, via an injected clock) so the
domain reads no clock.

Testing considerations
----------------------
* :meth:`create` yields a v1 ``DRAFT`` entry with fresh lineage + version ids.
* :meth:`revise` increments the version, mints a new version id, resets to
  ``DRAFT``, and preserves the lineage and relations.
* :meth:`with_status` evolves status on the same version and bumps ``updated_at``.
* :meth:`applies_to` delegates to the entry's :class:`Applicability`.
* The aggregate is immutable and rejects blank title/statement and version < 1.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from datetime import datetime

from core.errors import DesignDirectorError

from knowledge.domain.entry.applicability import Applicability
from knowledge.domain.entry.relation import KnowledgeRelation
from knowledge.domain.entry.source import Reference, Source
from knowledge.domain.entry.status import KnowledgeStatus
from knowledge.domain.shared.ids import EntryVersionId, KnowledgeId
from knowledge.domain.shared.value_objects import (
    Confidence,
    KnowledgeScope,
    Platform,
    Priority,
    Tag,
)
from knowledge.domain.taxonomy.category import KnowledgeCategory, Subcategory

__all__ = ["InvalidKnowledgeEntryError", "KnowledgeEntry"]


class InvalidKnowledgeEntryError(DesignDirectorError):
    """Raised when a knowledge entry is constructed with invalid attributes."""

    code = "invalid_knowledge_entry"
    http_status = 422


@dataclass(frozen=True, slots=True)
class KnowledgeEntry:
    """An immutable, versioned unit of curated knowledge.

    Attributes:
        id: This version's identity.
        knowledge_id: The stable lineage identity (constant across versions).
        version: Monotonic version number (``>= 1``).
        scope: Global or tenant-scoped visibility.
        category: Top-level classification.
        subcategory: Optional refinement within the category.
        title: Short human title.
        statement: The crisp, quotable principle.
        description: Fuller prose explanation.
        source: Provenance — who asserts it.
        confidence: How firmly it is held.
        priority: How important it is for ranking/conflict resolution.
        status: Lifecycle status.
        applicability: Where it applies (the relevance predicate).
        tags: Free-form labels for filtering.
        relations: Typed edges to other knowledge (by lineage).
        references: Supporting citations.
        created_at: When this version was created.
        updated_at: When this version was last touched.
    """

    id: EntryVersionId
    knowledge_id: KnowledgeId
    version: int
    scope: KnowledgeScope
    category: KnowledgeCategory
    title: str
    statement: str
    description: str
    source: Source
    confidence: Confidence
    priority: Priority
    status: KnowledgeStatus
    applicability: Applicability
    created_at: datetime
    updated_at: datetime
    subcategory: Subcategory | None = None
    tags: frozenset[Tag] = field(default_factory=frozenset)
    relations: tuple[KnowledgeRelation, ...] = ()
    references: tuple[Reference, ...] = ()

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidKnowledgeEntryError(
                "KnowledgeEntry.version must be >= 1.", details={"version": self.version}
            )
        if not self.title or not self.title.strip():
            raise InvalidKnowledgeEntryError("KnowledgeEntry.title must be non-empty.")
        if not self.statement or not self.statement.strip():
            raise InvalidKnowledgeEntryError("KnowledgeEntry.statement must be non-empty.")
        object.__setattr__(self, "tags", frozenset(self.tags))
        object.__setattr__(self, "relations", tuple(self.relations))
        object.__setattr__(self, "references", tuple(self.references))

    # -- construction ------------------------------------------------------ #
    @classmethod
    def create(
        cls,
        *,
        category: KnowledgeCategory,
        title: str,
        statement: str,
        description: str,
        source: Source,
        at: datetime,
        knowledge_id: KnowledgeId | None = None,
        subcategory: Subcategory | None = None,
        confidence: Confidence | None = None,
        priority: Priority = Priority.NORMAL,
        applicability: Applicability | None = None,
        tags: Iterable[Tag] = (),
        references: Iterable[Reference] = (),
        scope: KnowledgeScope | None = None,
        status: KnowledgeStatus = KnowledgeStatus.DRAFT,
    ) -> KnowledgeEntry:
        """Author a brand-new v1 entry (a fresh lineage unless one is supplied)."""
        return cls(
            id=EntryVersionId.new(),
            knowledge_id=knowledge_id or KnowledgeId.new(),
            version=1,
            scope=scope or KnowledgeScope.global_(),
            category=category,
            title=title,
            statement=statement,
            description=description,
            source=source,
            confidence=confidence or Confidence.default(),
            priority=priority,
            status=status,
            applicability=applicability or Applicability.any(),
            created_at=at,
            updated_at=at,
            subcategory=subcategory,
            tags=frozenset(tags),
            references=tuple(references),
        )

    # -- queries ----------------------------------------------------------- #
    @property
    def lineage(self) -> KnowledgeId:
        """The stable lineage identity of this entry."""
        return self.knowledge_id

    @property
    def is_active(self) -> bool:
        """Whether this version is currently ``ACTIVE``."""
        return self.status is KnowledgeStatus.ACTIVE

    @property
    def is_global(self) -> bool:
        """Whether this entry is universal (global scope)."""
        return self.scope.is_global

    def applies_to(
        self,
        *,
        page_type: str | None = None,
        component_type: str | None = None,
        platform: Platform | None = None,
        contexts: Iterable[Tag] = (),
    ) -> bool:
        """Whether this entry applies to the described situation."""
        return self.applicability.matches(
            page_type=page_type,
            component_type=component_type,
            platform=platform,
            contexts=contexts,
        )

    def relations_of(self, *relation_types: object) -> tuple[KnowledgeRelation, ...]:
        """The relations of the given types (all relations if none specified)."""
        if not relation_types:
            return self.relations
        wanted = set(relation_types)
        return tuple(r for r in self.relations if r.relation_type in wanted)

    # -- functional updaters ---------------------------------------------- #
    def with_status(self, status: KnowledgeStatus, *, at: datetime) -> KnowledgeEntry:
        """Evolve this *same* version's lifecycle status (no new version)."""
        return replace(self, status=status, updated_at=at)

    def with_confidence(self, confidence: Confidence, *, at: datetime) -> KnowledgeEntry:
        """Return a copy with a revised confidence, same version."""
        return replace(self, confidence=confidence, updated_at=at)

    def add_relation(self, relation: KnowledgeRelation, *, at: datetime) -> KnowledgeEntry:
        """Return a copy with a relationship edge added, same version."""
        return replace(self, relations=(*self.relations, relation), updated_at=at)

    def revise(
        self,
        *,
        at: datetime,
        title: str | None = None,
        statement: str | None = None,
        description: str | None = None,
        confidence: Confidence | None = None,
        priority: Priority | None = None,
        applicability: Applicability | None = None,
        subcategory: Subcategory | None = None,
        tags: Iterable[Tag] | None = None,
        references: Iterable[Reference] | None = None,
    ) -> KnowledgeEntry:
        """Create the next version under the same lineage.

        Returns a new ``DRAFT`` entry with ``version + 1`` and a fresh version id,
        preserving the lineage, category, scope, and relations while applying the
        supplied content changes. The prior version is left untouched (immutable
        history).
        """
        return replace(
            self,
            id=EntryVersionId.new(),
            version=self.version + 1,
            status=KnowledgeStatus.DRAFT,
            created_at=at,
            updated_at=at,
            title=self.title if title is None else title,
            statement=self.statement if statement is None else statement,
            description=self.description if description is None else description,
            confidence=self.confidence if confidence is None else confidence,
            priority=self.priority if priority is None else priority,
            applicability=self.applicability if applicability is None else applicability,
            subcategory=self.subcategory if subcategory is None else subcategory,
            tags=self.tags if tags is None else frozenset(tags),
            references=self.references if references is None else tuple(references),
        )
