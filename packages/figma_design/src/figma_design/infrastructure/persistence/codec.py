"""Codec — serializes a FigmaDesignModel to a JSON document and back.

A model is a deep, immutable aggregate; it is stored and loaded whole as one JSON document. This
codec is the single, exhaustive translation. Reconstruction goes through the normal aggregate
constructor, so a decoded model is re-validated (its provenance and reference integrity re-checked,
its trees and graphs re-checked, its mode parity re-enforced) — a corrupt document cannot yield an
inconsistent or ungrounded model.

Pure functions, no I/O. Imports no Figma SDK, MCP client, or HTTP library.
"""

from __future__ import annotations

from datetime import datetime

from figma_design.domain.component.component import FigmaComponent, VariantDefinition
from figma_design.domain.component.component_set import ComponentSetCatalog, FigmaComponentSet
from figma_design.domain.component.property import ComponentProperty
from figma_design.domain.context.context import SourceRefs
from figma_design.domain.evidence.evidence import Citation, EvidenceGraph, FDEvidence
from figma_design.domain.geometry.geometry import CornerRadius, Padding, Size
from figma_design.domain.graph.fd_graph import FDEdge, FDGraph, FDNode
from figma_design.domain.graph.graphs import FigmaGraphs
from figma_design.domain.layout.auto_layout import AutoLayout
from figma_design.domain.layout.constraint import LayoutConstraint
from figma_design.domain.mapping.token_mapping import TokenMapping
from figma_design.domain.mapping.variant_mapping import InstanceSelection, VariantMapping
from figma_design.domain.node.annotation import Annotation, Comment, DeveloperNote
from figma_design.domain.node.content import ImageRef, InstanceRef, TextContent
from figma_design.domain.node.node import FigmaNode, FigmaTree
from figma_design.domain.page.page import FigmaPage
from figma_design.domain.quality.quality import FigmaModelQualityMetrics
from figma_design.domain.report.report import FigmaDesignModel
from figma_design.domain.shared.ids import (
    FDEdgeId,
    FDEvidenceId,
    FDNodeId,
    FigmaComponentId,
    FigmaComponentSetId,
    FigmaDesignModelId,
    FigmaDesignModelLineageId,
    FigmaNodeId,
    FigmaPageId,
    StyleId,
    VariableCollectionId,
    VariableId,
)
from figma_design.domain.shared.value_objects import (
    AxisAlign,
    BlendMode,
    CollectionKind,
    ComponentPropertyType,
    Confidence,
    EffectType,
    FigmaPageKind,
    GraphKind,
    GraphRelation,
    LayoutConstraintKind,
    LayoutMode,
    NodeKind,
    NodeType,
    PaintType,
    Percentage,
    ProvenanceKind,
    SizingMode,
    StyleType,
    Tag,
    VariableScope,
    VariableType,
)
from figma_design.domain.style.paint import Effect, Paint
from figma_design.domain.style.style import Style, StyleSet
from figma_design.domain.style.typography import TypographyStyle
from figma_design.domain.variable.binding import VariableBinding
from figma_design.domain.variable.collection import VariableCollection
from figma_design.domain.variable.variable import Variable, VariableValue

__all__ = ["from_document", "to_document"]


def _ids(ids) -> list[str]:
    return [str(i) for i in ids]


def _citations_doc(citations) -> list[dict]:
    return [{"evidence_id": str(c.evidence_id), "relevance": c.relevance} for c in citations]


# --------------------------------------------------------------------------- #
# Encode                                                                       #
# --------------------------------------------------------------------------- #
def _size_doc(s: Size) -> dict:
    return {"mode": s.mode.value, "px": s.px}


def _auto_layout_doc(a: AutoLayout) -> dict:
    return {
        "mode": a.mode.value,
        "primary_axis_sizing": a.primary_axis_sizing.value,
        "counter_axis_sizing": a.counter_axis_sizing.value,
        "primary_align": a.primary_align.value,
        "counter_align": a.counter_align.value,
        "item_spacing_token": a.item_spacing_token,
        "padding": {"top": a.padding.top, "right": a.padding.right,
                    "bottom": a.padding.bottom, "left": a.padding.left},
        "wrap": a.wrap,
    }


