"""Codec — serializes a WireframePlan to a JSON document and back.

A plan is a deep, immutable aggregate; it is stored and loaded whole as one JSON document.
This codec is the single, exhaustive translation. Reconstruction goes through the normal
aggregate constructor, so a decoded plan is re-validated (its provenance and structural
integrity re-checked, its dependency/execution/component/approval graphs re-checked for
acyclicity) — a corrupt document cannot yield an invalid or ungrounded plan. The approval
plan is derived from the decoded sections, so the section-embedded and plan-level approval
requirements can never drift apart.

Pure functions, no I/O.
"""

from __future__ import annotations

from datetime import datetime

from wireframe.domain.approval.approval import ApprovalPlan, ApprovalRequirement
from wireframe.domain.block.block import Block
from wireframe.domain.component.component import ComponentRequirement, DataContractIntent
from wireframe.domain.evidence.evidence import EvidenceGraph, WFEvidence
from wireframe.domain.graph.graphs import WireframeGraphs
from wireframe.domain.graph.wf_graph import WFEdge, WFGraph, WFNode
from wireframe.domain.page.page_plan import PagePlan
from wireframe.domain.plan.blueprint import PlanBlueprint
from wireframe.domain.quality.quality import WireframeQualityMetrics
from wireframe.domain.report.report import WireframePlan
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
    ResponsiveRule,
    SEORequirement,
)
from wireframe.domain.section.section_plan import SectionPlan
from wireframe.domain.shared.ids import (
    ApprovalReqId,
    BlockId,
    ComponentReqId,
    PagePlanId,
    SectionId,
    WFEdgeId,
    WFEvidenceId,
    WFNodeId,
    WireframePlanId,
    WireframePlanLineageId,
)
from wireframe.domain.shared.value_objects import (
    AccessibilityKind,
    ApprovalGate,
    ApproverRole,
    AssetKind,
    BlockKind,
    Breakpoint,
    ComponentKind,
    Confidence,
    DataKind,
    GraphKind,
    GraphRelation,
    InteractionKind,
    IOKind,
    NodeKind,
    PageType,
    Percentage,
    PerformanceKind,
    Priority,
    ProvenanceKind,
    RequirementLevel,
    ResponsiveIntent,
    SEOKind,
    SectionType,
    Tag,
)

__all__ = ["from_document", "to_document"]


# --------------------------------------------------------------------------- #
# Encode                                                                       #
# --------------------------------------------------------------------------- #
def _ids(ids) -> list[str]:
    return [str(i) for i in ids]


def _evidence_doc(e: WFEvidence) -> dict:
    return {
        "id": str(e.id), "provenance": e.provenance.value, "external_ref": e.external_ref,
        "claim": e.claim, "confidence": e.confidence.value, "statement": e.statement,
        "source_name": e.source_name, "tags": sorted(t.value for t in e.tags),
    }


def _block_doc(b: Block) -> dict:
    return {
        "id": str(b.id), "kind": b.kind.value, "label": b.label, "priority": int(b.priority),
        "is_required": b.is_required, "data_kinds": [d.value for d in b.data_kinds],
        "evidence_ids": _ids(b.evidence_ids),
    }


def _component_doc(c: ComponentRequirement) -> dict:
    contract = None
    if c.data_contract is not None:
        contract = {
            "fields": list(c.data_contract.fields), "cardinality": c.data_contract.cardinality,
            "data_kind": (c.data_contract.data_kind.value if c.data_contract.data_kind else None),
        }
    return {
        "id": str(c.id), "component": c.component.value, "requirement": c.requirement.value,
        "rationale": c.rationale, "data_contract": contract,
        "depends_on": [d.value for d in c.depends_on], "evidence_ids": _ids(c.evidence_ids),
    }


def _approval_doc(a: ApprovalRequirement) -> dict:
    return {
        "id": str(a.id), "target": str(a.target), "gate": a.gate.value,
        "approver_role": a.approver_role.value, "criteria": list(a.criteria),
        "depends_on": _ids(a.depends_on), "evidence_ids": _ids(a.evidence_ids),
    }


def _section_doc(s: SectionPlan) -> dict:
    return {
        "id": str(s.id), "type": s.type.value, "execution_order": s.execution_order,
        "is_required": s.is_required, "priority": int(s.priority),
        "parent": (str(s.parent) if s.parent else None), "children": _ids(s.children),
        "goals": {
            "purpose": s.goals.purpose, "business_goal": s.goals.business_goal,
            "user_goal": s.goals.user_goal, "conversion_goal": s.goals.conversion_goal,
            "trust_goal": s.goals.trust_goal, "evidence_ids": _ids(s.goals.evidence_ids),
        },
        "blocks": [_block_doc(b) for b in s.blocks],
        "required_components": [_component_doc(c) for c in s.required_components],
        "optional_components": [_component_doc(c) for c in s.optional_components],
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
        "approval_requirement": (_approval_doc(s.approval_requirement)
                                 if s.approval_requirement else None),
        "evidence_ids": _ids(s.evidence_ids),
    }


