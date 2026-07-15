"""Serializable view DTOs — the specification projected for transport.

The facade never returns domain aggregates; it returns these flat, immutable views. They project
a :class:`DesignSystemSpecification` (and the neutral :class:`DesignSystemBundle`) into plain
``dict``-friendly structures an API, the orchestration layer, or a future UI/Figma engine can
serialize — carrying the full design system (the three-tier tokens, the scales and systems, the
per-component specs with variants/states/responsive/accessibility/performance and the
developer/Shopify/Magento mappings, the themes, the localization contract, the constraints, and
the six graphs) but no domain objects and no UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from design_system.domain.component.spec import ComponentSpec
from design_system.domain.graph.ds_graph import DSGraph
from design_system.domain.report.bundle import DesignSystemBundle
from design_system.domain.report.report import DesignSystemSpecification
from design_system.domain.token.token import DesignToken

__all__ = [
    "ComponentView",
    "DesignSystemBundleView",
    "GraphView",
    "QualityView",
    "SpecificationView",
    "TraceView",
]


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _ids(ids) -> list[str]:
    return [str(i) for i in ids]


def _token_view(t: DesignToken) -> dict:
    return {
        "key": t.key,
        "category": t.category.value,
        "tier": t.tier.value,
        "value": {"literal": t.value.literal, "ref": t.value.ref},
        "description": t.description,
        "evidence_ids": _ids(t.evidence_ids),
    }


def _component_view(s: ComponentSpec) -> dict:
    return {
        "component": s.component.value,
        "atomic_level": s.atomic_level.value,
        "token_refs": list(s.token_refs),
        "properties": [
            {
                "name": p.name,
                "type": p.type.value,
                "options": list(p.options),
                "default": p.default,
                "required": p.required,
            }
            for p in s.properties
        ],
        "variants": [
            {"name": v.name, "property_values": dict(v.property_values),
             "description": v.description}
            for v in s.variants
        ],
        "states": [
            {"state": st.state.value, "token_refs": dict(st.token_refs)}
            for st in s.states.states
        ],
        "responsive": {bp.value: note for bp, note in s.responsive.behavior.items()},
        "accessibility": {
            "role": s.accessibility.role,
            "keyboard": list(s.accessibility.keyboard),
            "min_contrast": s.accessibility.min_contrast,
            "focus_visible": s.accessibility.focus_visible,
            "notes": s.accessibility.notes,
        },
        "performance": {
            "lazy_load": s.performance.lazy_load,
            "max_dom_nodes": s.performance.max_dom_nodes,
            "blocks_lcp": s.performance.blocks_lcp,
            "notes": s.performance.notes,
        },
        "mappings": {
            platform.value: {
                "primitive": m.primitive,
                "identifier": m.identifier,
                "settings": list(m.settings),
                "capabilities": list(m.capabilities),
                "notes": m.notes,
            }
            for platform, m in s.mappings.items()
        },
        "evidence_ids": _ids(s.evidence_ids),
    }


def _scales_view(spec: DesignSystemSpecification) -> dict:
    return {
        "typography": {
            "base_px": spec.typography.base_px,
            "ratio": spec.typography.ratio.value,
            "role_tokens": list(spec.typography.role_tokens),
        },
        "spacing": {
            "base_px": spec.spacing.base_px,
            "step_tokens": list(spec.spacing.step_tokens),
        },
        "radius": {"step_tokens": list(spec.radius.step_tokens)},
        "elevation": {"level_tokens": list(spec.elevation.level_tokens)},
        "shadow": {"step_tokens": list(spec.shadow.step_tokens)},
        "border": {"width_tokens": list(spec.border.width_tokens)},
    }


def _systems_view(spec: DesignSystemSpecification) -> dict:
    return {
        "breakpoints": {bp.value: w for bp, w in spec.breakpoints.min_width_px.items()},
        "grid": {
            "columns": {bp.value: c for bp, c in spec.grid.columns.items()},
            "gutter_tokens": {bp.value: g for bp, g in spec.grid.gutter_tokens.items()},
        },
        "container": {bp.value: w for bp, w in spec.container.max_width_px.items()},
        "motion": {
            "duration_tokens": list(spec.motion.duration_tokens),
            "easing_tokens": list(spec.motion.easing_tokens),
        },
        "interaction": {
            "focus_ring_token": spec.interaction.focus_ring_token,
            "hit_target_token": spec.interaction.hit_target_token,
            "transition_token": spec.interaction.transition_token,
        },
    }


def _states_view(spec: DesignSystemSpecification) -> list[dict]:
    return [
        {"state": s.state.value, "token_refs": dict(s.token_refs)} for s in spec.states
    ]


def _themes_view(spec: DesignSystemSpecification) -> list[dict]:
    return [
        {"mode": t.mode.value, "name": t.name, "overrides": dict(t.overrides)}
        for t in spec.theme_set
    ]


def _localization_view(spec: DesignSystemSpecification) -> dict:
    return {
        "directions": [d.value for d in spec.localization.directions],
        "locales": list(spec.localization.locales),
        "mirror_properties": list(spec.localization.mirror_properties),
        "supports_rtl": spec.localization.supports_rtl,
    }


def _constraints_view(spec: DesignSystemSpecification) -> list[dict]:
    return [
        {
            "kind": c.kind.value,
            "enforcement": c.enforcement.value,
            "statement": c.statement,
            "rationale": c.rationale,
            "parameters": dict(c.parameters),
            "evidence_ids": _ids(c.evidence_ids),
        }
        for c in spec.constraint_set
    ]


def _graph_view(g: DSGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [
            {"id": str(n.id), "kind": n.kind.value, "label": n.label,
             "evidence_ids": _ids(n.evidence_ids)}
            for n in g
        ],
        "edges": [
            {"source": str(e.source), "target": str(e.target), "relation": e.relation.value}
            for e in g.edges
        ],
    }


@dataclass(frozen=True, slots=True)
class QualityView:
    overall_score: float
    band: str
    token_integrity: float
    component_coverage: float
    theme_parity: float
    grounding: float
    confidence: float
    is_fully_grounded: bool


@dataclass(frozen=True, slots=True)
class ComponentView:
    component: dict


@dataclass(frozen=True, slots=True)
class GraphView:
    graph: dict


@dataclass(frozen=True, slots=True)
class SpecificationView:
    """The full, flat projection of a design-system specification."""

    spec_id: str
    lineage_id: str
    version: int
    project_id: str
    is_production_ready: bool
    created_at: str
    quality: QualityView
    tokens: list[dict]
    scales: dict
    systems: dict
    states: list[dict]
    components: list[dict]
    themes: list[dict]
    localization: dict
    constraints: list[dict]
    graphs: dict
    token_count: int
    component_count: int
    evidence_count: int

    @classmethod
    def from_specification(cls, spec: DesignSystemSpecification) -> SpecificationView:
        quality = QualityView(
            overall_score=spec.quality.overall_score.value,
            band=spec.quality.band.value,
            token_integrity=spec.quality.token_integrity.value,
            component_coverage=spec.quality.component_coverage.value,
            theme_parity=spec.quality.theme_parity.value,
            grounding=spec.quality.grounding.value,
            confidence=spec.quality.confidence.value,
            is_fully_grounded=spec.quality.is_fully_grounded,
        )
        return cls(
            spec_id=str(spec.id),
            lineage_id=str(spec.lineage_id),
            version=spec.version,
            project_id=spec.project_id,
            is_production_ready=spec.is_production_ready,
            created_at=_iso(spec.created_at),
            quality=quality,
            tokens=[_token_view(t) for t in spec.token_set],
            scales=_scales_view(spec),
            systems=_systems_view(spec),
            states=_states_view(spec),
            components=[_component_view(s) for s in spec.component_specs],
            themes=_themes_view(spec),
            localization=_localization_view(spec),
            constraints=_constraints_view(spec),
            graphs={g.kind.value: _graph_view(g) for g in spec.graphs.all},
            token_count=spec.token_count(),
            component_count=spec.component_count(),
            evidence_count=spec.evidence_count(),
        )


@dataclass(frozen=True, slots=True)
class DesignSystemBundleView:
    """The neutral design-system specification a downstream UI phase consumes."""

    spec_id: str
    project_id: str
    is_production_ready: bool
    created_at: str
    tokens: list[dict]
    components: list[dict]
    themes: list[dict]
    localization: dict
    constraints: list[dict]

    @classmethod
    def from_bundle(
        cls, bundle: DesignSystemBundle, spec: DesignSystemSpecification
    ) -> DesignSystemBundleView:
        return cls(
            spec_id=str(bundle.spec_id),
            project_id=bundle.project_id,
            is_production_ready=bundle.is_production_ready,
            created_at=_iso(bundle.created_at),
            tokens=[_token_view(t) for t in bundle.token_set],
            components=[_component_view(s) for s in bundle.component_specs],
            themes=_themes_view(spec),
            localization=_localization_view(spec),
            constraints=_constraints_view(spec),
        )


@dataclass(frozen=True, slots=True)
class TraceView:
    """An explanation of one graph node: the node, its successors, and its evidence."""

    node: dict
    successors: list[dict]
    evidence: list[dict]