def _node_doc(n: FigmaNode) -> dict:
    return {
        "id": str(n.id), "type": n.type.value, "name": n.name,
        "parent_id": str(n.parent_id) if n.parent_id is not None else None,
        "order": n.order,
        "width": _size_doc(n.width), "height": _size_doc(n.height),
        "auto_layout": _auto_layout_doc(n.auto_layout) if n.auto_layout is not None else None,
        "constraint": (
            {"horizontal": n.constraint.horizontal.value, "vertical": n.constraint.vertical.value}
            if n.constraint is not None else None
        ),
        "corner_radius": n.corner_radius.token if n.corner_radius is not None else None,
        "fill_style_ref": str(n.fill_style_ref) if n.fill_style_ref is not None else None,
        "effect_style_ref": str(n.effect_style_ref) if n.effect_style_ref is not None else None,
        "variable_bindings": [
            {"property": b.property, "variable_key": b.variable_key} for b in n.variable_bindings
        ],
        "text_content": (
            {"characters": n.text_content.characters,
             "text_style_ref": str(n.text_content.text_style_ref)
             if n.text_content.text_style_ref is not None else None}
            if n.text_content is not None else None
        ),
        "image_ref": (
            {"image_ref": n.image_ref.image_ref, "alt": n.image_ref.alt}
            if n.image_ref is not None else None
        ),
        "instance_ref": (
            {"component_set_id": str(n.instance_ref.component_set_id),
             "variant_name": n.instance_ref.variant_name,
             "property_overrides": dict(n.instance_ref.property_overrides)}
            if n.instance_ref is not None else None
        ),
        "developer_notes": [{"label": d.label, "body": d.body} for d in n.developer_notes],
        "comments": [{"author": c.author, "body": c.body} for c in n.comments],
        "annotations": [{"property": a.property, "value": a.value} for a in n.annotations],
        "citations": _citations_doc(n.citations),
    }


def _page_doc(p: FigmaPage) -> dict:
    return {
        "id": str(p.id), "kind": p.kind.value, "name": p.name, "order": p.order,
        "nodes": [_node_doc(n) for n in p.tree],
    }


def _collection_doc(c: VariableCollection) -> dict:
    return {
        "id": str(c.id), "kind": c.kind.value, "name": c.name, "modes": list(c.modes),
        "variables": [
            {"id": str(v.id), "key": v.key, "type": v.type.value,
             "scopes": sorted(s.value for s in v.scopes), "description": v.description,
             "values": {mode: {"literal": val.literal, "ref": val.ref}
                        for mode, val in v.values.items()}}
            for v in c
        ],
    }


def _style_doc(s: Style) -> dict:
    return {
        "id": str(s.id), "name": s.name, "type": s.type.value,
        "paints": [{"type": p.type.value, "color_token": p.color_token, "opacity": p.opacity,
                    "blend_mode": p.blend_mode.value, "image_ref": p.image_ref} for p in s.paints],
        "typography": (
            {"font_family": s.typography.font_family, "font_weight": s.typography.font_weight,
             "font_size_token": s.typography.font_size_token,
             "line_height": s.typography.line_height,
             "letter_spacing": s.typography.letter_spacing, "text_case": s.typography.text_case}
            if s.typography is not None else None
        ),
        "effects": [{"type": e.type.value, "radius": e.radius, "color_token": e.color_token,
                     "offset_x": e.offset_x, "offset_y": e.offset_y} for e in s.effects],
        "grid_columns": s.grid_columns, "description": s.description,
    }


def _component_set_doc(cs: FigmaComponentSet) -> dict:
    return {
        "id": str(cs.id), "key": cs.key, "name": cs.name,
        "properties": [{"name": p.name, "type": p.type.value, "options": list(p.options),
                        "default": p.default} for p in cs.properties],
        "components": [{"id": str(c.id), "name": c.name,
                        "property_values": dict(c.variant.property_values),
                        "root_node_id": str(c.root_node_id) if c.root_node_id is not None else None}
                       for c in cs.components],
        "citations": _citations_doc(cs.citations),
    }


