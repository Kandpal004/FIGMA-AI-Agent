"""The Evidence model — the anti-opinion backbone of the intelligence engine.

Every recommendation, best practice, and matrix verdict the engine produces must
trace to a citation of a Knowledge-Engine entry — never a free-floating opinion.
An :class:`EvidenceRef` is a **pinned snapshot** of a cited entry (its stable
lineage id *and* exact version id, plus the salient facts), so a produced report
is reproducible and auditable even after the corpus is revised.

To keep the domain independent of the Knowledge Engine (Phase 3), knowledge
identities are held as plain strings; the infrastructure adapter that queries
Phase 3 constructs these refs. The :class:`EvidenceGraph` is the immutable registry
of all evidence in a report, addressable by :class:`EvidenceId`.

Pure domain: standard library, the shared-kernel error base, and competitive ids.

Testing considerations
----------------------
* :class:`EvidenceRef` validates non-empty knowledge/version ids and statement,
  and a confidence within ``[0, 1]``; it is immutable.
* :class:`EvidenceGraph` rejects duplicate ids, resolves by id (raising
  :class:`EvidenceNotFoundError` when absent), and its functional ``with_evidence``
  never mutates the original.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from competitive.domain.shared.ids import EvidenceId
from competitive.domain.shared.value_objects import CompetitorDimension

__all__ = [
    "EvidenceGraph",
    "EvidenceNotFoundError",
    "EvidenceRef",
    "InvalidEvidenceError",
]


class InvalidEvidenceError(DesignDirectorError):
    """Raised when an evidence reference is constructed with invalid data."""

    code = "invalid_competitive_evidence"
    http_status = 422


class EvidenceNotFoundError(DesignDirectorError):
    """Raised when evidence is requested by an id absent from the graph."""

    code = "competitive_evidence_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """A pinned citation of a Knowledge-Engine entry used within a report.

    Attributes:
        id: This citation's identity within the report.
        knowledge_id: The cited entry's stable lineage id (UUID string).
        entry_version_id: The exact version cited (UUID string) — pinned for
            reproducibility.
        category: The entry's knowledge category.
        title: The entry's title.
        statement: The entry's crisp principle.
        source_name: The provenance (who asserts it).
        confidence: The entry's confidence score in ``[0, 1]``.
        relevance: Why this evidence applies to the finding at hand.
        dimension: The competitor dimension it supports, if any.
    """

    id: EvidenceId
    knowledge_id: str
    entry_version_id: str
    category: str
    title: str
    statement: str
    source_name: str
    confidence: float
    relevance: str = ""
    dimension: CompetitorDimension | None = None

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
    """An immutable registry of the evidence cited within a report.

    Addressable by :class:`EvidenceId`; iteration preserves insertion order for
    deterministic output.
    """

    items: Mapping[EvidenceId, EvidenceRef] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.items, MappingProxyType):
            object.__setattr__(self, "items", MappingProxyType(dict(self.items)))

    @classmethod
    def empty(cls) -> EvidenceGraph:
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
        if ref.id in self.items:
            raise InvalidEvidenceError(
                "Duplicate evidence id in graph.", details={"id": str(ref.id)}
            )
        return EvidenceGraph(items=MappingProxyType({**self.items, ref.id: ref}))

    def by_dimension(self, dimension: CompetitorDimension) -> tuple[EvidenceRef, ...]:
        return tuple(r for r in self.items.values() if r.dimension is dimension)
