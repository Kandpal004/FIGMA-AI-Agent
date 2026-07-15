"""The Evidence model — the provenance backbone of the Component Intelligence Engine.

Every component decision the engine makes is grounded in :class:`CIEvidence`: a normalised,
cited fact carrying its origin (a :class:`ProvenanceKind` and the id it has in the source
engine — a Wireframe plan id, a Design Language spec id, a Creative Director review id, a UX
decision id, a Business-Strategy decision id, …). A :class:`Citation` is a lightweight
reference *into* the :class:`EvidenceGraph` used everywhere a decision needs to point at its
support.

This is the anti-randomness contract made structural: the specification rejects any component
decision, purpose, impact, rule, or graph node that references evidence absent from this graph.
No citation ⇒ no component. A component may only enter a composition because the evidence says
it improves a business outcome — never at random.

Pure domain: standard library, the shared-kernel error base, CI ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from component_intelligence.domain.shared.ids import CIEvidenceId
from component_intelligence.domain.shared.value_objects import Confidence, ProvenanceKind, Tag

__all__ = [
    "CIEvidence",
    "Citation",
    "EvidenceGraph",
    "EvidenceNotFoundError",
    "InvalidEvidenceError",
]


class InvalidEvidenceError(DesignDirectorError):
    """Raised when evidence is constructed with invalid data."""

    code = "invalid_component_intelligence_evidence"
    http_status = 422


class EvidenceNotFoundError(DesignDirectorError):
    """Raised when evidence is requested by an id absent from the graph."""

    code = "component_intelligence_evidence_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class CIEvidence:
    """One normalised, cited fact underpinning a component decision.

    Attributes:
        id: Evidence identity within this specification.
        provenance: Which upstream engine (or future source) it came from.
        external_ref: The identity it carries in that source system — the audit anchor.
        claim: The crisp statement the decision relies on.
        confidence: Confidence in the fact.
        statement: The fuller supporting text, if any.
        source_name: A human-readable source label.
        tags: Free-form tags for filtering.
    """

    id: CIEvidenceId
    provenance: ProvenanceKind
    external_ref: str
    claim: str
    confidence: Confidence
    statement: str = ""
    source_name: str = ""
    tags: frozenset[Tag] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.claim or not self.claim.strip():
            raise InvalidEvidenceError("CIEvidence.claim must be non-empty.")
        if not self.external_ref or not self.external_ref.strip():
            raise InvalidEvidenceError(
                "CIEvidence.external_ref must be non-empty (audit anchor)."
            )
        object.__setattr__(self, "tags", frozenset(self.tags))


@dataclass(frozen=True, slots=True)
class Citation:
    """A reference from a component decision to the evidence that supports it.

    Attributes:
        evidence_id: The evidence being cited (must resolve in the graph).
        relevance: Why this evidence supports the citing decision.
    """

    evidence_id: CIEvidenceId
    relevance: str = ""


@dataclass(frozen=True, slots=True)
class EvidenceGraph:
    """An immutable registry of the evidence a specification rests on."""

    items: Mapping[CIEvidenceId, CIEvidence] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.items, MappingProxyType):
            object.__setattr__(self, "items", MappingProxyType(dict(self.items)))

    @classmethod
    def empty(cls) -> EvidenceGraph:
        return cls()

    @classmethod
    def of(cls, evidence: Iterable[CIEvidence]) -> EvidenceGraph:
        """Build a graph from evidence.

        Raises:
            InvalidEvidenceError: If two items share an id.
        """
        mapping: dict[CIEvidenceId, CIEvidence] = {}
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

    def has(self, evidence_id: CIEvidenceId) -> bool:
        return evidence_id in self.items

    def get(self, evidence_id: CIEvidenceId) -> CIEvidence:
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

    def by_provenance(self, provenance: ProvenanceKind) -> tuple[CIEvidence, ...]:
        return tuple(e for e in self.items.values() if e.provenance is provenance)

    def missing(self, evidence_ids: Iterable[CIEvidenceId]) -> tuple[CIEvidenceId, ...]:
        """The subset of ``evidence_ids`` absent from this graph."""
        return tuple(eid for eid in evidence_ids if not self.has(eid))