def _graph_doc(g: FDGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [{"id": str(n.id), "kind": n.kind.value, "label": n.label,
                   "evidence_ids": _ids(n.evidence_ids)} for n in g],
        "edges": [{"id": str(e.id), "source": str(e.source), "target": str(e.target),
                   "relation": e.relation.value} for e in g.edges],
    }


def to_document(model: FigmaDesignModel) -> dict:
    """Serialize a model to a JSON-safe document."""
    sr = model.source_refs
    return {
        "id": str(model.id), "lineage_id": str(model.lineage_id), "version": model.version,
        "project_id": model.project_id, "created_at": model.created_at.isoformat(),
        "source_refs": {
            "execution_plan_id": sr.execution_plan_id,
            "design_system_spec_id": sr.design_system_spec_id,
            "component_spec_id": sr.component_spec_id,
            "design_language_spec_id": sr.design_language_spec_id,
            "creative_director_review_id": sr.creative_director_review_id,
        },
        "pages": [_page_doc(p) for p in model.pages],
        "collections": [_collection_doc(c) for c in model.collections],
        "styles": [_style_doc(s) for s in model.style_set],
        "component_sets": [_component_set_doc(cs) for cs in model.component_sets],
        "token_mapping": {str(nid): list(keys) for nid, keys in model.token_mapping},
        "variant_mapping": {
            str(nid): {"component_set_key": sel.component_set_key, "variant_name": sel.variant_name}
            for nid, sel in model.variant_mapping
        },
        "graphs": [_graph_doc(g) for g in model.graphs.all],
        "evidence": [
            {"id": str(e.id), "provenance": e.provenance.value, "external_ref": e.external_ref,
             "claim": e.claim, "confidence": e.confidence.value, "statement": e.statement,
             "source_name": e.source_name, "tags": sorted(t.value for t in e.tags)}
            for e in model.evidence_graph
        ],
        "quality": {
            "reference_integrity": model.quality.reference_integrity.value,
            "mode_parity": model.quality.mode_parity.value,
            "structure": model.quality.structure.value,
            "grounding": model.quality.grounding.value,
            "confidence": model.quality.confidence.value,
        },
    }


# --------------------------------------------------------------------------- #
# Decode                                                                       #
# --------------------------------------------------------------------------- #
def _ev_ids(raw) -> tuple[FDEvidenceId, ...]:
    return tuple(FDEvidenceId.from_string(i) for i in raw)


def _citations(raw) -> tuple[Citation, ...]:
    return tuple(
        Citation(evidence_id=FDEvidenceId.from_string(c["evidence_id"]), relevance=c["relevance"])
        for c in raw
    )


def _size(doc: dict) -> Size:
    return Size(mode=SizingMode(doc["mode"]), px=doc["px"])


def _auto_layout(doc: dict) -> AutoLayout:
    p = doc["padding"]
    return AutoLayout(
        mode=LayoutMode(doc["mode"]),
        primary_axis_sizing=SizingMode(doc["primary_axis_sizing"]),
        counter_axis_sizing=SizingMode(doc["counter_axis_sizing"]),
        primary_align=AxisAlign(doc["primary_align"]),
        counter_align=AxisAlign(doc["counter_align"]),
        item_spacing_token=doc["item_spacing_token"],
        padding=Padding(top=p["top"], right=p["right"], bottom=p["bottom"], left=p["left"]),
        wrap=doc["wrap"],
    )


