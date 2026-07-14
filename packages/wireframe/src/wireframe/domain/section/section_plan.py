"""The SectionPlan — the rich, executable unit of a wireframe plan.

A :class:`SectionPlan` is the heart of the engine: it carries everything the spec demands a
section define — identity, type, execution order, parent/children, priority, the four goals,
its blocks and required/optional components, its data/asset/interaction/responsive/
accessibility/SEO/performance requirements, its inputs/outputs, its dependencies, its
success/failure criteria, its review checklist, and its approval requirement. It describes
*what must be built, why, from what, in what order, and how it is judged* — and never how it
looks. Every visual decision belongs to a later phase; a SectionPlan holds no colour, font,
or coordinate.

Pure domain: standard library, the shared-kernel error base, wireframe ids, and the section/
block/component/approval value objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.errors import DesignDirectorError

from wireframe.domain.approval.approval import ApprovalRequirement
from wireframe.domain.block.block import Block
from wireframe.domain.component.component import ComponentRequirement
from wireframe.domain.section.criteria import (
    ChecklistItem,
    FailureCriterion,
    SectionIO,
    SuccessCriterion,
)
from wireframe.domain.section.goals import SectionGoals
from wireframe.domain.section.requirements import (
    AccessibilityRequirement,
    AssetRequirement,
    DataRequirement,
    InteractionRequirement,
    PerformanceConsideration,
    ResponsiveBehaviour,
    SEORequirement,
)
from wireframe.domain.shared.ids import SectionId, WFEvidenceId
from wireframe.domain.shared.value_objects import Priority, RequirementLevel, SectionType

__all__ = ["InvalidSectionPlanError", "SectionPlan"]


class InvalidSectionPlanError(DesignDirectorError):
    """Raised when a section plan is constructed with invalid data."""

    code = "invalid_wireframe_section_plan"
    http_status = 422


@dataclass(frozen=True, slots=True)
class SectionPlan:
    """One fully-specified section of a page's wireframe plan.

    Attributes:
        id: Section identity.
        type: The section's structural type.
        goals: The business/user/conversion/trust goals it serves.
        execution_order: Its position in the build sequence (assigned by the pipeline).
        is_required: Whether the page must carry the section.
        priority: Its priority relative to the page's other sections (5 = highest).
        parent: The parent section, if nested (``None`` for a top-level section).
        children: Nested child sections.
        blocks: The typed blocks it lays out.
        required_components: Components the section must have (all REQUIRED).
        optional_components: Components the section may have (all OPTIONAL).
        required_data: The data it needs supplied.
        required_assets: The assets it needs produced/sourced.
        interaction_requirements: The interaction behaviours it requires.
        responsive_behaviour: Its per-breakpoint behaviour intent.
        accessibility_requirements: The accessibility rules it must satisfy.
        seo_requirements: The SEO rules it must satisfy.
        performance_considerations: The performance rules it must honour.
        inputs: Data/assets/artifacts it consumes.
        outputs: Data/assets/artifacts it produces.
        dependencies: Sections that must be built before it.
        success_criteria: What makes the built section a success.
        failure_criteria: What makes the built section a failure.
        review_checklist: What a reviewer must verify.
        approval_requirement: The gate the section must pass, if any.
        evidence_ids: The evidence grounding the section.
    """

    id: SectionId
    type: SectionType
    goals: SectionGoals
    execution_order: int = 0
    is_required: bool = True
    priority: Priority = Priority(3)
    parent: SectionId | None = None
    children: tuple[SectionId, ...] = ()
    blocks: tuple[Block, ...] = ()
    required_components: tuple[ComponentRequirement, ...] = ()
    optional_components: tuple[ComponentRequirement, ...] = ()
    required_data: tuple[DataRequirement, ...] = ()
    required_assets: tuple[AssetRequirement, ...] = ()
    interaction_requirements: tuple[InteractionRequirement, ...] = ()
    responsive_behaviour: ResponsiveBehaviour = field(default_factory=ResponsiveBehaviour)
    accessibility_requirements: tuple[AccessibilityRequirement, ...] = ()
    seo_requirements: tuple[SEORequirement, ...] = ()
    performance_considerations: tuple[PerformanceConsideration, ...] = ()
    inputs: tuple[SectionIO, ...] = ()
    outputs: tuple[SectionIO, ...] = ()
    dependencies: tuple[SectionId, ...] = ()
    success_criteria: tuple[SuccessCriterion, ...] = ()
    failure_criteria: tuple[FailureCriterion, ...] = ()
    review_checklist: tuple[ChecklistItem, ...] = ()
    approval_requirement: ApprovalRequirement | None = None
    evidence_ids: tuple[WFEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.execution_order, int) or self.execution_order < 0:
            raise InvalidSectionPlanError(
                "SectionPlan.execution_order must be a non-negative int.",
                details={"execution_order": self.execution_order},
            )
        if self.parent == self.id:
            raise InvalidSectionPlanError(
                "SectionPlan cannot be its own parent.", details={"id": str(self.id)}
            )
        if self.id in self.dependencies:
            raise InvalidSectionPlanError(
                "SectionPlan cannot depend on itself.", details={"id": str(self.id)}
            )
        for comp in self.required_components:
            if comp.requirement is not RequirementLevel.REQUIRED:
                raise InvalidSectionPlanError(
                    "required_components must all be REQUIRED.",
                    details={"component": comp.component.value},
                )
        for comp in self.optional_components:
            if comp.requirement is not RequirementLevel.OPTIONAL:
                raise InvalidSectionPlanError(
                    "optional_components must all be OPTIONAL.",
                    details={"component": comp.component.value},
                )
        if self.approval_requirement is not None and self.approval_requirement.target != self.id:
            raise InvalidSectionPlanError(
                "approval_requirement.target must be this section.",
                details={"id": str(self.id)},
            )
        object.__setattr__(self, "children", tuple(self.children))
        object.__setattr__(self, "dependencies", tuple(dict.fromkeys(self.dependencies)))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    # -- queries ----------------------------------------------------------- #
    def required_blocks(self) -> tuple[Block, ...]:
        return tuple(b for b in self.blocks if b.is_required)

    def blocks_by_priority(self) -> tuple[Block, ...]:
        return tuple(sorted(self.blocks, key=lambda b: int(b.priority), reverse=True))

    def all_components(self) -> tuple[ComponentRequirement, ...]:
        return self.required_components + self.optional_components

    def all_evidence_ids(self) -> tuple[WFEvidenceId, ...]:
        ids: list[WFEvidenceId] = list(self.evidence_ids)
        ids.extend(self.goals.evidence_ids)
        for block in self.blocks:
            ids.extend(block.all_evidence_ids())
        for comp in self.all_components():
            ids.extend(comp.all_evidence_ids())
        if self.approval_requirement is not None:
            ids.extend(self.approval_requirement.all_evidence_ids())
        return tuple(ids)
