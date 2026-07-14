"""Unit tests for the wireframe domain — the invariants that make a plan trustworthy."""

from __future__ import annotations

import pytest

from wireframe.domain.approval.approval import ApprovalPlan, ApprovalRequirement
from wireframe.domain.block.block import Block
from wireframe.domain.component.component import ComponentRequirement
from wireframe.domain.evidence.evidence import EvidenceGraph, InvalidEvidenceError, WFEvidence
from wireframe.domain.graph.wf_graph import (
    InvalidWFGraphError,
    WFEdge,
    WFGraph,
    WFNode,
)
from wireframe.domain.page.page_plan import PagePlan
from wireframe.domain.plan.blueprint import InvalidPlanBlueprintError, PlanBlueprint
from wireframe.domain.quality.quality import WireframeQualityMetrics
from wireframe.domain.section.goals import SectionGoals
from wireframe.domain.section.section_plan import InvalidSectionPlanError, SectionPlan
from wireframe.domain.shared.ids import (
    ApprovalReqId,
    BlockId,
    ComponentReqId,
    PagePlanId,
    SectionId,
    WFEdgeId,
    WFEvidenceId,
    WFNodeId,
)
from wireframe.domain.shared.value_objects import (
    ApprovalGate,
    ApproverRole,
    BlockKind,
    ComponentKind,
    Confidence,
    GraphKind,
    GraphRelation,
    NodeKind,
    PageType,
    Percentage,
    Priority,
    ProvenanceKind,
    RequirementLevel,
    SectionType,
    WFScore,
)


# --- value objects -------------------------------------------------------- #

def test_page_type_and_graph_kind_cardinality() -> None:
    assert len(PageType) == 10
    assert len(GraphKind) == 6


@pytest.mark.parametrize("bad", [-0.01, 1.01])
def test_confidence_rejects_out_of_range(bad: float) -> None:
    with pytest.raises(Exception):
        Confidence(bad)


@pytest.mark.parametrize("bad", [0, 6])
def test_priority_rejects_out_of_range(bad: int) -> None:
    with pytest.raises(Exception):
        Priority(bad)


def test_wfscore_clamps() -> None:
    assert WFScore.clamp(150.0).value == 100.0
    assert WFScore.clamp(-5.0).value == 0.0


# --- evidence ------------------------------------------------------------- #

def _ev(ref: str) -> WFEvidence:
    return WFEvidence(
        id=WFEvidenceId.new(), provenance=ProvenanceKind.INFORMATION_ARCHITECTURE,
        external_ref=ref, claim=f"claim {ref}", confidence=Confidence(0.8),
    )


def test_evidence_requires_ref() -> None:
    with pytest.raises(InvalidEvidenceError):
        WFEvidence(id=WFEvidenceId.new(), provenance=ProvenanceKind.KNOWLEDGE,
                   external_ref="", claim="x", confidence=Confidence(0.5))


def test_evidence_graph_missing_and_duplicates() -> None:
    e = _ev("e1")
    graph = EvidenceGraph.of([e])
    absent = WFEvidenceId.new()
    assert graph.missing([e.id]) == () and graph.missing([absent]) == (absent,)
    with pytest.raises(InvalidEvidenceError):
        EvidenceGraph.of([e, e])


# --- graph ---------------------------------------------------------------- #

def _node() -> WFNode:
    return WFNode(id=WFNodeId.new(), kind=NodeKind.SECTION, label="Hero")


def test_graph_rejects_self_loop() -> None:
    n = _node()
    with pytest.raises(InvalidWFGraphError):
        WFEdge(id=WFEdgeId.new(), source=n.id, target=n.id, relation=GraphRelation.DEPENDS_ON)


def test_graph_detects_dependency_cycle() -> None:
    a, b = _node(), _node()
    with pytest.raises(InvalidWFGraphError):
        WFGraph.of(
            GraphKind.SECTION_DEPENDENCY, [a, b],
            [
                WFEdge(id=WFEdgeId.new(), source=a.id, target=b.id, relation=GraphRelation.DEPENDS_ON),
                WFEdge(id=WFEdgeId.new(), source=b.id, target=a.id, relation=GraphRelation.DEPENDS_ON),
            ],
        )


def test_graph_rejects_dangling_edge() -> None:
    a, b = _node(), _node()
    with pytest.raises(InvalidWFGraphError):
        WFGraph.of(
            GraphKind.EXECUTION, [a],
            [WFEdge(id=WFEdgeId.new(), source=a.id, target=b.id, relation=GraphRelation.ORDERED_BEFORE)],
        )


# --- section / blueprint -------------------------------------------------- #

