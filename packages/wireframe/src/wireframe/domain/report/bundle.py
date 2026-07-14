"""The FigmaPlanBundle — the neutral hand-off a future Figma engine consumes.

The Wireframe Planning Engine is upstream-independent of design: it imports nothing from any
later phase. Instead it emits this neutral, self-contained bundle — the pages in execution
order with their ordered sections, blocks, components, requirements, criteria, and the
approval plan — carrying **zero visual properties** (no coordinates, sizes, colours, fonts,
or styles). A future Phase-13 Figma Design Engine will consume it through a port *it* owns,
translating plan into visual design; this engine never knows Figma exists.

Pure domain: standard library, the shared-kernel error base, and the plan models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from wireframe.domain.approval.approval import ApprovalPlan
from wireframe.domain.page.page_plan import PagePlan
from wireframe.domain.report.report import WireframePlan
from wireframe.domain.shared.ids import WireframePlanId

__all__ = ["FigmaPlanBundle"]


@dataclass(frozen=True, slots=True)
class FigmaPlanBundle:
    """The neutral wireframe plan a downstream Figma engine builds from.

    Attributes:
        plan_id: The plan version this bundle projects.
        project_id: The owning project.
        pages: The page plans, sections within each already in execution order.
        approval_plan: The sign-off gates that govern the build.
        is_usable: Whether the plan is complete enough to design from.
        created_at: When the plan was produced.
    """

    plan_id: WireframePlanId
    project_id: str
    pages: tuple[PagePlan, ...]
    approval_plan: ApprovalPlan
    is_usable: bool
    created_at: datetime

    @classmethod
    def from_plan(cls, plan: WireframePlan) -> FigmaPlanBundle:
        pages = tuple(
            PagePlan(
                id=page.id,
                page_type=page.page_type,
                purpose=page.purpose,
                sections=page.sections_in_execution_order(),
                evidence_ids=page.evidence_ids,
            )
            for page in plan.blueprint.pages
        )
        return cls(
            plan_id=plan.id,
            project_id=plan.project_id,
            pages=pages,
            approval_plan=plan.approval_plan,
            is_usable=plan.is_usable,
            created_at=plan.created_at,
        )
