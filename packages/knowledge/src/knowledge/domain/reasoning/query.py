"""KnowledgeQuery — the structured, deterministic retrieval predicate.

This is the deliberate opposite of a vector similarity search: a
:class:`KnowledgeQuery` is an explicit set of structured filters (category, tags,
platform, status, confidence, priority, scope) that either match an entry or do
not — the same query always returns the same, explainable set. Ranking is likewise
deterministic, from a stable sort key.

The query owns two pure functions the repository uses: :meth:`matches` (the filter
predicate) and :meth:`sort_key` (the ranking key). Keeping them here makes the
query self-contained and unit-testable, and lets any repository — in-memory or
SQL — apply identical semantics.

Testing considerations
----------------------
* Default ``statuses`` is ``{ACTIVE}``; only servable knowledge is returned unless
  broadened.
* Scope visibility is enforced (global entries always visible; tenant entries only
  to their tenant).
* ``sort_key`` orders by the chosen :class:`SortOrder`; ``RELEVANCE`` ranks by
  priority, then confidence, then applicability specificity.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum

from knowledge.domain.entry.entry import KnowledgeEntry
from knowledge.domain.entry.status import ACTIVE_STATUSES, KnowledgeStatus
from knowledge.domain.shared.value_objects import (
    Confidence,
    Platform,
    Priority,
    Tag,
)
from knowledge.domain.taxonomy.category import KnowledgeCategory, Subcategory

__all__ = ["KnowledgeQuery", "QueryResult", "SortOrder"]


class SortOrder(str, Enum):
    """How query results are ordered (always descending — best first)."""

    RELEVANCE = "relevance"
    CONFIDENCE = "confidence"
    PRIORITY = "priority"
    RECENCY = "recency"


@dataclass(frozen=True, slots=True)
class KnowledgeQuery:
    """A structured retrieval predicate over the corpus.

    Every field defaults to "unconstrained" except ``statuses`` (defaults to the
    servable set, ``{ACTIVE}``). A constrained field filters; an unconstrained one
    does not.

    Attributes:
        categories: Restrict to these categories (empty = any).
        subcategory: Restrict to this subcategory.
        tags_any: Entry must carry at least one of these tags.
        tags_all: Entry must carry all of these tags.
        platforms: Restrict to entries applicable to these platforms.
        statuses: Lifecycle statuses to include (default ``{ACTIVE}``).
        min_confidence: Minimum confidence.
        min_priority: Minimum priority.
        viewer_tenant_id: The viewer's tenant, for scope resolution.
        text: Optional case-insensitive substring over title/statement/description.
        sort: Result ordering.
        limit: Maximum number of results.
    """

    categories: frozenset[KnowledgeCategory] = field(default_factory=frozenset)
    subcategory: Subcategory | None = None
    tags_any: frozenset[Tag] = field(default_factory=frozenset)
    tags_all: frozenset[Tag] = field(default_factory=frozenset)
    platforms: frozenset[Platform] = field(default_factory=frozenset)
    statuses: frozenset[KnowledgeStatus] = field(default_factory=lambda: ACTIVE_STATUSES)
    min_confidence: Confidence | None = None
    min_priority: Priority | None = None
    viewer_tenant_id: uuid.UUID | None = None
    text: str | None = None
    sort: SortOrder = SortOrder.RELEVANCE
    limit: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "categories", frozenset(self.categories))
        object.__setattr__(self, "tags_any", frozenset(self.tags_any))
        object.__setattr__(self, "tags_all", frozenset(self.tags_all))
        object.__setattr__(self, "platforms", frozenset(self.platforms))
        object.__setattr__(self, "statuses", frozenset(self.statuses))

    def matches(self, entry: KnowledgeEntry) -> bool:
        """Whether ``entry`` satisfies every constrained filter of this query."""
        if entry.status not in self.statuses:
            return False
        if not entry.scope.visible_to(self.viewer_tenant_id):
            return False
        if self.categories and entry.category not in self.categories:
            return False
        if self.subcategory is not None and entry.subcategory != self.subcategory:
            return False
        if self.tags_all and not self.tags_all <= entry.tags:
            return False
        if self.tags_any and entry.tags.isdisjoint(self.tags_any):
            return False
        if self.platforms:
            entry_platforms = entry.applicability.platforms
            if entry_platforms:  # empty = universal (matches any platform)
                if entry_platforms.isdisjoint(self.platforms) and (
                    Platform.AGNOSTIC not in entry_platforms
                ):
                    return False
        if self.min_confidence is not None and entry.confidence.score < self.min_confidence.score:
            return False
        if self.min_priority is not None and entry.priority < self.min_priority:
            return False
        if self.text:
            needle = self.text.lower()
            haystack = f"{entry.title}\n{entry.statement}\n{entry.description}".lower()
            if needle not in haystack:
                return False
        return True

    def sort_key(self, entry: KnowledgeEntry) -> tuple:
        """A stable, descending sort key for ``entry`` under this query's order."""
        if self.sort is SortOrder.CONFIDENCE:
            return (entry.confidence.score, int(entry.priority))
        if self.sort is SortOrder.PRIORITY:
            return (int(entry.priority), entry.confidence.score)
        if self.sort is SortOrder.RECENCY:
            return (entry.updated_at.timestamp(),)
        # RELEVANCE: priority, then confidence, then applicability specificity.
        return (
            int(entry.priority),
            entry.confidence.score,
            entry.applicability.specificity(),
        )


@dataclass(frozen=True, slots=True)
class QueryResult:
    """The outcome of a structured query: ranked entries and the total matched.

    Attributes:
        entries: The matching entries, already ranked best-first (and truncated to
            the query's limit).
        total: The number of entries that matched before any limit was applied.
    """

    entries: tuple[KnowledgeEntry, ...]
    total: int

    @property
    def is_empty(self) -> bool:
        return not self.entries

    @property
    def top(self) -> KnowledgeEntry | None:
        return self.entries[0] if self.entries else None
