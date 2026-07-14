"""ResearchReport — the aggregate the whole engine produces.

An immutable, versioned report: the research results, the unified evidence and
entity graphs, and an overall quality picture. It enforces the platform's provenance
promise at construction: **every evidence id referenced by any result, entity, or
relationship must resolve in the evidence graph, and every entity referenced must
resolve in the entity graph.** A report that references something it does not carry
cannot be built — so an unattributed finding or a dangling edge is impossible by
construction.

Versioning is lineage-based (``lineage_id`` + ``version``), consistent with Phases
3–5: re-research mints a new version under the same lineage, and history is retained.
Pure domain — it composes the other models and performs no I/O; ``created_at`` is
supplied by the caller.

Testing considerations
----------------------
* A report whose result/entity/relationship references an evidence id absent from
  the evidence graph — or an entity id absent from the entity graph — raises
  :class:`InvalidReportError`.
* Version ``< 1`` is rejected; convenience queries work.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from research.domain.entity.entity import Entity
from research.domain.entity.graph import EntityGraph
from research.domain.entity.relationship import Relationship
from research.domain.evidence.evidence import Evidence, EvidenceGraph
from research.domain.result.quality import QualityMetrics
from research.domain.result.result import ResearchResult
from research.domain.shared.ids import (
    EntityId,
    EvidenceId,
    ResearchReportId,
    ResearchReportLineageId,
    ResearchSourceId,
)
from research.domain.shared.value_objects import EntityType

__all__ = ["CompletenessThresholds", "InvalidReportError", "ResearchReport"]


class InvalidReportError(DesignDirectorError):
    """Raised when a report violates an integrity invariant (a dangling reference)."""

    code = "invalid_research_report"
    http_status = 422


class CompletenessThresholds:
    """Named thresholds used by :attr:`ResearchReport.is_usable`."""

    MIN_QUALITY = 40.0


@dataclass(frozen=True, slots=True)
class ResearchReport:
    """The complete, provenance-tracked, versioned research report."""

    id: ResearchReportId
    lineage_id: ResearchReportLineageId
    version: int
    project_id: str
    goal: str
    results: tuple[ResearchResult, ...]
    evidence_graph: EvidenceGraph
    entity_graph: EntityGraph
    quality: QualityMetrics
    created_at: datetime

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidReportError(
                "ResearchReport.version must be >= 1.", details={"version": self.version}
            )
        object.__setattr__(self, "results", tuple(self.results))
        self._validate_provenance()

    def _validate_provenance(self) -> None:
        referenced_evidence: set[EvidenceId] = set()
        referenced_entities: set[EntityId] = set()
        for result in self.results:
            for evidence in result.evidence:
                referenced_evidence.add(evidence.id)
            for entity in result.entities:
                referenced_entities.add(entity.id)
                referenced_evidence.update(entity.evidence_ids)
            for relationship in result.relationships:
                referenced_entities.add(relationship.source)
                referenced_entities.add(relationship.target)
                referenced_evidence.update(relationship.evidence_ids)

        missing_evidence = [e for e in referenced_evidence if not self.evidence_graph.has(e)]
        if missing_evidence:
            raise InvalidReportError(
                "Report references evidence absent from its evidence graph "
                "(no unattributed findings).",
                details={"missing_evidence": [str(e) for e in missing_evidence]},
            )
        missing_entities = [e for e in referenced_entities if not self.entity_graph.has(e)]
        if missing_entities:
            raise InvalidReportError(
                "Report references entities absent from its entity graph "
                "(no dangling edges).",
                details={"missing_entities": [str(e) for e in missing_entities]},
            )

    # -- queries ----------------------------------------------------------- #
    def __len__(self) -> int:
        return len(self.results)

    def all_evidence(self) -> tuple[Evidence, ...]:
        return tuple(self.evidence_graph)

    def all_entities(self) -> tuple[Entity, ...]:
        return tuple(self.entity_graph)

    def all_relationships(self) -> tuple[Relationship, ...]:
        return self.entity_graph.relationships

    def entities_by_type(self, entity_type: EntityType) -> tuple[Entity, ...]:
        return self.entity_graph.by_type(entity_type)

    def sources(self) -> tuple[ResearchSourceId, ...]:
        seen: list[ResearchSourceId] = []
        for result in self.results:
            if result.source_id not in seen:
                seen.append(result.source_id)
        return tuple(seen)

    def evidence_count(self) -> int:
        return len(self.evidence_graph)

    def entity_count(self) -> int:
        return len(self.entity_graph)

    @property
    def is_usable(self) -> bool:
        """Whether the report is good enough to feed downstream reasoning."""
        return (
            self.quality.quality_score.value >= CompletenessThresholds.MIN_QUALITY
            and self.evidence_count() > 0
        )