def _page_doc(p: PagePlan) -> dict:
    return {
        "id": str(p.id), "page_type": p.page_type.value, "purpose": p.purpose,
        "sections": [_section_doc(s) for s in p.sections], "evidence_ids": _ids(p.evidence_ids),
    }


def _graph_doc(g: WFGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [{"id": str(n.id), "kind": n.kind.value, "label": n.label,
                   "evidence_ids": _ids(n.evidence_ids)} for n in g],
        "edges": [{"id": str(e.id), "source": str(e.source), "target": str(e.target),
                   "relation": e.relation.value} for e in g.edges],
    }


def to_document(plan: WireframePlan) -> dict:
    """Serialize a plan to a JSON-safe document."""
    return {
        "id": str(plan.id), "lineage_id": str(plan.lineage_id), "version": plan.version,
        "project_id": plan.project_id, "created_at": plan.created_at.isoformat(),
        "pages": [_page_doc(p) for p in plan.blueprint.pages],
        "graphs": [_graph_doc(g) for g in plan.graphs.all()],
        "evidence": [_evidence_doc(e) for e in plan.evidence_graph],
        "quality": {
            "coverage": plan.quality.coverage.value, "grounding": plan.quality.grounding.value,
            "completeness": plan.quality.completeness.value, "confidence": plan.quality.confidence.value,
        },
    }


# --------------------------------------------------------------------------- #
# Decode                                                                       #
# --------------------------------------------------------------------------- #
def _ev_ids(raw) -> tuple[WFEvidenceId, ...]:
    return tuple(WFEvidenceId.from_string(i) for i in raw)


def _evidence(doc: dict) -> WFEvidence:
    return WFEvidence(
        id=WFEvidenceId.from_string(doc["id"]),
        provenance=ProvenanceKind(doc["provenance"]), external_ref=doc["external_ref"],
        claim=doc["claim"], confidence=Confidence(doc["confidence"]),
        statement=doc.get("statement", ""), source_name=doc.get("source_name", ""),
        tags=frozenset(Tag.of(t) for t in doc.get("tags", ())),
    )


def _block(doc: dict) -> Block:
    return Block(
        id=BlockId.from_string(doc["id"]), kind=BlockKind(doc["kind"]), label=doc["label"],
        priority=Priority(doc["priority"]), is_required=doc["is_required"],
        data_kinds=tuple(DataKind(d) for d in doc["data_kinds"]),
        evidence_ids=_ev_ids(doc["evidence_ids"]),
    )


def _component(doc: dict) -> ComponentRequirement:
    contract = None
    if doc.get("data_contract") is not None:
        c = doc["data_contract"]
        contract = DataContractIntent(
            fields=tuple(c["fields"]), cardinality=c["cardinality"],
            data_kind=(DataKind(c["data_kind"]) if c["data_kind"] else None),
        )
    return ComponentRequirement(
        id=ComponentReqId.from_string(doc["id"]), component=ComponentKind(doc["component"]),
        requirement=RequirementLevel(doc["requirement"]), rationale=doc["rationale"],
        data_contract=contract,
        depends_on=tuple(ComponentKind(d) for d in doc["depends_on"]),
        evidence_ids=_ev_ids(doc["evidence_ids"]),
    )


def _approval(doc: dict) -> ApprovalRequirement:
    return ApprovalRequirement(
        id=ApprovalReqId.from_string(doc["id"]), target=SectionId.from_string(doc["target"]),
        gate=ApprovalGate(doc["gate"]), approver_role=ApproverRole(doc["approver_role"]),
        criteria=tuple(doc["criteria"]),
        depends_on=tuple(ApprovalReqId.from_string(d) for d in doc["depends_on"]),
        evidence_ids=_ev_ids(doc["evidence_ids"]),
    )