def _goals() -> SectionGoals:
    return SectionGoals(purpose="p", business_goal="sell", user_goal="buy")


def _required_component() -> ComponentRequirement:
    return ComponentRequirement(
        id=ComponentReqId.new(), component=ComponentKind.ADD_TO_CART,
        requirement=RequirementLevel.REQUIRED,
    )


def _section(page_type_unique: SectionType = SectionType.HERO, **kw) -> SectionPlan:
    return SectionPlan(id=SectionId.new(), type=page_type_unique, goals=_goals(), **kw)


def test_section_rejects_self_dependency() -> None:
    sid = SectionId.new()
    with pytest.raises(InvalidSectionPlanError):
        SectionPlan(id=sid, type=SectionType.HERO, goals=_goals(), dependencies=(sid,))


def test_section_rejects_optional_in_required_components() -> None:
    optional = ComponentRequirement(
        id=ComponentReqId.new(), component=ComponentKind.NEWSLETTER_FORM,
        requirement=RequirementLevel.OPTIONAL,
    )
    with pytest.raises(InvalidSectionPlanError):
        SectionPlan(id=SectionId.new(), type=SectionType.HERO, goals=_goals(),
                    required_components=(optional,))


def test_blueprint_rejects_duplicate_page_type() -> None:
    p1 = PagePlan(id=PagePlanId.new(), page_type=PageType.PRODUCT, purpose="x",
                  sections=(_section(),))
    p2 = PagePlan(id=PagePlanId.new(), page_type=PageType.PRODUCT, purpose="y",
                  sections=(_section(),))
    with pytest.raises(InvalidPlanBlueprintError):
        PlanBlueprint.of([p1, p2])


def test_blueprint_allows_duplicate_cms() -> None:
    p1 = PagePlan(id=PagePlanId.new(), page_type=PageType.CMS, purpose="about",
                  sections=(_section(),))
    p2 = PagePlan(id=PagePlanId.new(), page_type=PageType.CMS, purpose="contact",
                  sections=(_section(),))
    assert len(PlanBlueprint.of([p1, p2])) == 2


def test_blueprint_rejects_section_id_reuse_across_pages() -> None:
    shared = _section()
    p1 = PagePlan(id=PagePlanId.new(), page_type=PageType.HOMEPAGE, purpose="x", sections=(shared,))
    p2 = PagePlan(id=PagePlanId.new(), page_type=PageType.PRODUCT, purpose="y", sections=(shared,))
    with pytest.raises(InvalidPlanBlueprintError):
        PlanBlueprint.of([p1, p2])


# --- approval ------------------------------------------------------------- #

def test_approval_plan_rejects_duplicate_ids() -> None:
    req = ApprovalRequirement(
        id=ApprovalReqId.new(), target=SectionId.new(), gate=ApprovalGate.DESIGN_REVIEW,
        approver_role=ApproverRole.DESIGNER,
    )
    with pytest.raises(Exception):
        ApprovalPlan.of([req, req])


def test_approval_roots_are_dependency_free() -> None:
    a = ApprovalReqId.new()
    r1 = ApprovalRequirement(id=a, target=SectionId.new(), gate=ApprovalGate.AUTO,
                             approver_role=ApproverRole.SYSTEM)
    r2 = ApprovalRequirement(id=ApprovalReqId.new(), target=SectionId.new(),
                             gate=ApprovalGate.DESIGN_REVIEW, approver_role=ApproverRole.DESIGNER,
                             depends_on=(a,))
    plan = ApprovalPlan.of([r1, r2])
    assert {r.id for r in plan.roots()} == {r1.id}


# --- quality -------------------------------------------------------------- #

def test_quality_weighting_and_grounding() -> None:
    perfect = WireframeQualityMetrics(
        coverage=Percentage(1.0), grounding=Percentage(1.0),
        completeness=Percentage(1.0), confidence=Confidence(1.0),
    )
    assert perfect.overall_score.value == 100.0 and perfect.is_fully_grounded

    partial = WireframeQualityMetrics(
        coverage=Percentage(0.5), grounding=Percentage(0.8),
        completeness=Percentage(0.4), confidence=Confidence(0.6),
    )
    # 0.3*0.5 + 0.3*0.8 + 0.25*0.4 + 0.15*0.6 = 0.58 → 58
    assert partial.overall_score.value == pytest.approx(58.0)
    assert not partial.is_fully_grounded


def test_block_and_component_helpers() -> None:
    ev = WFEvidenceId.new()
    block = Block(id=BlockId.new(), kind=BlockKind.CTA, label="Add to cart", evidence_ids=(ev,))
    assert block.all_evidence_ids() == (ev,)
    comp = _required_component()
    assert comp.is_required
