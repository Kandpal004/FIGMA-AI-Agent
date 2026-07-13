"""Rationale — the deterministic, cited answer the reasoner produces.

When an agent asks *"why should this component exist?"* or *"which UX law supports
this?"*, the engine must reply with **evidence, not a guess**. A :class:`Rationale`
is that reply: a ranked set of :class:`Citation` s (each an applicable principle,
with why it applies and its provenance), any :class:`Conflict` s between them (with
a deterministic resolution), and an aggregate confidence — assembled entirely from
the structured corpus, reproducible for the same context.

These are pure value objects. The :class:`~knowledge.application.reasoner.KnowledgeReasoner`
builds them; nothing here performs I/O.

Testing considerations
----------------------
* :meth:`Citation.from_entry` projects an entry into a flat, cited claim.
* A :class:`Rationale` reports emptiness and its primary citation, and carries the
  conflicts the reasoner detected.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from knowledge.domain.entry.entry import KnowledgeEntry
from knowledge.domain.reasoning.context import DecisionContext
from knowledge.domain.shared.ids import EntryVersionId, KnowledgeId
from knowledge.domain.shared.value_objects import Confidence, Priority
from knowledge.domain.taxonomy.category import KnowledgeCategory

__all__ = ["Citation", "Conflict", "Rationale"]


@dataclass(frozen=True, slots=True)
class Citation:
    """One cited principle within a rationale — a flat, serializable claim.

    Attributes:
        knowledge_id: The cited entry's lineage.
        entry_version_id: The exact version cited (for reproducibility).
        category: The entry's category.
        title: The entry's title.
        statement: The entry's crisp principle.
        confidence: How firmly the principle is held.
        priority: The principle's priority.
        source_name: The provenance (who asserts it).
        why: Why this principle applies to the decision at hand.
    """

    knowledge_id: KnowledgeId
    entry_version_id: EntryVersionId
    category: KnowledgeCategory
    title: str
    statement: str
    confidence: Confidence
    priority: Priority
    source_name: str
    why: str

    @classmethod
    def from_entry(cls, entry: KnowledgeEntry, *, why: str) -> Self:
        """Project a :class:`KnowledgeEntry` into a citation with a reason."""
        return cls(
            knowledge_id=entry.knowledge_id,
            entry_version_id=entry.id,
            category=entry.category,
            title=entry.title,
            statement=entry.statement,
            confidence=entry.confidence,
            priority=entry.priority,
            source_name=entry.source.name,
            why=why,
        )

    @property
    def weight(self) -> float:
        """A deterministic weight (priority × confidence) used to resolve
        conflicts and to order citations."""
        return float(int(self.priority)) * self.confidence.score


@dataclass(frozen=True, slots=True)
class Conflict:
    """A detected tension between two cited principles, with its resolution.

    Attributes:
        winner: The citation that prevails (higher priority × confidence).
        loser: The citation that yields.
        note: An explanation of the tension and how it was resolved.
    """

    winner: Citation
    loser: Citation
    note: str


@dataclass(frozen=True, slots=True)
class Rationale:
    """The cited, deterministic answer to a decision question.

    Attributes:
        context: The decision the rationale addresses.
        citations: The applicable principles, ranked best-first.
        conflicts: Any tensions detected among the citations, resolved.
        aggregate_confidence: The mean confidence of the cited principles.
        summary: A short human-readable synthesis.
    """

    context: DecisionContext
    citations: tuple[Citation, ...]
    conflicts: tuple[Conflict, ...]
    aggregate_confidence: float
    summary: str

    @property
    def is_empty(self) -> bool:
        """Whether no applicable principle was found."""
        return not self.citations

    @property
    def primary(self) -> Citation | None:
        """The highest-ranked citation, if any."""
        return self.citations[0] if self.citations else None
