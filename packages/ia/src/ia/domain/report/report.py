"""IAReport — the aggregate the whole engine produces.

An immutable, versioned report: the site map, the navigation, the page relationships, the
product-discovery strategy, the six IA graphs, and an overall quality picture.

It enforces the platform's promises at construction:

1. **Provenance integrity** — every evidence id referenced by any page, section, nav item,
   relationship, discovery strategy, or graph node must resolve in the report's
   :class:`EvidenceGraph`. An IA that references something it cannot cite cannot be built —
   so an ungrounded structural decision is impossible by construction.
2. **Structural integrity** — every navigation target and every page relationship endpoint
   references a page type that exists in the site map. No navigation may lead to a page the
   architecture does not define; no relationship may dangle.
   (Graph and content-tree acyclicity are enforced by the graph primitive.)

Versioning is lineage-based (``lineage_id`` + ``version``), consistent with Phases 3–10: a
catalog or strategy change mints a new version under the same lineage, and history is
retained. Pure domain — it composes the other models and performs no I/O; ``created_at`` is
supplied by the caller.

Testing considerations
----------------------
* A report whose any part references an evidence id absent from the evidence graph raises
  :class:`InvalidIAReportError`.
* A report whose navigation targets or relationships reference a page absent from the site
  map raises :class:`InvalidIAReportError`.
* Version ``< 1`` is rejected; convenience queries work.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from ia.domain.discovery.discovery import Discovery
from ia.domain.evidence.evidence import EvidenceGraph
from ia.domain.graph.graphs import IAGraphs
from ia.domain.navigation.navigation import Navigation
from ia.domain.quality.quality import IAQualityMetrics
from ia.domain.relationship.relationship import RelationshipSet
from ia.domain.shared.ids import IAEvidenceId, IAReportId, IAReportLineageId
from ia.domain.sitemap.sitemap import SiteMap

__all__ = ["IAReport", "InvalidIAReportError", "ReportThresholds"]


class InvalidIAReportError(DesignDirectorError):
    """Raised when a report violates an integrity invariant (ungrounded or dangling)."""

    code = "invalid_ia_report"
    http_status = 422


class ReportThresholds:
    """Named thresholds used by :attr:`IAReport.is_usable`."""

    MIN_OVERALL = 40.0


@dataclass(frozen=True, slots=True)
class IAReport:
    """The complete, provenance-tracked, versioned information architecture report."""

    id: IAReportId
    lineage_id: IAReportLineageId
    version: int
    project_id: str
    sitemap: SiteMap
    navigation: Navigation
    relationships: RelationshipSet
    discovery: Discovery
    graphs: IAGraphs
    evidence_graph: EvidenceGraph
    quality: IAQualityMetrics
    created_at: datetime

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidIAReportError(
                "IAReport.version must be >= 1.", details={"version": self.version}
            )
        self._validate_provenance()
        self._validate_structure()

    # -- invariants -------------------------------------------------------- #
    def _referenced_evidence(self) -> set[IAEvidenceId]:
        referenced: set[IAEvidenceId] = set()
        referenced.update(self.sitemap.evidence_ids())
        referenced.update(self.navigation.evidence_ids())
        referenced.update(self.relationships.evidence_ids())
        referenced.update(self.discovery.evidence_ids())
        referenced.update(self.graphs.evidence_ids())
        return referenced

    def _validate_provenance(self) -> None:
        missing = self.evidence_graph.missing(self._referenced_evidence())
        if missing:
            raise InvalidIAReportError(
                "Report references evidence absent from its evidence graph "
                "(no ungrounded IA decisions).",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def _validate_structure(self) -> None:
        page_types = self.sitemap.page_types()
        dangling_nav = [t.value for t in self.navigation.targets() if t not in page_types]
        if dangling_nav:
            raise InvalidIAReportError(
                "Navigation targets a page not in the site map.",
                details={"missing_pages": dangling_nav},
            )
        dangling_rel = [
            r.kind.value
            for r in self.relationships
            if r.source not in page_types or r.target not in page_types
        ]
        if dangling_rel:
            raise InvalidIAReportError(
                "A page relationship references a page not in the site map.",
                details={"relationships": dangling_rel},
            )

    # -- queries ----------------------------------------------------------- #
    def page_count(self) -> int:
        return len(self.sitemap)

    def required_page_count(self) -> int:
        return len(self.sitemap.required())

    def evidence_count(self) -> int:
        return len(self.evidence_graph)

    @property
    def is_usable(self) -> bool:
        """Whether the IA is complete enough to drive downstream wireframing.

        Requires a passing overall score, full grounding, at least one required page,
        every required page carrying at least one required section, and non-empty
        evidence — the IA is the source of truth every page structure derives from.
        """
        required = self.sitemap.required()
        every_required_has_section = bool(required) and all(
            p.required_sections for p in required
        )
        return (
            self.quality.overall_score.value >= ReportThresholds.MIN_OVERALL
            and self.quality.is_fully_grounded
            and every_required_has_section
            and self.evidence_count() > 0
        )
