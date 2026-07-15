"""Domain invariant tests — the structural guarantees of the Figma design model.

Proves the anti-fabrication and integrity contracts hold at construction: typed identities, the
token-first geometry rules, the auto-layout FILL rule, variable mode parity, the tree nesting
rules, graph acyclicity, component-set variant integrity, and the aggregate's provenance +
reference + mapping invariants.
"""

from __future__ import annotations

import dataclasses

import pytest

from figma_design.domain.component.component import FigmaComponent, VariantDefinition
from figma_design.domain.component.component_set import (
    FigmaComponentSet,
    InvalidComponentSetError,
)
from figma_design.domain.component.property import ComponentProperty
from figma_design.domain.geometry.geometry import InvalidGeometryError, Size
from figma_design.domain.graph.fd_graph import FDEdge, FDGraph, FDNode, InvalidFDGraphError
from figma_design.domain.layout.auto_layout import AutoLayout
from figma_design.domain.node.node import FigmaNode, FigmaTree, InvalidTreeError
from figma_design.domain.report.report import FigmaDesignModel, InvalidFigmaModelError
from figma_design.domain.shared.ids import (
    FDEdgeId,
    FDNodeId,
    FigmaComponentId,
    FigmaComponentSetId,
    FigmaDesignModelId,
    FigmaNodeId,
    Identifier,
    InvalidFDIdError,
    VariableId,
)
from figma_design.domain.shared.value_objects import (
    ComponentPropertyType,
    GraphKind,
    GraphRelation,
    LayoutMode,
    NodeKind,
    NodeType,
    SizingMode,
    VariableType,
)
from figma_design.domain.variable.collection import InvalidCollectionError, VariableCollection
from figma_design.domain.variable.variable import Variable, VariableValue
from figma_design.domain.shared.value_objects import CollectionKind
from figma_design.domain.shared.ids import VariableCollectionId


# --------------------------------------------------------------------------- #
# Identifiers                                                                   #
# --------------------------------------------------------------------------- #
def test_identifiers_are_typed_and_round_trip():
    vid = VariableId.new()
    assert VariableId.from_string(str(vid)) == vid
    assert FigmaNodeId(vid.value) != VariableId(FigmaNodeId.new().value)


def test_abstract_identifier_and_bad_string_rejected():
    import uuid

    with pytest.raises(InvalidFDIdError):
        Identifier(uuid.uuid4())
    with pytest.raises(InvalidFDIdError):
        FigmaDesignModelId.from_string("not-a-uuid")


# --------------------------------------------------------------------------- #
# Geometry & auto layout                                                       #
# --------------------------------------------------------------------------- #
def test_size_fixed_requires_px_and_others_forbid_it():
    assert Size.fixed(100).px == 100
    assert Size.fill().px is None
    with pytest.raises(InvalidGeometryError):
        Size(SizingMode.HUG, px=10)
    with pytest.raises(InvalidGeometryError):
        Size(SizingMode.FIXED)


def test_tree_fill_requires_auto_layout_parent():
    root = FigmaNode(id=FigmaNodeId.new(), type=NodeType.FRAME, name="Plain")  # no auto-layout
    from figma_design.domain.node.content import TextContent

    child = FigmaNode(id=FigmaNodeId.new(), type=NodeType.TEXT, name="T", parent_id=root.id,
                      width=Size.fill(), text_content=TextContent("x"))
    with pytest.raises(InvalidTreeError):
        FigmaTree.of([root, child])


def test_tree_component_set_contains_only_components():
    cs_node = FigmaNode(id=FigmaNodeId.new(), type=NodeType.COMPONENT_SET, name="Set")
    text = FigmaNode(id=FigmaNodeId.new(), type=NodeType.TEXT, name="T", parent_id=cs_node.id,
                     text_content=__import__("figma_design.domain.node.content",
                                             fromlist=["TextContent"]).TextContent("x"))
    with pytest.raises(InvalidTreeError):
        FigmaTree.of([cs_node, text])


