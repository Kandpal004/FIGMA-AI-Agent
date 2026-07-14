"""The Research Result — the atomic unit of the engine's output.

A :class:`ResearchResult` carries every field the mission requires: source,
timestamp, confidence, evidence, entities, relationships, category, tags, version,
quality score, freshness, and completeness (the last four via
:class:`QualityMetrics`). It is produced per de-duplicated artifact and gathered
into a :class:`~research.domain.report.report.ResearchReport`.

Pure domain: standard library, the shared-kernel error base, research ids, and the
evidence/entity/relationship/quality/validation models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from core.errors import DesignDirectorError

from research.domain.entity.entity import Entity
from research.domain.entity.relationship import Relationship
from research.domain.evidence.evidence import Evidence
from research.domain.result.quality import QualityMetrics
from research.domain.shared.ids import ResearchResultId, ResearchSourceId
from research.domain.shared.value_objects import (
    Completeness,
    Confidence,
    Freshness,
    QualityScore,
    ResearchCategory,
    Tag,
)
from research.domain.validation.issue import ValidationIssue

__all__ = ["InvalidResultError", "ResearchResult"]


class InvalidResultError(DesignDirectorError):
    """Raised when a research result is constructed with invalid data."""

    code = "invalid_result"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ResearchResult:
    """One unit of researched evidence, carrying all required fields.

    Attributes:
        id: Result identity.
        source_id: The source it was derived from.
        timestamp: When the underlying artifact was collected.
        category: The research category.
        evidence: The evidence in this result.
        entities: The entities extracted.
        relationships: The relationships detected.
        tags: Free-form tags.
        version: The result version (``>= 1``).
        metrics: Quality, freshness, completeness, and confidence.
        issues: Validation issues retained for auditability.
    """

    id: ResearchResultId
    source_id: ResearchSourceId
    timestamp: datetime
    category: ResearchCategory
    metrics: QualityMetrics
    version: int = 1
    evidence: tuple[Evidence, ...] = ()
    entities: tuple[Entity, ...] = ()
    relationships: tuple[Relationship, ...] = ()
    tags: frozenset[Tag] = field(default_factory=frozenset)
    issues: tuple[ValidationIssue, ...] = ()

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidResultError("ResearchResult.version must be >= 1.")
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "entities", tuple(self.entities))
        object.__setattr__(self, "relationships", tuple(self.relationships))
        object.__setattr__(self, "tags", frozenset(self.tags))
        object.__setattr__(self, "issues", tuple(self.issues))

    # -- the required fields, exposed as first-class accessors ------------- #
    @property
    def confidence(self) -> Confidence:
        return self.metrics.confidence

    @property
    def quality_score(self) -> QualityScore:
        return self.metrics.quality_score

    @property
    def freshness(self) -> Freshness:
        return self.metrics.freshness

    @property
    def completeness(self) -> Completeness:
        return self.metrics.completeness

    def evidence_ids(self):
        return tuple(e.id for e in self.evidence)

    def entity_ids(self):
        return tuple(e.id for e in self.entities)
