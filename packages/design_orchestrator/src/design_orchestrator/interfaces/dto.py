"""Serializable view DTOs — the plan projected for transport.

The facade never returns domain aggregates; it returns these flat, immutable views. They project
a :class:`DesignExecutionPlan` (and the neutral :class:`ExecutionPlanBundle`) into plain
``dict``-friendly structures an API, the orchestration layer, or a future Figma/MCP engine can
serialize — carrying the ordered per-page sections (with their component/variant/token bindings
and directives), the component tree, the layout model, the token and variant mappings, the two
graphs, and the review plan, but no domain objects and no UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from design_orchestrator.domain.graph.do_graph import DOGraph
from design_orchestrator.domain.plan.page import PagePlan
from design_orchestrator.domain.plan.section import SectionPlan
from design_orchestrator.domain.report.bundle import ExecutionPlanBundle
from design_orchestrator.domain.report.report import DesignExecutionPlan

__all__ = [
    "ExecutionPlanBundleView",
    "GraphView",
    "PageView",
    "QualityView",
    "ExecutionPlanView",
    "TraceView",
]


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _ids(ids) -> list[str]:
    return [str(i) for i in ids]


def _section_view(s: SectionPlan) -> dict:
    return {
        "id": str(s.id),
        "page_type": s.page_type.value,
        "order": int(s.order),
        "role": s.role.value,
        "component": s.component.value,
        "variant_name": s.variant_name,
        "layout": {
            "mode": s.layout.mode.value,
            "alignment": s.layout.alignment.value,
            "density": s.layout.density.value,
            "columns": s.layout.columns,
        },
        "spacing": {"gap_token": s.spacing.gap_token, "block_token": s.spacing.block_token},
        "typography": {
            "heading_token": s.typography.heading_token,
            "body_token": s.typography.body_token,
        },
        "visual": {
            "theme_mode": s.visual.theme_mode.value,
            "surface_tokens": list(s.visual.surface_tokens),
            "emphasis": s.visual.emphasis,
        },
        "token_bindings": list(s.token_bindings),
        "responsive": {bp.value: note for bp, note in s.responsive.behavior.items()},
        "animation": {
            "duration_token": s.animation.duration_token,
            "easing_token": s.animation.easing_token,
            "trigger": s.animation.trigger,
        },
        "accessibility": {
            "role": s.accessibility.role,
            "min_contrast": s.accessibility.min_contrast,
            "keyboard": list(s.accessibility.keyboard),
            "focus_visible": s.accessibility.focus_visible,
        },
        "performance": {
            "lazy_load": s.performance.lazy_load,
            "priority": s.performance.priority,
            "blocks_lcp": s.performance.blocks_lcp,
        },
        "considered_alternative": (
            {
                "option": s.considered_alternative.option,
                "reason_rejected": s.considered_alternative.reason_rejected,
            }
            if s.considered_alternative
            else None
        ),
        "evidence_ids": _ids(s.evidence_ids),
    }


def _page_view(p: PagePlan) -> dict:
    return {
        "id": str(p.id),
        "page_type": p.page_type.value,
        "region_id": str(p.region_id),
        "sections": [_section_view(s) for s in p.sections],
    }


def _tree_view(plan: DesignExecutionPlan) -> list[dict]:
    return [
        {
            "id": str(n.id),
            "kind": n.kind.value,
            "label": n.label,
            "parent_id": str(n.parent_id) if n.parent_id is not None else None,
            "order": n.order,
            "section_ref": str(n.section_ref) if n.section_ref is not None else None,
        }
        for n in plan.component_tree
    ]


def _layout_view(plan: DesignExecutionPlan) -> dict:
    lm = plan.layout_model
    return {
        "regions": [
            {
                "id": str(r.id),
                "kind": r.kind.value,
                "page_type": r.page_type.value,
                "parent_id": str(r.parent_id) if r.parent_id is not None else None,
                "label": r.label,
            }
            for r in lm.regions.values()
        ],
        "placements": [
            {
                "region_id": str(p.region_id),
                "breakpoint": p.breakpoint.value,
                "column_start": p.column_start,
                "column_span": p.column_span,
                "order": p.order,
            }
            for p in lm.placements
        ],
    }


def _graph_view(g: DOGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [
            {"id": str(n.id), "kind": n.kind.value, "label": n.label,
             "evidence_ids": _ids(n.evidence_ids)}
            for n in g
        ],
        "edges": [
            {"id": str(e.id), "source": str(e.source), "target": str(e.target),
             "relation": e.relation.value}
            for e in g.edges
        ],
    }


def _token_mapping_view(plan: DesignExecutionPlan) -> dict:
    return {str(sid): list(keys) for sid, keys in plan.token_mapping}


def _variant_mapping_view(plan: DesignExecutionPlan) -> dict:
    return {
        str(sid): {"component": choice.component.value, "variant_name": choice.variant_name}
        for sid, choice in plan.variant_mapping
    }


def _review_view(plan: DesignExecutionPlan) -> list[dict]:
    return [
        {
            "id": str(c.id),
            "gate": c.gate.value,
            "after_step": c.after_step.value,
            "statement": c.statement,
            "pass_criteria": list(c.pass_criteria),
            "status": c.status.value,
            "evidence_ids": _ids(c.evidence_ids),
        }
        for c in plan.review_plan
    ]


def _source_refs_view(plan: DesignExecutionPlan) -> dict:
    sr = plan.source_refs
    return {
        "design_system_spec_id": sr.design_system_spec_id,
        "component_spec_id": sr.component_spec_id,
        "design_language_spec_id": sr.design_language_spec_id,
        "creative_director_review_id": sr.creative_director_review_id,
        "wireframe_plan_id": sr.wireframe_plan_id,
        "ia_report_id": sr.ia_report_id,
    }


@dataclass(frozen=True, slots=True)
class QualityView:
    overall_score: float
    band: str
    coverage: float
    binding_integrity: float
    sequencing: float
    grounding: float
    confidence: float
    is_fully_grounded: bool


@dataclass(frozen=True, slots=True)
class PageView:
    page: dict


@dataclass(frozen=True, slots=True)
class GraphView:
    graph: dict


@dataclass(frozen=True, slots=True)
class ExecutionPlanView:
    """The full, flat projection of a design-execution plan."""

    plan_id: str
    lineage_id: str
    version: int
    project_id: str
    is_production_ready: bool
    created_at: str
    source_refs: dict
    quality: QualityView
    pages: list[dict]
    component_tree: list[dict]
    layout: dict
    token_mapping: dict
    variant_mapping: dict
    graphs: dict
    execution_order: list[dict]
    review_plan: list[dict]
    page_count: int
    section_count: int
    evidence_count: int

    @classmethod
    def from_plan(cls, plan: DesignExecutionPlan) -> ExecutionPlanView:
        quality = QualityView(
            overall_score=plan.quality.overall_score.value,
            band=plan.quality.band.value,
            coverage=plan.quality.coverage.value,
            binding_integrity=plan.quality.binding_integrity.value,
            sequencing=plan.quality.sequencing.value,
            grounding=plan.quality.grounding.value,
            confidence=plan.quality.confidence.value,
            is_fully_grounded=plan.quality.is_fully_grounded,
        )
        return cls(
            plan_id=str(plan.id),
            lineage_id=str(plan.lineage_id),
            version=plan.version,
            project_id=plan.project_id,
            is_production_ready=plan.is_production_ready,
            created_at=_iso(plan.created_at),
            source_refs=_source_refs_view(plan),
            quality=quality,
            pages=[_page_view(p) for p in plan.pages],
            component_tree=_tree_view(plan),
            layout=_layout_view(plan),
            token_mapping=_token_mapping_view(plan),
            variant_mapping=_variant_mapping_view(plan),
            graphs={g.kind.value: _graph_view(g) for g in plan.graphs.all},
            execution_order=[
                {"id": str(n.id), "kind": n.kind.value, "label": n.label}
                for n in plan.execution_order()
            ],
            review_plan=_review_view(plan),
            page_count=plan.page_count(),
            section_count=plan.section_count(),
            evidence_count=plan.evidence_count(),
        )


@dataclass(frozen=True, slots=True)
class ExecutionPlanBundleView:
    """The neutral execution plan a downstream Figma phase consumes."""

    plan_id: str
    project_id: str
    is_production_ready: bool
    created_at: str
    source_refs: dict
    pages: list[dict]
    token_mapping: dict
    variant_mapping: dict
    execution_order: list[dict]
    review_plan: list[dict]

    @classmethod
    def from_bundle(
        cls, bundle: ExecutionPlanBundle, plan: DesignExecutionPlan
    ) -> ExecutionPlanBundleView:
        return cls(
            plan_id=str(bundle.plan_id),
            project_id=bundle.project_id,
            is_production_ready=bundle.is_production_ready,
            created_at=_iso(bundle.created_at),
            source_refs=_source_refs_view(plan),
            pages=[_page_view(p) for p in bundle.pages],
            token_mapping=_token_mapping_view(plan),
            variant_mapping=_variant_mapping_view(plan),
            execution_order=[
                {"node_id": s.node_id, "kind": s.kind, "label": s.label}
                for s in bundle.execution_order
            ],
            review_plan=_review_view(plan),
        )


@dataclass(frozen=True, slots=True)
class TraceView:
    """An explanation of one graph node: the node, its successors, and its evidence."""

    node: dict
    successors: list[dict]
    evidence: list[dict]
