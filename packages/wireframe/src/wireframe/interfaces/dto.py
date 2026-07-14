"""Serializable view DTOs — the plan projected for transport.

The facade never returns domain aggregates; it returns these flat, immutable views. They
project a :class:`WireframePlan` (and the neutral :class:`FigmaPlanBundle`) into plain
``dict``-friendly structures an API, the orchestration layer, or a future Figma engine can
serialize — carrying the full plan (pages, sections, blocks, components, requirements,
criteria, checklists, approvals, and the six graphs) but no domain objects and no visual
properties.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from wireframe.domain.approval.approval import ApprovalPlan, ApprovalRequirement
from wireframe.domain.block.block import Block
from wireframe.domain.component.component import ComponentRequirement
from wireframe.domain.graph.wf_graph import WFGraph
from wireframe.domain.page.page_plan import PagePlan
from wireframe.domain.report.bundle import FigmaPlanBundle
from wireframe.domain.report.report import WireframePlan
from wireframe.domain.section.section_plan import SectionPlan

__all__ = [
    "ApprovalView",
    "FigmaPlanBundleView",
    "GraphView",
    "PageView",
    "PlanView",
    "QualityView",
    "SectionView",
    "WireframeTraceView",
]


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _ids(ids) -> list[str]:
    return [str(i) for i in ids]


def _block_view(b: Block) -> dict:
    return {
        "id": str(b.id), "kind": b.kind.value, "label": b.label,
        "priority": int(b.priority), "is_required": b.is_required,
        "data_kinds": [d.value for d in b.data_kinds], "evidence_ids": _ids(b.evidence_ids),
    }


def _component_view(c: ComponentRequirement) -> dict:
    return {
        "id": str(c.id), "component": c.component.value, "requirement": c.requirement.value,
        "rationale": c.rationale,
        "data_contract": (
            {
                "fields": list(c.data_contract.fields),
                "cardinality": c.data_contract.cardinality,
                "data_kind": (c.data_contract.data_kind.value if c.data_contract.data_kind else None),
            }
            if c.data_contract is not None
            else None
        ),
        "depends_on": [d.value for d in c.depends_on],
        "evidence_ids": _ids(c.evidence_ids),
    }


def _approval_req_view(a: ApprovalRequirement) -> dict:
    return {
        "id": str(a.id), "target": str(a.target), "gate": a.gate.value,
        "approver_role": a.approver_role.value, "criteria": list(a.criteria),
        "depends_on": _ids(a.depends_on), "evidence_ids": _ids(a.evidence_ids),
    }


def _section_view(s: SectionPlan) -> dict:
    return {
        "id": str(s.id), "type": s.type.value, "execution_order": s.execution_order,
        "is_required": s.is_required, "priority": int(s.priority),
        "parent": (str(s.parent) if s.parent else None),
        "children": _ids(s.children),
        "goals": {
            "purpose": s.goals.purpose, "business_goal": s.goals.business_goal,
            "user_goal": s.goals.user_goal, "conversion_goal": s.goals.conversion_goal,
            "trust_goal": s.goals.trust_goal, "evidence_ids": _ids(s.goals.evidence_ids),
        },
        "blocks": [_block_view(b) for b in s.blocks],
        "required_components": [_component_view(c) for c in s.required_components],
        "optional_components": [_component_view(c) for c in s.optional_components],
        "required_data": [{"kind": d.kind.value, "description": d.description, "required": d.required}
                          for d in s.required_data],
        "required_assets": [{"kind": a.kind.value, "description": a.description, "required": a.required}
                            for a in s.required_assets],
        "interaction_requirements": [{"kind": i.kind.value, "intent": i.intent}
                                     for i in s.interaction_requirements],
        "responsive_behaviour": [{"breakpoint": r.breakpoint.value, "intent": r.intent.value}
                                 for r in s.responsive_behaviour.rules],
        "accessibility_requirements": [{"kind": a.kind.value, "intent": a.intent}
                                       for a in s.accessibility_requirements],
        "seo_requirements": [{"kind": r.kind.value, "intent": r.intent} for r in s.seo_requirements],
        "performance_considerations": [{"kind": p.kind.value, "intent": p.intent}
                                       for p in s.performance_considerations],
        "inputs": [{"kind": io.kind.value, "name": io.name} for io in s.inputs],
        "outputs": [{"kind": io.kind.value, "name": io.name} for io in s.outputs],
        "dependencies": _ids(s.dependencies),
        "success_criteria": [c.statement for c in s.success_criteria],
        "failure_criteria": [c.statement for c in s.failure_criteria],
        "review_checklist": [{"statement": c.statement, "blocking": c.blocking}
                             for c in s.review_checklist],
        "approval_requirement": (
            _approval_req_view(s.approval_requirement) if s.approval_requirement else None
        ),
        "evidence_ids": _ids(s.evidence_ids),
    }


def _page_view(p: PagePlan) -> dict:
    return {
        "id": str(p.id), "page_type": p.page_type.value, "purpose": p.purpose,
        "sections": [_section_view(s) for s in p.sections_in_execution_order()],
        "evidence_ids": _ids(p.evidence_ids),
    }


def _graph_view(g: WFGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [{"id": str(n.id), "kind": n.kind.value, "label": n.label,
                   "evidence_ids": _ids(n.evidence_ids)} for n in g],
        "edges": [{"source": str(e.source), "target": str(e.target), "relation": e.relation.value}
                  for e in g.edges],
    }


def _approval_view(plan: ApprovalPlan) -> dict:
    return {"requirements": [_approval_req_view(r) for r in plan]}


@dataclass(frozen=True, slots=True)
class QualityView:
    overall_score: float
    band: str
    coverage: float
    grounding: float
    completeness: float
    confidence: float
    is_fully_grounded: bool


@dataclass(frozen=True, slots=True)
class PageView:
    page: dict


@dataclass(frozen=True, slots=True)
class SectionView:
    section: dict


@dataclass(frozen=True, slots=True)
class GraphView:
    graph: dict


@dataclass(frozen=True, slots=True)
class ApprovalView:
    approval: dict


@dataclass(frozen=True, slots=True)
class PlanView:
    """The full, flat projection of a wireframe plan."""

    plan_id: str
    lineage_id: str
    version: int
    project_id: str
    is_usable: bool
    created_at: str
    quality: QualityView
    pages: list[dict]
    approval_plan: dict
    graphs: dict
    page_count: int
    section_count: int
    evidence_count: int

    @classmethod
    def from_plan(cls, plan: WireframePlan) -> PlanView:
        quality = QualityView(
            overall_score=plan.quality.overall_score.value, band=plan.quality.band.value,
            coverage=plan.quality.coverage.value, grounding=plan.quality.grounding.value,
            completeness=plan.quality.completeness.value, confidence=plan.quality.confidence.value,
            is_fully_grounded=plan.quality.is_fully_grounded,
        )
        return cls(
            plan_id=str(plan.id), lineage_id=str(plan.lineage_id), version=plan.version,
            project_id=plan.project_id, is_usable=plan.is_usable, created_at=_iso(plan.created_at),
            quality=quality,
            pages=[_page_view(p) for p in plan.blueprint.pages],
            approval_plan=_approval_view(plan.approval_plan),
            graphs={g.kind.value: _graph_view(g) for g in plan.graphs.all()},
            page_count=plan.page_count(), section_count=plan.section_count(),
            evidence_count=plan.evidence_count(),
        )


@dataclass(frozen=True, slots=True)
class FigmaPlanBundleView:
    """The neutral wireframe plan a downstream Figma engine consumes."""

    plan_id: str
    project_id: str
    pages: list[dict]
    approval_plan: dict
    is_usable: bool
    created_at: str

    @classmethod
    def from_bundle(cls, b: FigmaPlanBundle) -> FigmaPlanBundleView:
        return cls(
            plan_id=str(b.plan_id), project_id=b.project_id,
            pages=[_page_view(p) for p in b.pages],
            approval_plan=_approval_view(b.approval_plan),
            is_usable=b.is_usable, created_at=_iso(b.created_at),
        )


@dataclass(frozen=True, slots=True)
class WireframeTraceView:
    """An explanation of one graph node: the node, its successors, and its evidence."""

    node: dict
    successors: list[dict]
    evidence: list[dict]
