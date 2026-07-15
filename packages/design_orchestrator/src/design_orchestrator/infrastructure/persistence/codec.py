"""Codec — serializes a DesignExecutionPlan to a JSON document and back.

A plan is a deep, immutable aggregate; it is stored and loaded whole as one JSON document. This
codec is the single, exhaustive translation. Reconstruction goes through the normal aggregate
constructor, so a decoded plan is re-validated (its provenance and binding integrity re-checked,
its graphs re-checked for acyclicity, its tree re-checked) — a corrupt document cannot yield an
inconsistent or ungrounded plan.

Pure functions, no I/O.
"""

from __future__ import annotations

from datetime import datetime

from design_orchestrator.domain.context.context import SourceRefs
from design_orchestrator.domain.evidence.evidence import Citation, DOEvidence, EvidenceGraph
from design_orchestrator.domain.graph.do_graph import DOEdge, DOGraph, DONode
from design_orchestrator.domain.graph.graphs import OrchestratorGraphs
from design_orchestrator.domain.layout.layout import GridPlacement, LayoutModel, LayoutRegion
from design_orchestrator.domain.mapping.token_mapping import TokenMapping
from design_orchestrator.domain.mapping.variant_mapping import VariantChoice, VariantMapping
from design_orchestrator.domain.plan.choice import (
    LayoutRule,
    SpacingRule,
    TypographyChoice,
    VisualChoice,
)
from design_orchestrator.domain.plan.directives import (
    AccessibilityDirective,
    AnimationDirective,
    PerformanceDirective,
    ResponsiveDirective,
)
from design_orchestrator.domain.plan.page import PagePlan
from design_orchestrator.domain.plan.section import SectionPlan
from design_orchestrator.domain.quality.quality import ExecutionPlanQualityMetrics
from design_orchestrator.domain.report.report import DesignExecutionPlan
from design_orchestrator.domain.review.review_plan import ReviewCheckpoint, ReviewPlan
from design_orchestrator.domain.shared.ids import (
    DesignExecutionPlanId,
    DesignExecutionPlanLineageId,
    DOEdgeId,
    DOEvidenceId,
    DONodeId,
    LayoutRegionId,
    PagePlanId,
    ReviewCheckpointId,
    SectionPlanId,
)
from design_orchestrator.domain.shared.value_objects import (
    Alignment,
    Breakpoint,
    CheckpointStatus,
    ComponentType,
    Confidence,
    ConsideredAlternative,
    Density,
    ExecutionStepKind,
    GraphKind,
    GraphRelation,
    LayoutMode,
    LayoutRegionKind,
    NodeKind,
    PageType,
    Percentage,
    ProvenanceKind,
    Rank,
    ReviewGateKind,
    SectionRole,
    Tag,
    ThemeMode,
    TreeNodeKind,
)
from design_orchestrator.domain.tree.component_tree import ComponentTree, TreeNode

__all__ = ["from_document", "to_document"]


def _ids(ids) -> list[str]:
    return [str(i) for i in ids]


def _citations_doc(citations) -> list[dict]:
    return [{"evidence_id": str(c.evidence_id), "relevance": c.relevance} for c in citations]


# --------------------------------------------------------------------------- #
# Encode                                                                       #
# --------------------------------------------------------------------------- #
def _section_doc(s: SectionPlan) -> dict:
    return {
        "id": str(s.id),
        "page_type": s.page_type.value,
        "order": int(s.order),
        "role": s.role.value,
        "component": s.component.value,
        "variant_name": s.variant_name,
        "layout": {"mode": s.layout.mode.value, "alignment": s.layout.alignment.value,
                   "density": s.layout.density.value, "columns": s.layout.columns},
        "spacing": {"gap_token": s.spacing.gap_token, "block_token": s.spacing.block_token},
        "typography": {"heading_token": s.typography.heading_token,
                       "body_token": s.typography.body_token},
        "visual": {"theme_mode": s.visual.theme_mode.value,
                   "surface_tokens": list(s.visual.surface_tokens), "emphasis": s.visual.emphasis},
        "token_bindings": list(s.token_bindings),
        "responsive": {bp.value: note for bp, note in s.responsive.behavior.items()},
        "animation": {"duration_token": s.animation.duration_token,
                      "easing_token": s.animation.easing_token, "trigger": s.animation.trigger},
        "accessibility": {"role": s.accessibility.role, "min_contrast": s.accessibility.min_contrast,
                          "keyboard": list(s.accessibility.keyboard),
                          "focus_visible": s.accessibility.focus_visible},
        "performance": {"lazy_load": s.performance.lazy_load, "priority": s.performance.priority,
                        "blocks_lcp": s.performance.blocks_lcp},
        "considered_alternative": (
            {"option": s.considered_alternative.option,
             "reason_rejected": s.considered_alternative.reason_rejected}
            if s.considered_alternative else None),
        "citations": _citations_doc(s.citations),
    }