def _node(doc: dict) -> FigmaNode:
    tc = doc["text_content"]
    ir = doc["image_ref"]
    inst = doc["instance_ref"]
    return FigmaNode(
        id=FigmaNodeId.from_string(doc["id"]),
        type=NodeType(doc["type"]),
        name=doc["name"],
        parent_id=FigmaNodeId.from_string(doc["parent_id"]) if doc["parent_id"] else None,
        order=doc["order"],
        width=_size(doc["width"]),
        height=_size(doc["height"]),
        auto_layout=_auto_layout(doc["auto_layout"]) if doc["auto_layout"] else None,
        constraint=(
            LayoutConstraint(horizontal=LayoutConstraintKind(doc["constraint"]["horizontal"]),
                             vertical=LayoutConstraintKind(doc["constraint"]["vertical"]))
            if doc["constraint"] else None
        ),
        corner_radius=CornerRadius(doc["corner_radius"]) if doc["corner_radius"] else None,
        fill_style_ref=StyleId.from_string(doc["fill_style_ref"]) if doc["fill_style_ref"] else None,
        effect_style_ref=(
            StyleId.from_string(doc["effect_style_ref"]) if doc["effect_style_ref"] else None
        ),
        variable_bindings=tuple(
            VariableBinding(property=b["property"], variable_key=b["variable_key"])
            for b in doc["variable_bindings"]
        ),
        text_content=(
            TextContent(characters=tc["characters"],
                        text_style_ref=StyleId.from_string(tc["text_style_ref"])
                        if tc["text_style_ref"] else None)
            if tc else None
        ),
        image_ref=ImageRef(image_ref=ir["image_ref"], alt=ir["alt"]) if ir else None,
        instance_ref=(
            InstanceRef(component_set_id=FigmaComponentSetId.from_string(inst["component_set_id"]),
                        variant_name=inst["variant_name"],
                        property_overrides=dict(inst["property_overrides"]))
            if inst else None
        ),
        developer_notes=tuple(
            DeveloperNote(label=d["label"], body=d["body"]) for d in doc["developer_notes"]
        ),
        comments=tuple(Comment(author=c["author"], body=c["body"]) for c in doc["comments"]),
        annotations=tuple(
            Annotation(property=a["property"], value=a["value"]) for a in doc["annotations"]
        ),
        citations=_citations(doc["citations"]),
    )


def _page(doc: dict) -> FigmaPage:
    return FigmaPage(
        id=FigmaPageId.from_string(doc["id"]),
        kind=FigmaPageKind(doc["kind"]),
        name=doc["name"],
        order=doc["order"],
        tree=FigmaTree.of(_node(n) for n in doc["nodes"]),
    )


def _value(doc: dict) -> VariableValue:
    return VariableValue.of(doc["literal"]) if doc["literal"] is not None else VariableValue.alias(
        doc["ref"]
    )


def _collection(doc: dict) -> VariableCollection:
    variables = [
        Variable(
            id=VariableId.from_string(v["id"]), key=v["key"], type=VariableType(v["type"]),
            values={mode: _value(val) for mode, val in v["values"].items()},
            scopes=frozenset(VariableScope(s) for s in v["scopes"]),
            description=v.get("description", ""),
        )
        for v in doc["variables"]
    ]
    return VariableCollection.of(
        VariableCollectionId.from_string(doc["id"]), CollectionKind(doc["kind"]), doc["name"],
        tuple(doc["modes"]), variables,
    )


def _style(doc: dict) -> Style:
    ty = doc["typography"]
    return Style(
        id=StyleId.from_string(doc["id"]), name=doc["name"], type=StyleType(doc["type"]),
        paints=tuple(
            Paint(type=PaintType(p["type"]), color_token=p["color_token"], opacity=p["opacity"],
                  blend_mode=BlendMode(p["blend_mode"]), image_ref=p["image_ref"])
            for p in doc["paints"]
        ),
        typography=(
            TypographyStyle(font_family=ty["font_family"], font_weight=ty["font_weight"],
                            font_size_token=ty["font_size_token"], line_height=ty["line_height"],
                            letter_spacing=ty["letter_spacing"], text_case=ty["text_case"])
            if ty else None
        ),
        effects=tuple(
            Effect(type=EffectType(e["type"]), radius=e["radius"], color_token=e["color_token"],
                   offset_x=e["offset_x"], offset_y=e["offset_y"])
            for e in doc["effects"]
        ),
        grid_columns=doc["grid_columns"], description=doc.get("description", ""),
    )


