"""The Evidence model — the provenance backbone of the Customer Psychology Engine.

Every psychological determination the engine makes is grounded in
:class:`PsychologyEvidence`: a normalised, cited fact carrying its origin (a
:class:`ProvenanceKind` and the id it has in the source engine — a Brand-Strategy
decision id, a Business-Strategy decision id, a Knowledge lineage id, a Research
evidence id, …). A :class:`Citation` is a lightweight reference *into* the
:class:`EvidenceGraph` used everywhere a finding needs to point at its support.

This is the anti-hallucination contract, made structural: the report aggregate rejects
any determination, matrix cell, framework application, or graph node that references
evidence absent from this graph. No citation ⇒ no psychological claim. Everything is
evidence-backed.

Pure domain: standard library, the shared-kernel error base, psychology ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from psychology.domain.shared.ids import PsychologyEvidenceId
from psychology.domain.shared.value_objects import Confidence, ProvenanceKind, Tag

__all__ = [
    "Citation",
    "EvidenceGraph",
    "EvidenceNotFoundError",
    "InvalidEvidenceError",
    "PsychologyEvidence",
]


class InvalidEvidenceError(DesignDirectorError):
    """Raised when evidence is constructed with invalid data."""

    code = "invalid_psychology_evidence"
    http_status = 422


class EvidenceNotFoundError(DesignDirectorError):
    """Raised when evidence is requested by an id absent from the graph."""

    code = "psychology_evidence_not_found"
    http_status = 404


@dataclass(frozen=True, slots=True)
class PsychologyEvidence:
    """One normalised, cited fact underpinning the psychology model.

    Attributes:
        id: Evidence identity within this report.
        provenance: Which upstream engine (or future source) it came from.
        external_ref: The identity it carries in that source system (a Brand-Strategy
            decision id, a Knowledge lineage id, …) — the audit anchor back to origin.
        claim: The crisp statement the psychology relies on.
        confidence: Confidence in the fact.
        statement: The fuller supporting text, if any.
        source_name: A human-readable source label.
        tags: Free-form tags for filtering.
    """

    id: PsychologyEvidenceId
    provenance: ProvenanceKind
    external_ref: str
    claim: str
    confidence: Confidence
    statement: str = ""
    source_name: str = ""
    tags: frozenset[Tag] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.claim or not self.claim.strip():
            raise InvalidEvidenceError("PsychologyEvidence.claim must be non-empty.")
        if not self.external_ref or not self.external_ref.strip():
            raise InvalidEvidenceError(
                "PsychologyEvidence.external_ref must be non-empty (audit anchor)."
            )
        object.__setattr__(self, "tags", frozenset(self.tags))


@dataclass(frozen=True, slots=True)
class Citation:
    """A reference from a psychology finding to the evidence that supports it.

    Attributes:
        evidence_id: The evidence being cited (must resolve in the graph).
        relevance: Why this evidence supports the citing finding.
    """

    evidence_id: PsychologyEvidenceId
    relevance: str = ""


@dataclass(frozen=True, slots=True)
class EvidenceGraph:
    """An immutable registry of the evidence a report rests on."""

    items: Mapping[PsychologyEvidenceId, PsychologyEvidence] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not isinstance(self.items, MappingProxyType):
            object.__setattr__(self, "items", MappingProxyType(dict(self.items)))

    @classmethod
    def empty(cls) -> EvidenceGraph:
        return cls()

    @classmethod
    def of(cls, evidence: Iterable[PsychologyEvidence]) -> EvidenceGraph:
        """Build a graph from evidence.

        Raises:
            InvalidEvidenceError: If two items share an id.
        """
        mapping: dict[PsychologyEvidenceId, PsychologyEvidence] = {}
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

    def has(self, evidence_id: PsychologyEvidenceId) -> bool:
        return evidence_id in self.items

    def get(self, evidence_id: PsychologyEvidenceId) -> PsychologyEvidence:
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

    def by_provenance(self, provenance: ProvenanceKind) -> tuple[PsychologyEvidence, ...]:
        return tuple(e for e in self.items.values() if e.provenance is provenance)

    def missing(
        self, evidence_ids: Iterable[PsychologyEvidenceId]
    ) -> tuple[PsychologyEvidenceId, ...]:
        """The subset of ``evidence_ids`` absent from this graph."""
        return tuple(eid for eid in evidence_ids if not self.has(eid))