def _page_doc(p: PagePlan) -> dict:
    return {
        "id": str(p.id), "page_type": p.page_type.value, "region_id": str(p.region_id),
        "sections": [_section_doc(s) for s in p.sections],
    }


def _tree_doc(tree: ComponentTree) -> list[dict]:
    return [
        {"id": str(n.id), "kind": n.kind.value, "label": n.label,
         "parent_id": str(n.parent_id) if n.parent_id is not None else None,
         "order": n.order,
         "section_ref": str(n.section_ref) if n.section_ref is not None else None,
         "evidence_ids": _ids(n.evidence_ids)}
        for n in tree
    ]


def _layout_doc(lm: LayoutModel) -> dict:
    return {
        "regions": [
            {"id": str(r.id), "kind": r.kind.value, "page_type": r.page_type.value,
             "parent_id": str(r.parent_id) if r.parent_id is not None else None, "label": r.label}
            for r in lm.regions.values()
        ],
        "placements": [
            {"region_id": str(p.region_id), "breakpoint": p.breakpoint.value,
             "column_start": p.column_start, "column_span": p.column_span, "order": p.order}
            for p in lm.placements
        ],
    }


def _graph_doc(g: DOGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [{"id": str(n.id), "kind": n.kind.value, "label": n.label,
                   "evidence_ids": _ids(n.evidence_ids)} for n in g],
        "edges": [{"id": str(e.id), "source": str(e.source), "target": str(e.target),
                   "relation": e.relation.value} for e in g.edges],
    }


def to_document(plan: DesignExecutionPlan) -> dict:
    """Serialize a plan to a JSON-safe document."""
    sr = plan.source_refs
    return {
        "id": str(plan.id), "lineage_id": str(plan.lineage_id), "version": plan.version,
        "project_id": plan.project_id, "created_at": plan.created_at.isoformat(),
        "source_refs": {
            "design_system_spec_id": sr.design_system_spec_id,
            "component_spec_id": sr.component_spec_id,
            "design_language_spec_id": sr.design_language_spec_id,
            "creative_director_review_id": sr.creative_director_review_id,
            "wireframe_plan_id": sr.wireframe_plan_id,
            "ia_report_id": sr.ia_report_id,
        },
        "pages": [_page_doc(p) for p in plan.pages],
        "component_tree": _tree_doc(plan.component_tree),
        "layout": _layout_doc(plan.layout_model),
        "token_mapping": {str(sid): list(keys) for sid, keys in plan.token_mapping},
        "variant_mapping": {
            str(sid): {"component": c.component.value, "variant_name": c.variant_name}
            for sid, c in plan.variant_mapping
        },
        "graphs": [_graph_doc(g) for g in plan.graphs.all],
        "review_plan": [
            {"id": str(c.id), "gate": c.gate.value, "after_step": c.after_step.value,
             "statement": c.statement, "pass_criteria": list(c.pass_criteria),
             "status": c.status.value, "citations": _citations_doc(c.citations)}
            for c in plan.review_plan
        ],
        "evidence": [
            {"id": str(e.id), "provenance": e.provenance.value, "external_ref": e.external_ref,
             "claim": e.claim, "confidence": e.confidence.value, "statement": e.statement,
             "source_name": e.source_name, "tags": sorted(t.value for t in e.tags)}
            for e in plan.evidence_graph
        ],
        "quality": {
            "coverage": plan.quality.coverage.value,
            "binding_integrity": plan.quality.binding_integrity.value,
            "sequencing": plan.quality.sequencing.value,
            "grounding": plan.quality.grounding.value,
            "confidence": plan.quality.confidence.value,
        },
    }


