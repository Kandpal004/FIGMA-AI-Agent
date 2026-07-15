"""DesignExecutionPlan — the aggregate the whole engine produces.

An immutable, versioned plan: the ordered per-page section plans, the component tree, the layout
model, the resolved token and variant mappings, the execution and layout graphs, the review
plan, the evidence graph, and the quality picture. It is the authoritative, machine-executable
plan a future Figma-generation phase replays — it renders no UI and no Figma.

It enforces the platform's promises at construction:

1. **Provenance integrity** — every evidence id referenced by any section, tree node, graph node,
   or review checkpoint resolves in the plan's :class:`EvidenceGraph`. Nothing the orchestrator
   cannot cite enters the plan — no ordering or binding is chosen at random.
2. **Binding integrity** — the token and variant mappings key exactly onto the plan's sections;
   each section's resolved token binding equals its declared bindings and its variant choice
   matches its component and variant. A binding that dangles or drifts is rejected.
3. **Structure integrity** — the component tree is a valid rooted tree, both graphs are acyclic
   and resolve, and each page's sections form a total order (enforced by the respective models),
   and the tree's COMPONENT nodes cover exactly the plan's sections.
4. **Coverage** — the plan has at least one page, every section is realised by a tree node, and
   the review plan ends in the pre-generation gate (enforced by :class:`ReviewPlan`).

Versioning is lineage-based (``lineage_id`` + ``version``), consistent with Phases 3–16.

Pure domain — it composes the other models and performs no I/O; ``created_at`` is supplied by
the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from design_orchestrator.domain.context.context import SourceRefs
from design_orchestrator.domain.evidence.evidence import EvidenceGraph
from design_orchestrator.domain.graph.graphs import OrchestratorGraphs
from design_orchestrator.domain.layout.layout import LayoutModel
from design_orchestrator.domain.mapping.token_mapping import TokenMapping
from design_orchestrator.domain.mapping.variant_mapping import VariantMapping
from design_orchestrator.domain.plan.page import PagePlan
from design_orchestrator.domain.plan.section import SectionPlan
from design_orchestrator.domain.quality.quality import ExecutionPlanQualityMetrics
from design_orchestrator.domain.review.review_plan import ReviewPlan
from design_orchestrator.domain.shared.ids import (
    DesignExecutionPlanId,
    DesignExecutionPlanLineageId,
    DOEvidenceId,
    SectionPlanId,
)
from design_orchestrator.domain.shared.value_objects import PageType, TreeNodeKind
from design_orchestrator.domain.tree.component_tree import ComponentTree

__all__ = ["DesignExecutionPlan", "InvalidExecutionPlanError"]


class InvalidExecutionPlanError(DesignDirectorError):
    """Raised when an execution plan violates an integrity invariant."""

    code = "invalid_design_orchestrator_execution_plan"
    http_status = 422


@dataclass(frozen=True, slots=True)
class DesignExecutionPlan:
    """The complete, provenance-tracked, versioned design-execution plan."""

    id: DesignExecutionPlanId
    lineage_id: DesignExecutionPlanLineageId
    version: int
    project_id: str
    source_refs: SourceRefs
    pages: tuple[PagePlan, ...]
    component_tree: ComponentTree
    layout_model: LayoutModel
    token_mapping: TokenMapping
    variant_mapping: VariantMapping
    graphs: OrchestratorGraphs
    review_plan: ReviewPlan
    evidence_graph: EvidenceGraph
    quality: ExecutionPlanQualityMetrics
    created_at: datetime

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidExecutionPlanError(
                "DesignExecutionPlan.version must be >= 1.", details={"version": self.version}
            )
        object.__setattr__(self, "pages", tuple(self.pages))
        if not self.pages:
            raise InvalidExecutionPlanError("A DesignExecutionPlan must have at least one page.")
        self._validate_provenance()
        self._validate_binding_integrity()
        self._validate_coverage()

    # -- section index ----------------------------------------------------- #
    def _sections(self) -> tuple[SectionPlan, ...]:
        return tuple(s for page in self.pages for s in page.sections)

    def _section_index(self) -> dict[SectionPlanId, SectionPlan]:
        index: dict[SectionPlanId, SectionPlan] = {}
        for section in self._sections():
            if section.id in index:
                raise InvalidExecutionPlanError(
                    "A section id is used on more than one page.",
                    details={"section": str(section.id)},
                )
            index[section.id] = section
        return index

    # -- invariant 1: provenance ------------------------------------------- #
    def _referenced_evidence(self) -> set[DOEvidenceId]:
        referenced: set[DOEvidenceId] = set()
        for page in self.pages:
            referenced.update(page.evidence_ids)
        referenced.update(self.component_tree.evidence_ids())
        referenced.update(self.graphs.evidence_ids())
        referenced.update(self.review_plan.evidence_ids)
        return referenced

    def _validate_provenance(self) -> None:
        missing = self.evidence_graph.missing(self._referenced_evidence())
        if missing:
            raise InvalidExecutionPlanError(
                "Plan references evidence absent from its evidence graph "
                "(no ungrounded orchestration choices).",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    # -- invariant 2: binding integrity ------------------------------------ #
    def _validate_binding_integrity(self) -> None:
        index = self._section_index()
        section_ids = set(index)

        for section_id, _ in self.token_mapping:
            if section_id not in section_ids:
                raise InvalidExecutionPlanError(
                    "Token mapping references a section not in the plan.",
                    details={"section": str(section_id)},
                )
        for section_id, _ in self.variant_mapping:
            if section_id not in section_ids:
                raise InvalidExecutionPlanError(
                    "Variant mapping references a section not in the plan.",
                    details={"section": str(section_id)},
                )

        for section_id, section in index.items():
            bound = self.token_mapping.for_section(section_id)
            if set(bound) != set(section.token_bindings):
                raise InvalidExecutionPlanError(
                    "A section's resolved token mapping does not match its declared bindings.",
                    details={"section": str(section_id)},
                )
            choice = self.variant_mapping.for_section(section_id)
            if choice is None:
                raise InvalidExecutionPlanError(
                    "A section has no variant mapping entry.",
                    details={"section": str(section_id)},
                )
            if choice.component is not section.component:
                raise InvalidExecutionPlanError(
                    "A section's variant mapping targets a different component.",
                    details={"section": str(section_id)},
                )
            if choice.variant_name != section.variant_name:
                raise InvalidExecutionPlanError(
                    "A section's variant mapping names a different variant.",
                    details={"section": str(section_id)},
                )

    # -- invariant 3/4: structure + coverage ------------------------------- #
    def _validate_coverage(self) -> None:
        section_ids = set(self._section_index())
        covered = {
            n.section_ref
            for n in self.component_tree.by_kind(TreeNodeKind.COMPONENT)
            if n.section_ref is not None
        }
        if covered != section_ids:
            raise InvalidExecutionPlanError(
                "The component tree's COMPONENT nodes must cover exactly the plan's sections.",
                details={
                    "unmapped_sections": [str(s) for s in section_ids - covered],
                    "orphan_nodes": [str(s) for s in covered - section_ids],
                },
            )

    # -- queries ----------------------------------------------------------- #
    def page_types(self) -> tuple[PageType, ...]:
        return tuple(page.page_type for page in self.pages)

    def section_count(self) -> int:
        return sum(len(page) for page in self.pages)

    def page_count(self) -> int:
        return len(self.pages)

    def evidence_count(self) -> int:
        return len(self.evidence_graph)

    def execution_order(self) -> tuple:
        """The deterministic execution-step order (the P18 replay sequence)."""
        return self.graphs.execution.topological_order()

    @property
    def is_production_ready(self) -> bool:
        """Whether the plan is complete enough to hand to Figma generation.

        Requires pages and sections, full grounding and binding integrity, a scheduled review
        plan ending in pre-generation, and non-empty evidence — the structural invariants are
        already guaranteed at construction.
        """
        if not self.pages or self.section_count() == 0:
            return False
        return (
            self.quality.is_fully_grounded
            and self.quality.has_binding_integrity
            and len(self.review_plan) >= 1
            and self.evidence_count() > 0
        )
