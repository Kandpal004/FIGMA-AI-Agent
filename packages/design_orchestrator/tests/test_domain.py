"""Domain invariant tests — the structural guarantees of the execution plan.

Proves the no-guessing and integrity contracts hold at construction: typed identities, the
token-key choice rules, page ordering as a total order, the rooted component tree with legal
nesting, graph acyclicity and deterministic topological order, review-gate ordering, and the
aggregate's provenance + binding + coverage invariants.
"""

from __future__ import annotations

import dataclasses

import pytest

from design_orchestrator.domain.evidence.evidence import DOEvidence, EvidenceGraph
from design_orchestrator.domain.graph.do_graph import (
    DOEdge,
    DOGraph,
    DONode,
    InvalidDOGraphError,
)
from design_orchestrator.domain.plan.choice import InvalidChoiceError, LayoutRule, SpacingRule
from design_orchestrator.domain.plan.page import InvalidPagePlanError, PagePlan
from design_orchestrator.domain.report.report import (
    DesignExecutionPlan,
    InvalidExecutionPlanError,
)
from design_orchestrator.domain.review.review_plan import (
    InvalidReviewPlanError,
    ReviewCheckpoint,
    ReviewPlan,
)
from design_orchestrator.domain.shared.ids import (
    DOEdgeId,
    DONodeId,
    DesignExecutionPlanId,
    Identifier,
    InvalidDOIdError,
    ReviewCheckpointId,
    SectionPlanId,
)
from design_orchestrator.domain.shared.value_objects import (
    ExecutionStepKind,
    GraphKind,
    GraphRelation,
    LayoutMode,
    NodeKind,
    ReviewGateKind,
)
from design_orchestrator.domain.tree.component_tree import (
    ComponentTree,
    InvalidComponentTreeError,
    TreeNode,
)
from design_orchestrator.domain.shared.value_objects import TreeNodeKind


# --------------------------------------------------------------------------- #
# Identifiers                                                                   #
# --------------------------------------------------------------------------- #
def test_identifiers_are_typed_and_round_trip():
    sid = SectionPlanId.new()
    assert SectionPlanId.from_string(str(sid)) == sid
    assert DONodeId(sid.value) != SectionPlanId(DONodeId.new().value)


def test_abstract_identifier_and_bad_string_rejected():
    import uuid

    with pytest.raises(InvalidDOIdError):
        Identifier(uuid.uuid4())
    with pytest.raises(InvalidDOIdError):
        DesignExecutionPlanId.from_string("not-a-uuid")


# --------------------------------------------------------------------------- #
# Choices                                                                       #
# --------------------------------------------------------------------------- #
def test_choice_rejects_non_token_and_bad_grid():
    with pytest.raises(InvalidChoiceError):
        SpacingRule("NOT A TOKEN", "space.8")
    with pytest.raises(InvalidChoiceError):
        LayoutRule(mode=LayoutMode.GRID, columns=1)  # grid needs >= 2 columns


# --------------------------------------------------------------------------- #
# Page ordering                                                                 #
# --------------------------------------------------------------------------- #
def test_page_orders_must_be_a_total_order(make_section):
    from design_orchestrator.domain.shared.ids import LayoutRegionId, PagePlanId
    from design_orchestrator.domain.shared.value_objects import ComponentType, PageType

    a = make_section(1, ComponentType.HERO)
    b = make_section(1, ComponentType.FOOTER)  # duplicate order
    with pytest.raises(InvalidPagePlanError):
        PagePlan(id=PagePlanId.new(), page_type=PageType.PRODUCT,
                 region_id=LayoutRegionId.new(), sections=(a, b))


# --------------------------------------------------------------------------- #
# Component tree                                                                 #
# --------------------------------------------------------------------------- #
def test_tree_requires_single_root_and_legal_nesting():
    root = TreeNode(DONodeId.new(), TreeNodeKind.ROOT, "root")
    page = TreeNode(DONodeId.new(), TreeNodeKind.PAGE, "product", parent_id=root.id)
    ComponentTree.of([root, page])
    # a COMPONENT directly under ROOT is illegal
    with pytest.raises(InvalidComponentTreeError):
        ComponentTree.of([root, TreeNode(DONodeId.new(), TreeNodeKind.COMPONENT, "x",
                                         parent_id=root.id)])
    # two roots
    with pytest.raises(InvalidComponentTreeError):
        ComponentTree.of([root, TreeNode(DONodeId.new(), TreeNodeKind.ROOT, "root2")])