# --------------------------------------------------------------------------- #
# Decode                                                                       #
# --------------------------------------------------------------------------- #
def _ev_ids(raw) -> tuple[DOEvidenceId, ...]:
    return tuple(DOEvidenceId.from_string(i) for i in raw)


def _citations(raw) -> tuple[Citation, ...]:
    return tuple(
        Citation(evidence_id=DOEvidenceId.from_string(c["evidence_id"]), relevance=c["relevance"])
        for c in raw
    )


def _section(doc: dict) -> SectionPlan:
    a, p = doc["accessibility"], doc["performance"]
    ca = doc["considered_alternative"]
    return SectionPlan(
        id=SectionPlanId.from_string(doc["id"]),
        page_type=PageType(doc["page_type"]),
        order=Rank(doc["order"]),
        role=SectionRole(doc["role"]),
        component=ComponentType(doc["component"]),
        variant_name=doc["variant_name"],
        layout=LayoutRule(mode=LayoutMode(doc["layout"]["mode"]),
                          alignment=Alignment(doc["layout"]["alignment"]),
                          density=Density(doc["layout"]["density"]),
                          columns=doc["layout"]["columns"]),
        spacing=SpacingRule(gap_token=doc["spacing"]["gap_token"],
                            block_token=doc["spacing"]["block_token"]),
        typography=TypographyChoice(heading_token=doc["typography"]["heading_token"],
                                    body_token=doc["typography"]["body_token"]),
        visual=VisualChoice(theme_mode=ThemeMode(doc["visual"]["theme_mode"]),
                            surface_tokens=tuple(doc["visual"]["surface_tokens"]),
                            emphasis=doc["visual"]["emphasis"]),
        token_bindings=tuple(doc["token_bindings"]),
        responsive=ResponsiveDirective(
            behavior={Breakpoint(bp): note for bp, note in doc["responsive"].items()}),
        animation=AnimationDirective(duration_token=doc["animation"]["duration_token"],
                                     easing_token=doc["animation"]["easing_token"],
                                     trigger=doc["animation"]["trigger"]),
        accessibility=AccessibilityDirective(role=a["role"], min_contrast=a["min_contrast"],
                                             keyboard=tuple(a["keyboard"]),
                                             focus_visible=a["focus_visible"]),
        performance=PerformanceDirective(lazy_load=p["lazy_load"], priority=p["priority"],
                                         blocks_lcp=p["blocks_lcp"]),
        considered_alternative=(ConsideredAlternative(option=ca["option"],
                                reason_rejected=ca["reason_rejected"]) if ca else None),
        citations=_citations(doc["citations"]),
    )


def _page(doc: dict) -> PagePlan:
    return PagePlan(
        id=PagePlanId.from_string(doc["id"]),
        page_type=PageType(doc["page_type"]),
        region_id=LayoutRegionId.from_string(doc["region_id"]),
        sections=tuple(_section(s) for s in doc["sections"]),
    )


def _tree(docs: list[dict]) -> ComponentTree:
    return ComponentTree.of(
        TreeNode(
            id=DONodeId.from_string(n["id"]), kind=TreeNodeKind(n["kind"]), label=n["label"],
            parent_id=DONodeId.from_string(n["parent_id"]) if n["parent_id"] else None,
            order=n["order"],
            section_ref=SectionPlanId.from_string(n["section_ref"]) if n["section_ref"] else None,
            evidence_ids=_ev_ids(n["evidence_ids"]),
        )
        for n in docs
    )