def _component_set(doc: dict) -> FigmaComponentSet:
    return FigmaComponentSet(
        id=FigmaComponentSetId.from_string(doc["id"]), key=doc["key"], name=doc["name"],
        properties=tuple(
            ComponentProperty(name=p["name"], type=ComponentPropertyType(p["type"]),
                              options=tuple(p["options"]), default=p["default"])
            for p in doc["properties"]
        ),
        components=tuple(
            FigmaComponent(
                id=FigmaComponentId.from_string(c["id"]),
                variant=VariantDefinition(name=c["name"], property_values=dict(c["property_values"])),
                root_node_id=FigmaNodeId.from_string(c["root_node_id"]) if c["root_node_id"] else None,
            )
            for c in doc["components"]
        ),
        citations=_citations(doc["citations"]),
    )


def _graph(doc: dict) -> FDGraph:
    return FDGraph.of(
        GraphKind(doc["kind"]),
        [FDNode(id=FDNodeId.from_string(n["id"]), kind=NodeKind(n["kind"]), label=n["label"],
                evidence_ids=_ev_ids(n["evidence_ids"])) for n in doc["nodes"]],
        [FDEdge(id=FDEdgeId.from_string(e["id"]), source=FDNodeId.from_string(e["source"]),
                target=FDNodeId.from_string(e["target"]), relation=GraphRelation(e["relation"]))
         for e in doc["edges"]],
    )


def from_document(doc: dict) -> FigmaDesignModel:
    """Reconstruct a model from its document, re-validating every invariant."""
    sr = doc["source_refs"]
    q = doc["quality"]
    graphs_by_kind = {GraphKind(g["kind"]): _graph(g) for g in doc["graphs"]}
    token_mapping = TokenMapping(
        {FigmaNodeId.from_string(nid): tuple(keys) for nid, keys in doc["token_mapping"].items()}
    )
    variant_mapping = VariantMapping(
        {FigmaNodeId.from_string(nid): InstanceSelection(
            component_set_key=v["component_set_key"], variant_name=v["variant_name"])
         for nid, v in doc["variant_mapping"].items()}
    )
    return FigmaDesignModel(
        id=FigmaDesignModelId.from_string(doc["id"]),
        lineage_id=FigmaDesignModelLineageId.from_string(doc["lineage_id"]),
        version=doc["version"],
        project_id=doc["project_id"],
        source_refs=SourceRefs(
            execution_plan_id=sr["execution_plan_id"],
            design_system_spec_id=sr["design_system_spec_id"],
            component_spec_id=sr["component_spec_id"],
            design_language_spec_id=sr["design_language_spec_id"],
            creative_director_review_id=sr["creative_director_review_id"],
        ),
        pages=tuple(_page(p) for p in doc["pages"]),
        collections=tuple(_collection(c) for c in doc["collections"]),
        style_set=StyleSet.of(_style(s) for s in doc["styles"]),
        component_sets=ComponentSetCatalog.of(_component_set(cs) for cs in doc["component_sets"]),
        token_mapping=token_mapping,
        variant_mapping=variant_mapping,
        graphs=FigmaGraphs(
            figma_tree=graphs_by_kind[GraphKind.FIGMA_TREE],
            component=graphs_by_kind[GraphKind.COMPONENT],
            auto_layout=graphs_by_kind[GraphKind.AUTO_LAYOUT],
            variable=graphs_by_kind[GraphKind.VARIABLE],
            style=graphs_by_kind[GraphKind.STYLE],
        ),
        evidence_graph=EvidenceGraph.of(
            FDEvidence(id=FDEvidenceId.from_string(e["id"]),
                       provenance=ProvenanceKind(e["provenance"]), external_ref=e["external_ref"],
                       claim=e["claim"], confidence=Confidence(e["confidence"]),
                       statement=e.get("statement", ""), source_name=e.get("source_name", ""),
                       tags=frozenset(Tag.of(t) for t in e.get("tags", ())))
            for e in doc["evidence"]
        ),
        quality=FigmaModelQualityMetrics(
            reference_integrity=Percentage(q["reference_integrity"]),
            mode_parity=Percentage(q["mode_parity"]),
            structure=Percentage(q["structure"]),
            grounding=Percentage(q["grounding"]),
            confidence=Confidence(q["confidence"]),
        ),
        created_at=datetime.fromisoformat(doc["created_at"]),
    )
