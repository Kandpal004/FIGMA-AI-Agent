"""Serializable view DTOs — the model projected for transport.

The facade never returns domain aggregates; it returns these flat, immutable views. They project a
:class:`FigmaDesignModel` (and the neutral :class:`FigmaDesignBundle`) into plain ``dict``-friendly
structures an API, the orchestration layer, or a future Figma/MCP renderer can serialize — carrying
the organized pages and their layer trees, the variable collections, the styles, the component-set
catalog, the token/variant mappings, and the five graphs, but no domain objects and no rendered
Figma.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from figma_design.domain.graph.fd_graph import FDGraph
from figma_design.domain.node.node import FigmaNode
from figma_design.domain.page.page import FigmaPage
from figma_design.domain.report.bundle import FigmaDesignBundle
from figma_design.domain.report.report import FigmaDesignModel
from figma_design.domain.variable.collection import VariableCollection

__all__ = [
    "FigmaDesignBundleView",
    "FigmaModelView",
    "GraphView",
    "PageView",
    "QualityView",
    "TraceView",
]


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _ids(ids) -> list[str]:
    return [str(i) for i in ids]


def _node_view(n: FigmaNode) -> dict:
    return {
        "id": str(n.id),
        "type": n.type.value,
        "name": n.name,
        "parent_id": str(n.parent_id) if n.parent_id is not None else None,
        "order": n.order,
        "width": {"mode": n.width.mode.value, "px": n.width.px},
        "height": {"mode": n.height.mode.value, "px": n.height.px},
        "auto_layout": (
            {
                "mode": n.auto_layout.mode.value,
                "primary_axis_sizing": n.auto_layout.primary_axis_sizing.value,
                "counter_axis_sizing": n.auto_layout.counter_axis_sizing.value,
                "primary_align": n.auto_layout.primary_align.value,
                "counter_align": n.auto_layout.counter_align.value,
                "item_spacing_token": n.auto_layout.item_spacing_token,
                "padding": {
                    "top": n.auto_layout.padding.top, "right": n.auto_layout.padding.right,
                    "bottom": n.auto_layout.padding.bottom, "left": n.auto_layout.padding.left,
                },
                "wrap": n.auto_layout.wrap,
            }
            if n.auto_layout is not None
            else None
        ),
        "constraint": (
            {"horizontal": n.constraint.horizontal.value, "vertical": n.constraint.vertical.value}
            if n.constraint is not None
            else None
        ),
        "corner_radius": n.corner_radius.token if n.corner_radius is not None else None,
        "fill_style_ref": str(n.fill_style_ref) if n.fill_style_ref is not None else None,
        "effect_style_ref": str(n.effect_style_ref) if n.effect_style_ref is not None else None,
        "variable_bindings": [
            {"property": b.property, "variable_key": b.variable_key}
            for b in n.variable_bindings
        ],
        "text": n.text_content.characters if n.text_content is not None else None,
        "image_ref": n.image_ref.image_ref if n.image_ref is not None else None,
        "instance": (
            {
                "component_set_id": str(n.instance_ref.component_set_id),
                "variant_name": n.instance_ref.variant_name,
                "property_overrides": dict(n.instance_ref.property_overrides),
            }
            if n.instance_ref is not None
            else None
        ),
        "developer_notes": [{"label": d.label, "body": d.body} for d in n.developer_notes],
        "evidence_ids": _ids(n.evidence_ids),
    }


def _page_view(p: FigmaPage) -> dict:
    return {
        "id": str(p.id),
        "kind": p.kind.value,
        "name": p.name,
        "order": p.order,
        "nodes": [_node_view(n) for n in p.tree],
    }


def _collection_view(c: VariableCollection) -> dict:
    return {
        "id": str(c.id),
        "kind": c.kind.value,
        "name": c.name,
        "modes": list(c.modes),
        "variables": [
            {
                "id": str(v.id),
                "key": v.key,
                "type": v.type.value,
                "scopes": sorted(s.value for s in v.scopes),
                "values": {
                    mode: {"literal": val.literal, "ref": val.ref}
                    for mode, val in v.values.items()
                },
            }
            for v in c
        ],
    }


def _style_view(model: FigmaDesignModel) -> list[dict]:
    views: list[dict] = []
    for style in model.style_set:
        views.append({
            "id": str(style.id),
            "name": style.name,
            "type": style.type.value,
            "paints": [
                {"type": p.type.value, "color_token": p.color_token, "opacity": p.opacity}
                for p in style.paints
            ],
            "typography": (
                {
                    "font_family": style.typography.font_family,
                    "font_weight": style.typography.font_weight,
                    "font_size_token": style.typography.font_size_token,
                    "line_height": style.typography.line_height,
                }
                if style.typography is not None
                else None
            ),
            "effects": [
                {"type": e.type.value, "radius": e.radius, "color_token": e.color_token}
                for e in style.effects
            ],
            "grid_columns": style.grid_columns,
        })
    return views


def _component_set_view(model: FigmaDesignModel) -> list[dict]:
    views: list[dict] = []
    for cs in model.component_sets:
        views.append({
            "id": str(cs.id),
            "key": cs.key,
            "name": cs.name,
            "properties": [
                {"name": p.name, "type": p.type.value, "options": list(p.options),
                 "default": p.default}
                for p in cs.properties
            ],
            "variants": [
                {"name": c.name, "property_values": dict(c.variant.property_values)}
                for c in cs.components
            ],
            "evidence_ids": _ids(cs.evidence_ids),
        })
    return views


def _graph_view(g: FDGraph) -> dict:
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


def _token_mapping_view(model: FigmaDesignModel) -> dict:
    return {str(nid): list(keys) for nid, keys in model.token_mapping}


def _variant_mapping_view(model: FigmaDesignModel) -> dict:
    return {
        str(nid): {"component_set_key": sel.component_set_key, "variant_name": sel.variant_name}
        for nid, sel in model.variant_mapping
    }


def _source_refs_view(model: FigmaDesignModel) -> dict:
    sr = model.source_refs
    return {
        "execution_plan_id": sr.execution_plan_id,
        "design_system_spec_id": sr.design_system_spec_id,
        "component_spec_id": sr.component_spec_id,
        "design_language_spec_id": sr.design_language_spec_id,
        "creative_director_review_id": sr.creative_director_review_id,
    }


@dataclass(frozen=True, slots=True)
class QualityView:
    overall_score: float
    band: str
    reference_integrity: float
    mode_parity: float
    structure: float
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
class FigmaModelView:
    """The full, flat projection of a Figma design model."""

    model_id: str
    lineage_id: str
    version: int
    project_id: str
    is_production_ready: bool
    created_at: str
    source_refs: dict
    quality: QualityView
    pages: list[dict]
    collections: list[dict]
    styles: list[dict]
    component_sets: list[dict]
    token_mapping: dict
    variant_mapping: dict
    graphs: dict
    page_count: int
    node_count: int
    variable_count: int
    component_set_count: int
    evidence_count: int

    @classmethod
    def from_model(cls, model: FigmaDesignModel) -> FigmaModelView:
        quality = QualityView(
            overall_score=model.quality.overall_score.value,
            band=model.quality.band.value,
            reference_integrity=model.quality.reference_integrity.value,
            mode_parity=model.quality.mode_parity.value,
            structure=model.quality.structure.value,
            grounding=model.quality.grounding.value,
            confidence=model.quality.confidence.value,
            is_fully_grounded=model.quality.is_fully_grounded,
        )
        return cls(
            model_id=str(model.id),
            lineage_id=str(model.lineage_id),
            version=model.version,
            project_id=model.project_id,
            is_production_ready=model.is_production_ready,
            created_at=_iso(model.created_at),
            source_refs=_source_refs_view(model),
            quality=quality,
            pages=[_page_view(p) for p in model.pages],
            collections=[_collection_view(c) for c in model.collections],
            styles=_style_view(model),
            component_sets=_component_set_view(model),
            token_mapping=_token_mapping_view(model),
            variant_mapping=_variant_mapping_view(model),
            graphs={g.kind.value: _graph_view(g) for g in model.graphs.all},
            page_count=model.page_count(),
            node_count=model.node_count(),
            variable_count=model.variable_count(),
            component_set_count=model.component_set_count(),
            evidence_count=model.evidence_count(),
        )


@dataclass(frozen=True, slots=True)
class FigmaDesignBundleView:
    """The neutral Figma design model a downstream renderer consumes."""

    model_id: str
    project_id: str
    is_production_ready: bool
    created_at: str
    source_refs: dict
    pages: list[dict]
    collections: list[dict]
    styles: list[dict]
    component_sets: list[dict]
    token_mapping: dict
    variant_mapping: dict

    @classmethod
    def from_bundle(
        cls, bundle: FigmaDesignBundle, model: FigmaDesignModel
    ) -> FigmaDesignBundleView:
        return cls(
            model_id=str(bundle.model_id),
            project_id=bundle.project_id,
            is_production_ready=bundle.is_production_ready,
            created_at=_iso(bundle.created_at),
            source_refs=_source_refs_view(model),
            pages=[_page_view(p) for p in bundle.pages],
            collections=[_collection_view(c) for c in bundle.collections],
            styles=_style_view(model),
            component_sets=_component_set_view(model),
            token_mapping=_token_mapping_view(model),
            variant_mapping=_variant_mapping_view(model),
        )


@dataclass(frozen=True, slots=True)
class TraceView:
    """An explanation of one graph node: the node, its successors, and its evidence."""

    node: dict
    successors: list[dict]
    evidence: list[dict]