# --------------------------------------------------------------------------- #
# Graph                                                                         #
# --------------------------------------------------------------------------- #
def test_graph_rejects_cycle_and_orders_deterministically():
    a, b, c = DONodeId.new(), DONodeId.new(), DONodeId.new()
    nodes = [DONode(a, NodeKind.STEP, "a"), DONode(b, NodeKind.STEP, "b"),
             DONode(c, NodeKind.STEP, "c")]
    g = DOGraph.of(GraphKind.EXECUTION, nodes, [
        DOEdge(DOEdgeId.new(), a, b, GraphRelation.PRECEDES),
        DOEdge(DOEdgeId.new(), b, c, GraphRelation.PRECEDES),
    ])
    assert [n.label for n in g.topological_order()] == ["a", "b", "c"]
    with pytest.raises(InvalidDOGraphError):
        DOGraph.of(GraphKind.EXECUTION, nodes, [
            DOEdge(DOEdgeId.new(), a, b, GraphRelation.PRECEDES),
            DOEdge(DOEdgeId.new(), b, a, GraphRelation.PRECEDES),
        ])


# --------------------------------------------------------------------------- #
# Review plan                                                                   #
# --------------------------------------------------------------------------- #
def test_review_plan_requires_pre_generation_last():
    early = ReviewCheckpoint(ReviewCheckpointId.new(), ReviewGateKind.TOKENS_APPROVED,
                             ExecutionStepKind.SETUP_TOKENS, "tokens")
    final = ReviewCheckpoint(ReviewCheckpointId.new(), ReviewGateKind.PRE_GENERATION,
                             ExecutionStepKind.REVIEW_GATE, "final")
    ReviewPlan((early, final))
    with pytest.raises(InvalidReviewPlanError):
        ReviewPlan((final, early))  # pre-generation not last


# --------------------------------------------------------------------------- #
# Aggregate invariants                                                          #
# --------------------------------------------------------------------------- #
def test_aggregate_rejects_variant_drift(built_plan):
    from design_orchestrator.domain.mapping.variant_mapping import VariantChoice, VariantMapping
    from design_orchestrator.domain.shared.value_objects import ComponentType

    plan = built_plan
    section = plan.pages[0].sections[0]
    drifted = VariantMapping(
        {sid: (choice if sid != section.id
               else VariantChoice(section.component, "definitely-not-the-variant"))
         for sid, choice in plan.variant_mapping}
    )
    with pytest.raises(InvalidExecutionPlanError):
        dataclasses.replace(plan, variant_mapping=drifted)


def test_aggregate_rejects_ungrounded_section(built_plan):
    from design_orchestrator.domain.evidence.evidence import Citation
    from design_orchestrator.domain.shared.ids import DOEvidenceId

    plan = built_plan
    page = plan.pages[0]
    section = page.sections[0]
    rogue = dataclasses.replace(
        section, citations=(Citation(evidence_id=DOEvidenceId.new(), relevance="ungrounded"),)
    )
    bad_page = dataclasses.replace(page, sections=(rogue, *page.sections[1:]))
    with pytest.raises(InvalidExecutionPlanError):
        dataclasses.replace(plan, pages=(bad_page, *plan.pages[1:]))


def test_evidence_graph_reports_missing():
    from design_orchestrator.domain.shared.ids import DOEvidenceId
    from design_orchestrator.domain.shared.value_objects import Confidence, ProvenanceKind

    ev = DOEvidence(id=DOEvidenceId.new(), provenance=ProvenanceKind.WIREFRAME,
                    external_ref="w", claim="c", confidence=Confidence.of(0.5))
    graph = EvidenceGraph.of([ev])
    assert graph.missing([ev.id]) == ()
    absent = DOEvidenceId.new()
    assert graph.missing([absent]) == (absent,)
