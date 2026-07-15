"""The ExecutionPlanBundle — the neutral hand-off a future Figma phase consumes.

The Design Orchestrator is downstream-independent of rendering: it imports nothing from any later
phase and produces no UI and no Figma. Instead it emits this neutral, self-contained bundle — the
source refs, the ordered per-page sections (with their chosen component, variant, and token
bindings), the deterministic execution-step order, and the scheduled review gates — everything a
downstream Figma-generation / MCP phase needs to *materialise* the design, and nothing that
pre-empts how. A future Phase-18 Figma engine consumes it through a port *it* owns.

Pure domain: standard library and the plan models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from design_orchestrator.domain.context.context import SourceRefs
from design_orchestrator.domain.mapping.token_mapping import TokenMapping
from design_orchestrator.domain.mapping.variant_mapping import VariantMapping
from design_orchestrator.domain.plan.page import PagePlan
from design_orchestrator.domain.report.report import DesignExecutionPlan
from design_orchestrator.domain.review.review_plan import ReviewPlan
from design_orchestrator.domain.shared.ids import DesignExecutionPlanId

__all__ = ["ExecutionPlanBundle", "ExecutionStepRef"]


@dataclass(frozen=True, slots=True)
class ExecutionStepRef:
    """One step in the deterministic execution order, projected for a Figma driver.

    Attributes:
        node_id: The execution-graph node id (string).
        kind: The execution-step kind (e.g. "instantiate_component").
        label: A human-readable label.
    """

    node_id: str
    kind: str
    label: str


@dataclass(frozen=True, slots=True)
class ExecutionPlanBundle:
    """The neutral execution plan a downstream Figma phase builds from.

    Attributes:
        plan_id: The plan version this bundle projects.
        project_id: The owning project.
        source_refs: The upstream artifacts the plan was orchestrated from.
        pages: The ordered per-page section plans.
        token_mapping: The resolved token bindings per section.
        variant_mapping: The resolved variant choices per section.
        execution_order: The deterministic execution-step sequence.
        review_plan: The scheduled review gates (ending in pre-generation).
        is_production_ready: Whether the plan is settled.
        created_at: When the plan was produced.
    """

    plan_id: DesignExecutionPlanId
    project_id: str
    source_refs: SourceRefs
    pages: tuple[PagePlan, ...]
    token_mapping: TokenMapping
    variant_mapping: VariantMapping
    execution_order: tuple[ExecutionStepRef, ...]
    review_plan: ReviewPlan
    is_production_ready: bool
    created_at: datetime

    @classmethod
    def from_plan(cls, plan: DesignExecutionPlan) -> ExecutionPlanBundle:
        order = tuple(
            ExecutionStepRef(node_id=str(node.id), kind=node.kind.value, label=node.label)
            for node in plan.execution_order()
        )
        return cls(
            plan_id=plan.id,
            project_id=plan.project_id,
            source_refs=plan.source_refs,
            pages=plan.pages,
            token_mapping=plan.token_mapping,
            variant_mapping=plan.variant_mapping,
            execution_order=order,
            review_plan=plan.review_plan,
            is_production_ready=plan.is_production_ready,
            created_at=plan.created_at,
        )
