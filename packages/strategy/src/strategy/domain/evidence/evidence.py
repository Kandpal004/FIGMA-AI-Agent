"""The Evidence model — the provenance backbone of the Business Strategy Engine.

Every strategic decision the engine makes is grounded in :class:`StrategyEvidence`: a
normalised, cited fact carrying its origin (a :class:`ProvenanceKind` and the id it
has in the source engine — a Knowledge lineage id, a Research evidence id, a
Competitor evidence id, a Reasoning conclusion id). A :class:`Citation` is a
lightweight reference *into* the :class:`EvidenceGraph` used everywhere a decision or
section needs to point at its support.

This is the anti-hallucination contract, made structural: the report aggregate
rejects any decision, section, edge, risk, or opportunity that references evidence
absent from this graph. No citation ⇒ no decision.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import StrategyEvidenceId
from strategy.domain.shared.value_objects import Confidence, ProvenanceKind, Tag

__all__ = [
    "Citation",
    "EvidenceGraph",
    "EvidenceNotFoundError",
    "InvalidEvidenceError",
    "StrategyEvidence",
]


class InvalidEvidenceError(DesignDirectorError):
    """Raised when evidence is constructed with invalid data."""

    code = "invalid_strategy_evidence"
    http_status = 422


class EvidenceNotFoundError(DesignDirectorError):
    """Raised when evidence is requested by an id absent from the graph."""

    code = "strategy_evidence_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class StrategyEvidence:
    """One normalised, cited fact underpinning strategy.

    Attributes:
        id: Evidence identity within this report.
        provenance: Which upstream engine (or future source) it came from.
        external_ref: The identity it carries in that source system (e.g. a Knowledge
            lineage id, a Research evidence id) — the audit anchor back to origin.
        claim: The crisp statement the strategy relies on.
        statement: The fuller supporting text, if any.
        source_name: A human-readable source label (e.g. "NNG", "Competitor: Aesop").
        confidence: Confidence in the fact.
        tags: Free-form tags for filtering.
    """

    id: StrategyEvidenceId
    provenance: ProvenanceKind
    external_ref: str
    claim: str
    confidence: Confidence
    statement: str = ""
    source_name: str = ""
    tags: frozenset[Tag] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.claim or not self.claim.strip():
            raise InvalidEvidenceError("StrategyEvidence.claim must be non-empty.")
        if not self.external_ref or not self.external_ref.strip():
            raise InvalidEvidenceError(
                "StrategyEvidence.external_ref must be non-empty (audit anchor)."
            )
        object.__setattr__(self, "tags", frozenset(self.tags))


@dataclass(frozen=True, slots=True)
class Citation:
    """A reference from a strategic object to the evidence that supports it.

    Attributes:
        evidence_id: The evidence being cited (must resolve in the graph).
        relevance: Why this evidence supports the citing decision.
    """

    evidence_id: StrategyEvidenceId
    relevance: str = ""


@dataclass(frozen=True, slots=True)
class EvidenceGraph:
    """An immutable registry of the evidence a report rests on."""

    items: Mapping[StrategyEvidenceId, StrategyEvidence] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.items, MappingProxyType):
            object.__setattr__(self, "items", MappingProxyType(dict(self.items)))

    @classmethod
    def empty(cls) -> EvidenceGraph:
        return cls()

    @classmethod
    def of(cls, evidence: Iterable[StrategyEvidence]) -> EvidenceGraph:
        """Build a graph from evidence.

        Raises:
            InvalidEvidenceError: If two items share an id.
        """
        mapping: dict[StrategyEvidenceId, StrategyEvidence] = {}
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

    def has(self, evidence_id: StrategyEvidenceId) -> bool:
        return evidence_id in self.items

    def get(self, evidence_id: StrategyEvidenceId) -> StrategyEvidence:
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

    def by_provenance(self, provenance: ProvenanceKind) -> tuple[StrategyEvidence, ...]:
        return tuple(e for e in self.items.values() if e.provenance is provenance)

    def resolve_all(self, evidence_ids: Iterable[StrategyEvidenceId]) -> bool:
        """Whether every id in ``evidence_ids`` resolves in this graph."""
        return all(self.has(eid) for eid in evidence_ids)

    def missing(
        self, evidence_ids: Iterable[StrategyEvidenceId]
    ) -> tuple[StrategyEvidenceId, ...]:
        """The subset of ``evidence_ids`` absent from this graph."""
        return tuple(eid for eid in evidence_ids if not self.has(eid))
