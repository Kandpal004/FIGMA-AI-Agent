"""WireframePlan — the aggregate the whole engine produces.

An immutable, versioned plan: the page/section blueprint, the approval plan, the six
planning graphs, and an overall quality picture. It is the single source of truth every
future Figma document derives from — and it holds no visual design whatsoever.

It enforces the platform's promises at construction:

1. **Provenance integrity** — every evidence id referenced by any page, section, block,
   component, approval requirement, or graph node must resolve in the plan's
   :class:`EvidenceGraph`. A plan that references something it cannot cite cannot be built —
   so an ungrounded planning decision is impossible by construction.
2. **Structural integrity** — every section's parent, children, dependencies, and approval
   dependencies resolve to sections/approvals that exist; every approval target resolves to
   a section; and every section's dependencies reference sections in the plan. (Cycle
   freedom of the dependency, execution, component, and approval graphs is enforced by the
   graph primitive.)

Versioning is lineage-based (``lineage_id`` + ``version``), consistent with Phases 3–11: an
IA or strategy change mints a new version under the same lineage, and history is retained.
Pure domain — it composes the other models and performs no I/O; ``created_at`` is supplied
by the caller.

Testing considerations
----------------------
* A plan whose any part references an evidence id absent from the evidence graph raises
  :class:`InvalidWireframePlanError`.
* A plan whose section dependencies or approval targets/dependencies dangle raises
  :class:`InvalidWireframePlanError`.
* Version ``< 1`` is rejected; convenience queries work.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from wireframe.domain.approval.approval import ApprovalPlan
from wireframe.domain.evidence.evidence import EvidenceGraph
from wireframe.domain.graph.graphs import WireframeGraphs
from wireframe.domain.plan.blueprint import PlanBlueprint
from wireframe.domain.quality.quality import WireframeQualityMetrics
from wireframe.domain.shared.ids import (
    ApprovalReqId,
    SectionId,
    WFEvidenceId,
    WireframePlanId,
    WireframePlanLineageId,
)

__all__ = ["InvalidWireframePlanError", "PlanThresholds", "WireframePlan"]


class InvalidWireframePlanError(DesignDirectorError):
    """Raised when a plan violates an integrity invariant (ungrounded or dangling)."""

    code = "invalid_wireframe_plan"
    http_status = 422


class PlanThresholds:
    """Named thresholds used by :attr:`WireframePlan.is_usable`."""

    MIN_OVERALL = 40.0


@dataclass(frozen=True, slots=True)
class WireframePlan:
    """The complete, provenance-tracked, versioned wireframe execution plan."""

    id: WireframePlanId
    lineage_id: WireframePlanLineageId
    version: int
    project_id: str
    blueprint: PlanBlueprint
    approval_plan: ApprovalPlan
    graphs: WireframeGraphs
    evidence_graph: EvidenceGraph
    quality: WireframeQualityMetrics
    created_at: datetime

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidWireframePlanError(
                "WireframePlan.version must be >= 1.", details={"version": self.version}
            )
        self._validate_provenance()
        self._validate_structure()

    # -- invariants -------------------------------------------------------- #
    def _referenced_evidence(self) -> set[WFEvidenceId]:
        referenced: set[WFEvidenceId] = set()
        referenced.update(self.blueprint.evidence_ids())
        referenced.update(self.approval_plan.evidence_ids())
        referenced.update(self.graphs.evidence_ids())
        return referenced

    def _validate_provenance(self) -> None:
        missing = self.evidence_graph.missing(self._referenced_evidence())
        if missing:
            raise InvalidWireframePlanError(
                "Plan references evidence absent from its evidence graph "
                "(no ungrounded planning decisions).",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def _validate_structure(self) -> None:
        section_ids = self.blueprint.section_ids()
        for section in self.blueprint.sections():
            if section.parent is not None and section.parent not in section_ids:
                raise InvalidWireframePlanError(
                    "Section parent references a section not in the plan.",
                    details={"section_id": str(section.id)},
                )
            dangling_children = [str(c) for c in section.children if c not in section_ids]
            if dangling_children:
                raise InvalidWireframePlanError(
                    "Section children reference sections not in the plan.",
                    details={"section_id": str(section.id), "children": dangling_children},
                )
            dangling_deps = [str(d) for d in section.dependencies if d not in section_ids]
            if dangling_deps:
                raise InvalidWireframePlanError(
                    "Section dependencies reference sections not in the plan.",
                    details={"section_id": str(section.id), "dependencies": dangling_deps},
                )
        self._validate_approvals(section_ids)

    def _validate_approvals(self, section_ids: frozenset[SectionId]) -> None:
        approval_ids: set[ApprovalReqId] = set(self.approval_plan.ids())
        for req in self.approval_plan:
            if req.target not in section_ids:
                raise InvalidWireframePlanError(
                    "Approval requirement targets a section not in the plan.",
                    details={"approval_id": str(req.id)},
                )
            dangling = [str(d) for d in req.depends_on if d not in approval_ids]
            if dangling:
                raise InvalidWireframePlanError(
                    "Approval requirement depends on approvals not in the plan.",
                    details={"approval_id": str(req.id), "depends_on": dangling},
                )

    # -- queries ----------------------------------------------------------- #
    def page_count(self) -> int:
        return len(self.blueprint)

    def section_count(self) -> int:
        return self.blueprint.section_count()

    def evidence_count(self) -> int:
        return len(self.evidence_graph)

    @property
    def is_usable(self) -> bool:
        """Whether the plan is complete enough to drive downstream Figma work.

        Requires a passing overall score, full grounding, at least one page, every required
        section carrying a required component, success criteria, and a review checklist, and
        non-empty evidence — the plan is the source of truth every Figma document derives
        from.
        """
        pages = self.blueprint.pages
        if not pages:
            return False
        for page in pages:
            required = page.required_sections()
            if not required:
                return False
            for section in required:
                if not section.required_components:
                    return False
                if not section.success_criteria:
                    return False
                if not section.review_checklist:
                    return False
        return (
            self.quality.overall_score.value >= PlanThresholds.MIN_OVERALL
            and self.quality.is_fully_grounded
            and self.evidence_count() > 0
        )
