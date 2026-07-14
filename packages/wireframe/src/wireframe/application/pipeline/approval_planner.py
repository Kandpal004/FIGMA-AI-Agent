"""Stage — Approval Planning.

The planner proposes a per-section approval requirement (its gate, approver, and criteria);
this stage wires those requirements into an approval *plan*. A section's approval depends on
the approvals of the sections it is built on — you cannot sign off a section before what it
depends on is signed off — so the approval dependencies mirror the section dependencies. The
result is the Approval Plan (and, downstream, the Approval Graph), kept acyclic by the same
dependency structure the ordering resolver already proved acyclic.

The section-embedded approval requirement and the plan-level requirement are the *same*
object after this stage, so the two never drift.
"""

from __future__ import annotations

from dataclasses import replace

from wireframe.domain.approval.approval import ApprovalPlan, ApprovalRequirement
from wireframe.domain.plan.blueprint import PlanBlueprint
from wireframe.domain.shared.ids import ApprovalReqId, SectionId

__all__ = ["ApprovalPlanner"]


class ApprovalPlanner:
    """Wires per-section approval requirements into a dependency-aware approval plan."""

    def plan(self, blueprint: PlanBlueprint) -> tuple[PlanBlueprint, ApprovalPlan]:
        sections = blueprint.sections()
        req_by_section: dict[SectionId, ApprovalReqId] = {
            s.id: s.approval_requirement.id
            for s in sections
            if s.approval_requirement is not None
        }

        wired: dict[SectionId, ApprovalRequirement] = {}
        for section in sections:
            req = section.approval_requirement
            if req is None:
                continue
            depends_on = tuple(
                req_by_section[d]
                for d in section.dependencies
                if d in req_by_section
            )
            wired[section.id] = replace(req, depends_on=depends_on)

        ordered_pages = tuple(
            replace(
                page,
                sections=tuple(
                    replace(section, approval_requirement=wired.get(section.id))
                    if section.approval_requirement is not None
                    else section
                    for section in page.sections
                ),
            )
            for page in blueprint.pages
        )
        new_blueprint = PlanBlueprint.of(ordered_pages)
        approval_plan = ApprovalPlan.of(wired.values())
        return new_blueprint, approval_plan
