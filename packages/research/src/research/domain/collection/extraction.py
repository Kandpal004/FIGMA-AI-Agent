"""Raw extraction candidates — what an extraction adapter produces from an artifact.

An :class:`ExtractionPort` adapter (a deterministic parser today; vision/LLM later)
turns a :class:`RawArtifact` into a :class:`RawExtraction`: lightweight *candidate*
entities, evidence, and relationships. These are not yet domain
:class:`~research.domain.entity.entity.Entity` /
:class:`~research.domain.evidence.evidence.Evidence` objects — the pipeline refines,
validates, and grounds them into those. Keeping candidates separate is what lets all
provider intelligence live behind the port while the domain stays deterministic.

Pure domain: standard library, the shared-kernel error base, research ids, source
locator, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from research.domain.shared.ids import ArtifactId
from research.domain.shared.value_objects import (
    Confidence,
    EntityType,
    RelationshipType,
    ResearchCategory,
)
from research.domain.source.source import SourceLocator

__all__ = [
    "CandidateEntity",
    "CandidateEvidence",
    "CandidateRelationship",
    "InvalidExtractionError",
    "RawExtraction",
]


class InvalidExtractionError(DesignDirectorError):
    """Raised when an extraction candidate is constructed with invalid data."""

    code = "invalid_extraction"
    http_status = 422


@dataclass(frozen=True, slots=True)
class CandidateEntity:
    """A candidate entity proposed by an extraction adapter.

    Attributes:
        type: The proposed entity type.
        label: The entity's label (used to resolve relationships by name).
        attributes: Proposed attributes (read-only).
        confidence: The adapter's confidence in the candidate.
    """

    type: EntityType
    label: str
    confidence: Confidence
    attributes: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidExtractionError("CandidateEntity.label must be non-empty.")
        if not isinstance(self.attributes, MappingProxyType):
            object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))


@dataclass(frozen=True, slots=True)
class CandidateEvidence:
    """A candidate piece of evidence proposed by an extraction adapter.

    Attributes:
        claim: The finding (a fact, not an opinion).
        snippet: The raw excerpt supporting it.
        confidence: The adapter's confidence.
        category: The research category it belongs to.
        locator: Where in the source it was found, if narrower than the artifact.
    """

    claim: str
    confidence: Confidence
    category: ResearchCategory
    snippet: str = ""
    locator: SourceLocator | None = None

    def __post_init__(self) -> None:
        if not self.claim or not self.claim.strip():
            raise InvalidExtractionError("CandidateEvidence.claim must be non-empty.")


@dataclass(frozen=True, slots=True)
class CandidateRelationship:
    """A candidate relationship between two entities, by label.

    Attributes:
        type: The relationship type.
        source_label: The label of the source entity.
        target_label: The label of the target entity.
        confidence: The adapter's confidence.
    """

    type: RelationshipType
    source_label: str
    target_label: str
    confidence: Confidence

    def __post_init__(self) -> None:
        if not self.source_label.strip() or not self.target_label.strip():
            raise InvalidExtractionError("CandidateRelationship labels must be non-empty.")


@dataclass(frozen=True, slots=True)
class RawExtraction:
    """The candidates extracted from one artifact.

    Attributes:
        artifact_id: The artifact the candidates came from.
        entities: Candidate entities.
        evidence: Candidate evidence.
        relationships: Candidate relationships (resolved by label downstream).
    """

    artifact_id: ArtifactId
    entities: tuple[CandidateEntity, ...] = ()
    evidence: tuple[CandidateEvidence, ...] = ()
    relationships: tuple[CandidateRelationship, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "entities", tuple(self.entities))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "relationships", tuple(self.relationships))

    @property
    def is_empty(self) -> bool:
        return not (self.entities or self.evidence or self.relationships)