def _layout(doc: dict) -> LayoutModel:
    regions = [
        LayoutRegion(id=LayoutRegionId.from_string(r["id"]), kind=LayoutRegionKind(r["kind"]),
                     page_type=PageType(r["page_type"]),
                     parent_id=LayoutRegionId.from_string(r["parent_id"]) if r["parent_id"] else None,
                     label=r["label"])
        for r in doc["regions"]
    ]
    placements = [
        GridPlacement(region_id=LayoutRegionId.from_string(p["region_id"]),
                      breakpoint=Breakpoint(p["breakpoint"]), column_start=p["column_start"],
                      column_span=p["column_span"], order=p["order"])
        for p in doc["placements"]
    ]
    return LayoutModel.of(regions, placements)


def _graph(doc: dict) -> DOGraph:
    return DOGraph.of(
        GraphKind(doc["kind"]),
        [DONode(id=DONodeId.from_string(n["id"]), kind=NodeKind(n["kind"]), label=n["label"],
                evidence_ids=_ev_ids(n["evidence_ids"])) for n in doc["nodes"]],
        [DOEdge(id=DOEdgeId.from_string(e["id"]), source=DONodeId.from_string(e["source"]),
                target=DONodeId.from_string(e["target"]), relation=GraphRelation(e["relation"]))
         for e in doc["edges"]],
    )


def from_document(doc: dict) -> DesignExecutionPlan:
    """Reconstruct a plan from its document, re-validating every invariant."""
    sr = doc["source_refs"]
    q = doc["quality"]
    graphs_by_kind = {GraphKind(g["kind"]): _graph(g) for g in doc["graphs"]}
    token_mapping = TokenMapping(
        {SectionPlanId.from_string(sid): tuple(keys)
         for sid, keys in doc["token_mapping"].items()}
    )
    variant_mapping = VariantMapping(
        {SectionPlanId.from_string(sid): VariantChoice(
            component=ComponentType(v["component"]), variant_name=v["variant_name"])
         for sid, v in doc["variant_mapping"].items()}
    )
    return DesignExecutionPlan(
        id=DesignExecutionPlanId.from_string(doc["id"]),
        lineage_id=DesignExecutionPlanLineageId.from_string(doc["lineage_id"]),
        version=doc["version"],
        project_id=doc["project_id"],
        source_refs=SourceRefs(
            design_system_spec_id=sr["design_system_spec_id"],
            component_spec_id=sr["component_spec_id"],
            design_language_spec_id=sr["design_language_spec_id"],
            creative_director_review_id=sr["creative_director_review_id"],
            wireframe_plan_id=sr["wireframe_plan_id"],
            ia_report_id=sr["ia_report_id"],
        ),
        pages=tuple(_page(p) for p in doc["pages"]),
        component_tree=_tree(doc["component_tree"]),
        layout_model=_layout(doc["layout"]),
        token_mapping=token_mapping,
        variant_mapping=variant_mapping,
        graphs=OrchestratorGraphs(
            execution=graphs_by_kind[GraphKind.EXECUTION],
            layout=graphs_by_kind[GraphKind.LAYOUT],
        ),
        review_plan=ReviewPlan(tuple(
            ReviewCheckpoint(
                id=ReviewCheckpointId.from_string(c["id"]), gate=ReviewGateKind(c["gate"]),
                after_step=ExecutionStepKind(c["after_step"]), statement=c["statement"],
                pass_criteria=tuple(c["pass_criteria"]), status=CheckpointStatus(c["status"]),
                citations=_citations(c["citations"]))
            for c in doc["review_plan"]
        )),
        evidence_graph=EvidenceGraph.of(
            DOEvidence(id=DOEvidenceId.from_string(e["id"]),
                provenance=ProvenanceKind(e["provenance"]), external_ref=e["external_ref"],
                claim=e["claim"], confidence=Confidence(e["confidence"]),
                statement=e.get("statement", ""), source_name=e.get("source_name", ""),
                tags=frozenset(Tag.of(t) for t in e.get("tags", ())))
            for e in doc["evidence"]
        ),
        quality=ExecutionPlanQualityMetrics(
            coverage=Percentage(q["coverage"]),
            binding_integrity=Percentage(q["binding_integrity"]),
            sequencing=Percentage(q["sequencing"]),
            grounding=Percentage(q["grounding"]),
            confidence=Confidence(q["confidence"]),
        ),
        created_at=datetime.fromisoformat(doc["created_at"]),
    )