def _section(doc: dict) -> SectionPlan:
    g = doc["goals"]
    return SectionPlan(
        id=SectionId.from_string(doc["id"]), type=SectionType(doc["type"]),
        goals=SectionGoals(
            purpose=g["purpose"], business_goal=g["business_goal"], user_goal=g["user_goal"],
            conversion_goal=g["conversion_goal"], trust_goal=g["trust_goal"],
            evidence_ids=_ev_ids(g["evidence_ids"]),
        ),
        execution_order=doc["execution_order"], is_required=doc["is_required"],
        priority=Priority(doc["priority"]),
        parent=(SectionId.from_string(doc["parent"]) if doc["parent"] else None),
        children=tuple(SectionId.from_string(c) for c in doc["children"]),
        blocks=tuple(_block(b) for b in doc["blocks"]),
        required_components=tuple(_component(c) for c in doc["required_components"]),
        optional_components=tuple(_component(c) for c in doc["optional_components"]),
        required_data=tuple(
            DataRequirement(kind=DataKind(d["kind"]), description=d["description"], required=d["required"])
            for d in doc["required_data"]
        ),
        required_assets=tuple(
            AssetRequirement(kind=AssetKind(a["kind"]), description=a["description"], required=a["required"])
            for a in doc["required_assets"]
        ),
        interaction_requirements=tuple(
            InteractionRequirement(kind=InteractionKind(i["kind"]), intent=i["intent"])
            for i in doc["interaction_requirements"]
        ),
        responsive_behaviour=ResponsiveBehaviour(rules=tuple(
            ResponsiveRule(breakpoint=Breakpoint(r["breakpoint"]), intent=ResponsiveIntent(r["intent"]))
            for r in doc["responsive_behaviour"]
        )),
        accessibility_requirements=tuple(
            AccessibilityRequirement(kind=AccessibilityKind(a["kind"]), intent=a["intent"])
            for a in doc["accessibility_requirements"]
        ),
        seo_requirements=tuple(
            SEORequirement(kind=SEOKind(r["kind"]), intent=r["intent"]) for r in doc["seo_requirements"]
        ),
        performance_considerations=tuple(
            PerformanceConsideration(kind=PerformanceKind(p["kind"]), intent=p["intent"])
            for p in doc["performance_considerations"]
        ),
        inputs=tuple(SectionIO(kind=IOKind(io["kind"]), name=io["name"]) for io in doc["inputs"]),
        outputs=tuple(SectionIO(kind=IOKind(io["kind"]), name=io["name"]) for io in doc["outputs"]),
        dependencies=tuple(SectionId.from_string(d) for d in doc["dependencies"]),
        success_criteria=tuple(SuccessCriterion(s) for s in doc["success_criteria"]),
        failure_criteria=tuple(FailureCriterion(s) for s in doc["failure_criteria"]),
        review_checklist=tuple(
            ChecklistItem(statement=c["statement"], blocking=c["blocking"])
            for c in doc["review_checklist"]
        ),
        approval_requirement=(_approval(doc["approval_requirement"])
                              if doc["approval_requirement"] else None),
        evidence_ids=_ev_ids(doc["evidence_ids"]),
    )


def _page(doc: dict) -> PagePlan:
    return PagePlan(
        id=PagePlanId.from_string(doc["id"]), page_type=PageType(doc["page_type"]),
        purpose=doc["purpose"], sections=tuple(_section(s) for s in doc["sections"]),
        evidence_ids=_ev_ids(doc["evidence_ids"]),
    )


def _graph(doc: dict) -> WFGraph:
    return WFGraph.of(
        GraphKind(doc["kind"]),
        [WFNode(id=WFNodeId.from_string(n["id"]), kind=NodeKind(n["kind"]), label=n["label"],
                evidence_ids=_ev_ids(n["evidence_ids"])) for n in doc["nodes"]],
        [WFEdge(id=WFEdgeId.from_string(e["id"]), source=WFNodeId.from_string(e["source"]),
                target=WFNodeId.from_string(e["target"]), relation=GraphRelation(e["relation"]))
         for e in doc["edges"]],
    )


def from_document(doc: dict) -> WireframePlan:
    """Reconstruct a plan from its document, re-validating every invariant."""
    blueprint = PlanBlueprint.of(_page(p) for p in doc["pages"])
    approval_plan = ApprovalPlan.of(
        s.approval_requirement
        for s in blueprint.sections()
        if s.approval_requirement is not None
    )
    q = doc["quality"]
    return WireframePlan(
        id=WireframePlanId.from_string(doc["id"]),
        lineage_id=WireframePlanLineageId.from_string(doc["lineage_id"]),
        version=doc["version"], project_id=doc["project_id"],
        blueprint=blueprint, approval_plan=approval_plan,
        graphs=WireframeGraphs.of(_graph(g) for g in doc["graphs"]),
        evidence_graph=EvidenceGraph.of(_evidence(e) for e in doc["evidence"]),
        quality=WireframeQualityMetrics(
            coverage=Percentage(q["coverage"]), grounding=Percentage(q["grounding"]),
            completeness=Percentage(q["completeness"]), confidence=Confidence(q["confidence"]),
        ),
        created_at=datetime.fromisoformat(doc["created_at"]),
    )
