"""BrandStrategyReport — the aggregate the whole engine produces.

An immutable, versioned report: the classification, the brand identity, the brand
character, the emotional strategy, the visual direction, the verbal system, the brand
decision graph, the governance rule system, and an overall quality picture.

It enforces the platform's anti-hallucination promise at construction:

1. **Provenance integrity** — every evidence id referenced by any element, decision,
   graph edge, or governance rule must resolve in the report's :class:`EvidenceGraph`. A
   brand that references something it cannot cite cannot be built — so an ungrounded
   brand decision is impossible by construction.
2. **Decision reference integrity** — the decision graph's ``DERIVES_FROM`` acyclicity
   is enforced by the graph; the report re-checks nothing it does not own.

Versioning is lineage-based (``lineage_id`` + ``version``), consistent with Phases 3–7:
a brand refresh mints a new version under the same lineage, and history is retained.
Pure domain — it composes the other models and performs no I/O; ``created_at`` is
supplied by the caller.

Testing considerations
----------------------
* A report whose any part references an evidence id absent from the evidence graph
  raises :class:`InvalidBrandReportError`.
* Version ``< 1`` is rejected; convenience queries work.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from brand.domain.classification.classification import BrandClassification
from brand.domain.decision.decision_graph import BrandDecisionGraph
from brand.domain.emotional.emotional_strategy import EmotionalStrategy
from brand.domain.evidence.evidence import EvidenceGraph
from brand.domain.governance.governance_model import BrandGovernance
from brand.domain.identity.identity import BrandIdentity
from brand.domain.personality.character import BrandCharacter
from brand.domain.quality.quality import BrandQualityMetrics
from brand.domain.shared.ids import (
    BrandEvidenceId,
    BrandReportId,
    BrandReportLineageId,
)
from brand.domain.shared.value_objects import BrandArchetype, BrandCategory
from brand.domain.verbal.verbal_system import BrandVerbalSystem
from brand.domain.visual.visual_direction import BrandVisualDirection

__all__ = ["BrandStrategyReport", "InvalidBrandReportError", "ReportThresholds"]


class InvalidBrandReportError(DesignDirectorError):
    """Raised when a report violates an integrity invariant (ungrounded or dangling)."""

    code = "invalid_brand_report"
    http_status = 422


class ReportThresholds:
    """Named thresholds used by :attr:`BrandStrategyReport.is_usable`."""

    MIN_OVERALL = 40.0


@dataclass(frozen=True, slots=True)
class BrandStrategyReport:
    """The complete, provenance-tracked, versioned brand strategy report."""

    id: BrandReportId
    lineage_id: BrandReportLineageId
    version: int
    project_id: str
    classification: BrandClassification
    identity: BrandIdentity
    character: BrandCharacter
    emotional: EmotionalStrategy
    visual: BrandVisualDirection
    verbal: BrandVerbalSystem
    decision_graph: BrandDecisionGraph
    governance: BrandGovernance
    evidence_graph: EvidenceGraph
    quality: BrandQualityMetrics
    created_at: datetime

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidBrandReportError(
                "BrandStrategyReport.version must be >= 1.",
                details={"version": self.version},
            )
        self._validate_provenance()

    # -- invariants -------------------------------------------------------- #
    def _referenced_evidence(self) -> set[BrandEvidenceId]:
        referenced: set[BrandEvidenceId] = set()
        referenced.update(self.classification.evidence_ids)
        referenced.update(self.identity.evidence_ids())
        referenced.update(self.character.evidence_ids())
        referenced.update(self.emotional.evidence_ids())
        referenced.update(self.visual.evidence_ids())
        referenced.update(self.verbal.evidence_ids())
        for decision in self.decision_graph:
            referenced.update(decision.evidence_ids)
        for edge in self.decision_graph.edges:
            referenced.update(edge.evidence_ids)
        referenced.update(self.governance.evidence_ids())
        return referenced

    def _validate_provenance(self) -> None:
        missing = self.evidence_graph.missing(self._referenced_evidence())
        if missing:
            raise InvalidBrandReportError(
                "Report references evidence absent from its evidence graph "
                "(no ungrounded brand decisions).",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    # -- queries ----------------------------------------------------------- #
    @property
    def primary_category(self) -> BrandCategory:
        return self.classification.primary

    @property
    def archetype(self) -> BrandArchetype:
        return self.character.archetype.primary

    def decision_count(self) -> int:
        return len(self.decision_graph)

    def evidence_count(self) -> int:
        return len(self.evidence_graph)

    @property
    def is_usable(self) -> bool:
        """Whether the brand is complete enough to drive downstream design.

        Requires a passing overall score, full grounding, and non-empty evidence — the
        brand is the constitution every design decision derives from, so it must be
        fully cited.
        """
        return (
            self.quality.overall_score.value >= ReportThresholds.MIN_OVERALL
            and self.quality.is_fully_grounded
            and self.evidence_count() > 0
        )
