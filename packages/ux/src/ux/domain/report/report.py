"""UXStrategyReport — the aggregate the whole engine produces.

An immutable, versioned report: the goals and mental model, the page strategies, the
journey map, the flows, the six UX strategies, the friction and drop-off analyses, the UX
law lens, the five UX graphs, and an overall quality picture.

It enforces the platform's anti-hallucination promise at construction:

**Provenance integrity** — every evidence id referenced by any goal, page strategy,
journey stage, flow step, strategy, analysis, law application, or graph node must resolve
in the report's :class:`EvidenceGraph`. A strategy that references something it cannot
cite cannot be built — so an ungrounded UX decision is impossible by construction. (Graph
and flow acyclicity are enforced by their own value objects.)

Versioning is lineage-based (``lineage_id`` + ``version``), consistent with Phases 3–9:
new evidence mints a new version under the same lineage, and history is retained. Pure
domain — it composes the other models and performs no I/O; ``created_at`` is supplied by
the caller.

Testing considerations
----------------------
* A report whose any part references an evidence id absent from the evidence graph raises
  :class:`InvalidUXReportError`.
* Version ``< 1`` is rejected; convenience queries work.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from ux.domain.analysis.dropoff import DropoffAnalysis
from ux.domain.analysis.friction import FrictionAnalysis
from ux.domain.evidence.evidence import EvidenceGraph
from ux.domain.flow.flow import FlowSet
from ux.domain.goals.goal import GoalSet
from ux.domain.goals.mental_model import MentalModel
from ux.domain.graph.graphs import UXGraphs
from ux.domain.journey.journeys import JourneyMap
from ux.domain.laws.lens import UXLawLens
from ux.domain.page.page_strategy import PageStrategySet
from ux.domain.quality.quality import UXQualityMetrics
from ux.domain.shared.ids import (
    UXEvidenceId,
    UXReportId,
    UXReportLineageId,
)
from ux.domain.strategy.strategies import UXStrategies

__all__ = ["InvalidUXReportError", "ReportThresholds", "UXStrategyReport"]


class InvalidUXReportError(DesignDirectorError):
    """Raised when a report violates an integrity invariant (ungrounded or dangling)."""

    code = "invalid_ux_report"
    http_status = 422


class ReportThresholds:
    """Named thresholds used by :attr:`UXStrategyReport.is_usable`."""

    MIN_OVERALL = 40.0


@dataclass(frozen=True, slots=True)
class UXStrategyReport:
    """The complete, provenance-tracked, versioned UX strategy report."""

    id: UXReportId
    lineage_id: UXReportLineageId
    version: int
    project_id: str
    goals: GoalSet
    mental_model: MentalModel
    pages: PageStrategySet
    journeys: JourneyMap
    flows: FlowSet
    strategies: UXStrategies
    friction: FrictionAnalysis
    dropoff: DropoffAnalysis
    laws: UXLawLens
    graphs: UXGraphs
    evidence_graph: EvidenceGraph
    quality: UXQualityMetrics
    created_at: datetime

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidUXReportError(
                "UXStrategyReport.version must be >= 1.", details={"version": self.version}
            )
        self._validate_provenance()

    # -- invariants -------------------------------------------------------- #
    def _referenced_evidence(self) -> set[UXEvidenceId]:
        referenced: set[UXEvidenceId] = set()
        referenced.update(self.goals.evidence_ids())
        referenced.update(self.mental_model.evidence_ids)
        referenced.update(self.pages.evidence_ids())
        referenced.update(self.journeys.evidence_ids())
        referenced.update(self.flows.evidence_ids())
        referenced.update(self.strategies.evidence_ids())
        referenced.update(self.friction.evidence_ids())
        referenced.update(self.dropoff.evidence_ids())
        referenced.update(self.laws.evidence_ids())
        referenced.update(self.graphs.evidence_ids())
        return referenced

    def _validate_provenance(self) -> None:
        missing = self.evidence_graph.missing(self._referenced_evidence())
        if missing:
            raise InvalidUXReportError(
                "Report references evidence absent from its evidence graph "
                "(no ungrounded UX decisions).",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    # -- queries ----------------------------------------------------------- #
    def page_count(self) -> int:
        return len(self.pages)

    def evidence_count(self) -> int:
        return len(self.evidence_graph)

    @property
    def is_usable(self) -> bool:
        """Whether the UX strategy is complete enough to drive downstream design.

        Requires a passing overall score, full grounding, at least one page strategy, a
        primary user goal, and non-empty evidence — the strategy is the source of truth
        every screen derives from, so it must be fully cited and anchored.
        """
        return (
            self.quality.overall_score.value >= ReportThresholds.MIN_OVERALL
            and self.quality.is_fully_grounded
            and self.page_count() > 0
            and self.goals.primary_user_goal is not None
            and self.evidence_count() > 0
        )
