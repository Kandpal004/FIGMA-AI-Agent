"""The Evidence model — the anti-hallucination backbone of the engine.

Every recommendation the Reasoning Engine makes must trace to at least one piece
of evidence, and evidence is *always* a citation of a Knowledge-Engine entry —
never a free-floating assertion. An :class:`EvidenceRef` is a **pinned snapshot**
of a cited entry: it records the entry's stable lineage id *and* the exact version
id, plus a copy of the salient facts (statement, source, confidence). Pinning the
version is deliberate — it makes a produced strategy reproducible and auditable
forever, even after the corpus is revised.

To honour the ports-and-adapters boundary, this module does **not** import the
Knowledge Engine (Phase 3). Knowledge identities are held as plain strings (the
canonical UUID strings of a ``KnowledgeId`` / ``EntryVersionId``); the
infrastructure adapter that talks to Phase 3 is what constructs these refs and
converts the typed ids to strings. The reasoning domain therefore stays fully
decoupled and unit-testable without Phase 3.

The :class:`EvidenceGraph` is the immutable registry of all evidence used within a
strategy, addressable by :class:`EvidenceId`. The reverse "which reasons/decisions
use this evidence" view is derived from the reason and decision graphs (which hold
evidence ids), so it is not duplicated here.

Testing considerations
----------------------
* :class:`EvidenceRef` validates non-empty knowledge/version ids and statement,
  and a confidence within ``[0, 1]``; it is immutable.
* :class:`EvidenceGraph` rejects duplicate ids, resolves by id (raising
  :class:`EvidenceNotFoundError` when absent), and offers dimension/lineage
  lookups; functional ``with_evidence`` never mutates the original.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from reasoning.domain.shared.ids import EvidenceId
from reasoning.domain.shared.value_objects import ReasoningDimension

__all__ = [
    "EvidenceGraph",
    "EvidenceNotFoundError",
    "EvidenceRef",
    "InvalidEvidenceError",
]


class InvalidEvidenceError(DesignDirectorError):
    """Raised when an evidence reference is constructed with invalid data."""

    code = "invalid_evidence"
    http_status = 422


class EvidenceNotFoundError(DesignDirectorError):
    """Raised when evidence is requested by an id absent from the graph."""

    code = "evidence_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """A pinned citation of a Knowledge-Engine entry used within a strategy.

    Attributes:
        id: This citation's identity within the strategy.
        knowledge_id: The cited entry's stable lineage id (UUID string).
        entry_version_id: The exact version cited (UUID string) — pinned for
            reproducibility.
        dimension: The reasoning dimension this evidence supports.
        category: The entry's knowledge category (e.g. ``"ux_laws"``).
        title: The entry's title.
        statement: The entry's crisp principle.
        source_name: The provenance (who asserts it).
        confidence: The entry's confidence score in ``[0, 1]``.
        relevance: Why this evidence applies to the decision at hand.
    """

    id: EvidenceId
    knowledge_id: str
    entry_version_id: str
    dimension: ReasoningDimension
    category: str
    title: str
    statement: str
    source_name: str
    confidence: float
    relevance: str = ""

    def __post_init__(self) -> None:
        if not self.knowledge_id or not self.knowledge_id.strip():
            raise InvalidEvidenceError("EvidenceRef.knowledge_id must be non-empty.")
        if not self.entry_version_id or not self.entry_version_id.strip():
            raise InvalidEvidenceError("EvidenceRef.entry_version_id must be non-empty.")
        if not self.statement or not self.statement.strip():
            raise InvalidEvidenceError("EvidenceRef.statement must be non-empty.")
        if not 0.0 <= self.confidence <= 1.0:
            raise InvalidEvidenceError(
                "EvidenceRef.confidence must be within [0, 1].",
                details={"confidence": self.confidence},
            )


@dataclass(frozen=True, slots=True)
class EvidenceGraph:
    """An immutable registry of the evidence cited within a strategy.

    Addressable by :class:`EvidenceId`; iteration preserves insertion order for
    deterministic output. Functional updates return a new graph.

    Attributes:
        items: The evidence refs, keyed by id (read-only).
    """

    items: Mapping[EvidenceId, EvidenceRef] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.items, MappingProxyType):
            # Copy into a read-only view; a plain dict preserves insertion order.
            object.__setattr__(self, "items", MappingProxyType(dict(self.items)))

    @classmethod
    def empty(cls) -> EvidenceGraph:
        """An empty evidence graph."""
        return cls()

    @classmethod
    def of(cls, refs: Iterable[EvidenceRef]) -> EvidenceGraph:
        """Build a graph from evidence refs.

        Raises:
            InvalidEvidenceError: If two refs share an id.
        """
        mapping: dict[EvidenceId, EvidenceRef] = {}
        for ref in refs:
            if ref.id in mapping:
                raise InvalidEvidenceError(
                    "Duplicate evidence id in graph.", details={"id": str(ref.id)}
                )
            mapping[ref.id] = ref
        return cls(items=MappingProxyType(mapping))

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items.values())

    def has(self, evidence_id: EvidenceId) -> bool:
        """Whether an evidence ref with ``evidence_id`` is present."""
        return evidence_id in self.items

    def get(self, evidence_id: EvidenceId) -> EvidenceRef:
        """Return the evidence ref for ``evidence_id``.

        Raises:
            EvidenceNotFoundError: If no such evidence exists.
        """
        ref = self.items.get(evidence_id)
        if ref is None:
            raise EvidenceNotFoundError(
                f"Evidence {evidence_id} not found.",
                details={"evidence_id": str(evidence_id)},
            )
        return ref

    def with_evidence(self, ref: EvidenceRef) -> EvidenceGraph:
        """Return a new graph with ``ref`` added.

        Raises:
            InvalidEvidenceError: If the id already exists.
        """
        if ref.id in self.items:
            raise InvalidEvidenceError(
                "Duplicate evidence id in graph.", details={"id": str(ref.id)}
            )
        return EvidenceGraph(items=MappingProxyType({**self.items, ref.id: ref}))

    def by_dimension(self, dimension: ReasoningDimension) -> tuple[EvidenceRef, ...]:
        """All evidence supporting a given dimension, in insertion order."""
        return tuple(ref for ref in self.items.values() if ref.dimension is dimension)

    def for_knowledge(self, knowledge_id: str) -> tuple[EvidenceRef, ...]:
        """All evidence pinned to a given knowledge lineage."""
        return tuple(
            ref for ref in self.items.values() if ref.knowledge_id == knowledge_id
        )