# --------------------------------------------------------------------------- #
# Variables                                                                     #
# --------------------------------------------------------------------------- #
def test_collection_enforces_mode_parity():
    ok = Variable(id=VariableId.new(), key="color.text", type=VariableType.COLOR,
                  values={"Light": VariableValue.of("#000"), "Dark": VariableValue.of("#fff")})
    VariableCollection.of(VariableCollectionId.new(), CollectionKind.THEME, "Theme",
                          ("Light", "Dark"), [ok])
    bad = Variable(id=VariableId.new(), key="x.y", type=VariableType.COLOR,
                   values={"Light": VariableValue.of("#000")})  # missing Dark
    with pytest.raises(InvalidCollectionError):
        VariableCollection.of(VariableCollectionId.new(), CollectionKind.THEME, "Theme",
                              ("Light", "Dark"), [bad])


# --------------------------------------------------------------------------- #
# Components                                                                     #
# --------------------------------------------------------------------------- #
def test_component_set_variant_integrity():
    prop = ComponentProperty(name="variant", type=ComponentPropertyType.VARIANT,
                             options=("a", "b"), default="a")
    good = FigmaComponent(id=FigmaComponentId.new(), variant=VariantDefinition("a", {"variant": "a"}))
    FigmaComponentSet(id=FigmaComponentSetId.new(), key="card", name="Card",
                      properties=(prop,), components=(good,))
    bad = FigmaComponent(id=FigmaComponentId.new(), variant=VariantDefinition("c", {"variant": "z"}))
    with pytest.raises(InvalidComponentSetError):
        FigmaComponentSet(id=FigmaComponentSetId.new(), key="x", name="X",
                          properties=(prop,), components=(bad,))


# --------------------------------------------------------------------------- #
# Graph                                                                         #
# --------------------------------------------------------------------------- #
def test_graph_rejects_cycle():
    a, b = FDNodeId.new(), FDNodeId.new()
    nodes = [FDNode(a, NodeKind.NODE, "a"), FDNode(b, NodeKind.NODE, "b")]
    FDGraph.of(GraphKind.FIGMA_TREE, nodes, [FDEdge(FDEdgeId.new(), a, b, GraphRelation.CONTAINS)])
    with pytest.raises(InvalidFDGraphError):
        FDGraph.of(GraphKind.FIGMA_TREE, nodes, [
            FDEdge(FDEdgeId.new(), a, b, GraphRelation.CONTAINS),
            FDEdge(FDEdgeId.new(), b, a, GraphRelation.CONTAINS),
        ])


# --------------------------------------------------------------------------- #
# Aggregate invariants                                                          #
# --------------------------------------------------------------------------- #
def test_aggregate_rejects_ungrounded_node(built_model):
    from figma_design.domain.evidence.evidence import Citation
    from figma_design.domain.shared.ids import FDEvidenceId

    model = built_model
    page = model.pages[0]
    node = page.tree.root
    rogue = dataclasses.replace(
        node, citations=(Citation(evidence_id=FDEvidenceId.new(), relevance="ungrounded"),)
    )
    others = [n for n in page.tree if n.id != node.id]
    bad_page = dataclasses.replace(page, tree=FigmaTree.of([rogue, *others]))
    with pytest.raises(InvalidFigmaModelError):
        dataclasses.replace(model, pages=(bad_page, *model.pages[1:]))


def test_aggregate_variant_mapping_matches_instances(built_model):
    # Every instance node has a variant-mapping entry (guaranteed by construction).
    model = built_model
    instances = [
        n for page in model.pages for n in page.tree if n.type is NodeType.INSTANCE
    ]
    assert instances
    for inst in instances:
        assert model.variant_mapping.has(inst.id)


def test_evidence_graph_reports_missing():
    from figma_design.domain.evidence.evidence import EvidenceGraph, FDEvidence
    from figma_design.domain.shared.ids import FDEvidenceId
    from figma_design.domain.shared.value_objects import Confidence, ProvenanceKind

    ev = FDEvidence(id=FDEvidenceId.new(), provenance=ProvenanceKind.DESIGN_SYSTEM,
                    external_ref="d", claim="c", confidence=Confidence.of(0.5))
    graph = EvidenceGraph.of([ev])
    assert graph.missing([ev.id]) == ()
    absent = FDEvidenceId.new()
    assert graph.missing([absent]) == (absent,)
