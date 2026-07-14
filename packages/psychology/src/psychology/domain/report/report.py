"""CustomerPsychologyReport — the aggregate the whole engine produces.

An immutable, versioned report: the psychological profile, the personas (customer +
buying), the jobs-to-be-done, the buying and decision journeys, the nine psychology
matrices, the behavioral-framework lens, the six psychology graphs, and an overall
quality picture.

It enforces the platform's anti-hallucination promise at construction:

**Provenance integrity** — every evidence id referenced by any determination, persona,
job, journey stage, matrix cell, framework application, or graph node must resolve in the
report's :class:`EvidenceGraph`. A model that references something it cannot cite cannot
be built — so an ungrounded psychological claim is impossible by construction.
(Graph acyclicity is enforced by each :class:`PsychGraph`.)

Versioning is lineage-based (``lineage_id`` + ``version``), consistent with Phases 3–8:
new evidence mints a new version under the same lineage, and history is retained. Pure
domain — it composes the other models and performs no I/O; ``created_at`` is supplied by
the caller.

Testing considerations
----------------------
* A report whose any part references an evidence id absent from the evidence graph
  raises :class:`InvalidPsychologyReportError`.
* Version ``< 1`` is rejected; convenience queries work.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from psychology.domain.evidence.evidence import EvidenceGraph
from psychology.domain.frameworks.lens import FrameworkLens
from psychology.domain.graph.graphs import PsychologyGraphs
from psychology.domain.journey.buying_journey import BuyingJourney
from psychology.domain.journey.decision_journey import DecisionJourney
from psychology.domain.matrices.matrices import PsychologyMatrices
from psychology.domain.persona.buying_persona import BuyingPersonaSet
from psychology.domain.persona.jtbd import JTBDSet
from psychology.domain.persona.persona import PersonaSet
from psychology.domain.quality.quality import PsychologyQualityMetrics
from psychology.domain.shared.ids import (
    PsychologyEvidenceId,
    PsychologyReportId,
    PsychologyReportLineageId,
)
from psychology.domain.shared.value_objects import AwarenessLevel, SophisticationLevel
from psychology.domain.state.profile import PsychologicalProfile

__all__ = [
    "CustomerPsychologyReport",
    "InvalidPsychologyReportError",
    "ReportThresholds",
]


class InvalidPsychologyReportError(DesignDirectorError):
    """Raised when a report violates an integrity invariant (ungrounded or dangling)."""

    code = "invalid_psychology_report"
    http_status = 422


class ReportThresholds:
    """Named thresholds used by :attr:`CustomerPsychologyReport.is_usable`."""

    MIN_OVERALL = 40.0


@dataclass(frozen=True, slots=True)
class CustomerPsychologyReport:
    """The complete, provenance-tracked, versioned customer psychology report."""

    id: PsychologyReportId
    lineage_id: PsychologyReportLineageId
    version: int
    project_id: str
    profile: PsychologicalProfile
    personas: PersonaSet
    buying_personas: BuyingPersonaSet
    jobs: JTBDSet
    buying_journey: BuyingJourney
    decision_journey: DecisionJourney
    matrices: PsychologyMatrices
    frameworks: FrameworkLens
    graphs: PsychologyGraphs
    evidence_graph: EvidenceGraph
    quality: PsychologyQualityMetrics
    created_at: datetime

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidPsychologyReportError(
                "CustomerPsychologyReport.version must be >= 1.",
                details={"version": self.version},
            )
        self._validate_provenance()

    # -- invariants -------------------------------------------------------- #
    def _referenced_evidence(self) -> set[PsychologyEvidenceId]:
        referenced: set[PsychologyEvidenceId] = set()
        referenced.update(self.profile.evidence_ids())
        referenced.update(self.personas.evidence_ids())
        referenced.update(self.buying_personas.evidence_ids())
        referenced.update(self.jobs.evidence_ids())
        referenced.update(self.buying_journey.evidence_ids())
        referenced.update(self.decision_journey.evidence_ids())
        referenced.update(self.matrices.evidence_ids())
        referenced.update(self.frameworks.evidence_ids())
        referenced.update(self.graphs.evidence_ids())
        return referenced

    def _validate_provenance(self) -> None:
        missing = self.evidence_graph.missing(self._referenced_evidence())
        if missing:
            raise InvalidPsychologyReportError(
                "Report references evidence absent from its evidence graph "
                "(no ungrounded psychological claims).",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    # -- queries ----------------------------------------------------------- #
    @property
    def awareness(self) -> AwarenessLevel:
        return self.profile.awareness

    @property
    def sophistication(self) -> SophisticationLevel:
        return self.profile.sophistication

    def matrix_count(self) -> int:
        return self.matrices.count()

    def evidence_count(self) -> int:
        return len(self.evidence_graph)

    @property
    def is_usable(self) -> bool:
        """Whether the psychology model is complete enough to drive downstream UX/CRO.

        Requires a passing overall score, full grounding, and non-empty evidence — the
        model is the foundation every UX and CRO decision derives from, so it must be
        fully cited.
        """
        return (
            self.quality.overall_score.value >= ReportThresholds.MIN_OVERALL
            and self.quality.is_fully_grounded
            and self.evidence_count() > 0
        )
