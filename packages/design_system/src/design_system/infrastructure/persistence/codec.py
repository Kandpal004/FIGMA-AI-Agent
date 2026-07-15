"""Codec — serializes a DesignSystemSpecification to a JSON document and back.

A specification is a deep, immutable aggregate; it is stored and loaded whole as one JSON
document. This codec is the single, exhaustive translation. Reconstruction goes through the
normal aggregate constructor, so a decoded specification is re-validated (its provenance and
token integrity re-checked, its graphs re-checked for acyclicity, its theme parity re-enforced)
— a corrupt document cannot yield an inconsistent or ungrounded design system.

Pure functions, no I/O.
"""

from __future__ import annotations

from datetime import datetime

from design_system.domain.component.mapping import PlatformMapping
from design_system.domain.component.spec import (
    AccessibilitySpec,
    ComponentSpec,
    ComponentSpecSet,
    PerformanceBudget,
)
from design_system.domain.component.variant import (
    ComponentProperty,
    ComponentStateSpec,
    ComponentVariant,
    ResponsiveSpec,
)
from design_system.domain.constraint.constraint import Constraint, ConstraintSet
from design_system.domain.evidence.evidence import Citation, DSEvidence, EvidenceGraph
from design_system.domain.graph.ds_graph import DSEdge, DSGraph, DSNode
from design_system.domain.graph.graphs import DesignSystemGraphs
from design_system.domain.quality.quality import DesignSystemQualityMetrics
from design_system.domain.report.report import DesignSystemSpecification
from design_system.domain.shared.ids import (
    ComponentSpecId,
    ConstraintId,
    DesignSystemSpecId,
    DesignSystemSpecLineageId,
    DSEdgeId,
    DSEvidenceId,
    DSNodeId,
    ThemeId,
    TokenId,
)
from design_system.domain.shared.value_objects import (
    AtomicLevel,
    Breakpoint,
    ComponentType,
    Confidence,
    ConstraintKind,
    Direction,
    EnforcementLevel,
    GraphKind,
    GraphRelation,
    NodeKind,
    Percentage,
    Platform,
    PropertyType,
    ProvenanceKind,
    Ratio,
    StateKind,
    Tag,
    ThemeMode,
    TokenCategory,
    TokenTier,
)
from design_system.domain.theme.localization import Localization
from design_system.domain.theme.theme import Theme, ThemeSet
from design_system.domain.token.scales import (
    BorderScale,
    ElevationScale,
    RadiusScale,
    ShadowScale,
    SpacingScale,
    TypographyScale,
)
from design_system.domain.token.state import StateTokens
from design_system.domain.token.systems import (
    BreakpointSystem,
    ContainerRules,
    GridSystem,
    InteractionTokens,
    MotionSystem,
)
from design_system.domain.token.token import DesignToken, TokenSet, TokenValue

__all__ = ["from_document", "to_document"]


def _ids(ids) -> list[str]:
    return [str(i) for i in ids]


def _citations_doc(citations) -> list[dict]:
    return [{"evidence_id": str(c.evidence_id), "relevance": c.relevance} for c in citations]


# --------------------------------------------------------------------------- #
# Encode                                                                       #
# --------------------------------------------------------------------------- #
def _token_doc(t: DesignToken) -> dict:
    return {
        "id": str(t.id),
        "key": t.key,
        "category": t.category.value,
        "tier": t.tier.value,
        "literal": t.value.literal,
        "ref": t.value.ref,
        "description": t.description,
        "citations": _citations_doc(t.citations),
        "tags": sorted(tag.value for tag in t.tags),
    }


def _component_doc(s: ComponentSpec) -> dict:
    return {
        "id": str(s.id),
        "component": s.component.value,
        "atomic_level": s.atomic_level.value,
        "token_refs": list(s.token_refs),
        "properties": [
            {"name": p.name, "type": p.type.value, "options": list(p.options),
             "default": p.default, "required": p.required}
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
            "role": s.accessibility.role, "keyboard": list(s.accessibility.keyboard),
            "min_contrast": s.accessibility.min_contrast,
            "focus_visible": s.accessibility.focus_visible, "notes": s.accessibility.notes,
        },
        "performance": {
            "lazy_load": s.performance.lazy_load, "max_dom_nodes": s.performance.max_dom_nodes,
            "blocks_lcp": s.performance.blocks_lcp, "notes": s.performance.notes,
        },
        "mappings": [
            {"platform": m.platform.value, "primitive": m.primitive, "identifier": m.identifier,
             "settings": list(m.settings), "capabilities": list(m.capabilities), "notes": m.notes}
            for m in s.mappings.values()
        ],
        "citations": _citations_doc(s.citations),
        "tags": sorted(tag.value for tag in s.tags),
    }


def _graph_doc(g: DSGraph) -> dict:
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


def to_document(spec: DesignSystemSpecification) -> dict:
    """Serialize a specification to a JSON-safe document."""
    return {
        "id": str(spec.id),
        "lineage_id": str(spec.lineage_id),
        "version": spec.version,
        "project_id": spec.project_id,
        "created_at": spec.created_at.isoformat(),
        "tokens": [_token_doc(t) for t in spec.token_set],
        "scales": {
            "typography": {"base_px": spec.typography.base_px, "ratio": spec.typography.ratio.value,
                           "role_tokens": list(spec.typography.role_tokens)},
            "spacing": {"base_px": spec.spacing.base_px,
                        "step_tokens": list(spec.spacing.step_tokens)},
            "radius": {"step_tokens": list(spec.radius.step_tokens)},
            "elevation": {"level_tokens": list(spec.elevation.level_tokens)},
            "shadow": {"step_tokens": list(spec.shadow.step_tokens)},
            "border": {"width_tokens": list(spec.border.width_tokens)},
        },
        "systems": {
            "breakpoints": {bp.value: w for bp, w in spec.breakpoints.min_width_px.items()},
            "grid": {
                "columns": {bp.value: c for bp, c in spec.grid.columns.items()},
                "gutter_tokens": {bp.value: g for bp, g in spec.grid.gutter_tokens.items()},
            },
            "container": {bp.value: w for bp, w in spec.container.max_width_px.items()},
            "motion": {"duration_tokens": list(spec.motion.duration_tokens),
                       "easing_tokens": list(spec.motion.easing_tokens)},
            "interaction": {
                "focus_ring_token": spec.interaction.focus_ring_token,
                "hit_target_token": spec.interaction.hit_target_token,
                "transition_token": spec.interaction.transition_token,
            },
        },
        "states": [{"state": s.state.value, "token_refs": dict(s.token_refs)} for s in spec.states],
        "components": [_component_doc(s) for s in spec.component_specs],
        "themes": [
            {"id": str(t.id), "mode": t.mode.value, "name": t.name, "overrides": dict(t.overrides)}
            for t in spec.theme_set
        ],
        "localization": {
            "directions": [d.value for d in spec.localization.directions],
            "locales": list(spec.localization.locales),
            "mirror_properties": list(spec.localization.mirror_properties),
        },
        "constraints": [
            {"id": str(c.id), "kind": c.kind.value, "enforcement": c.enforcement.value,
             "statement": c.statement, "rationale": c.rationale,
             "parameters": dict(c.parameters), "citations": _citations_doc(c.citations)}
            for c in spec.constraint_set
        ],
        "graphs": [_graph_doc(g) for g in spec.graphs.all],
        "evidence": [
            {"id": str(e.id), "provenance": e.provenance.value, "external_ref": e.external_ref,
             "claim": e.claim, "confidence": e.confidence.value, "statement": e.statement,
             "source_name": e.source_name, "tags": sorted(t.value for t in e.tags)}
            for e in spec.evidence_graph
        ],
        "quality": {
            "token_integrity": spec.quality.token_integrity.value,
            "component_coverage": spec.quality.component_coverage.value,
            "theme_parity": spec.quality.theme_parity.value,
            "grounding": spec.quality.grounding.value,
            "confidence": spec.quality.confidence.value,
        },
    }


# --------------------------------------------------------------------------- #
# Decode                                                                       #
# --------------------------------------------------------------------------- #
def _ev_ids(raw) -> tuple[DSEvidenceId, ...]:
    return tuple(DSEvidenceId.from_string(i) for i in raw)


def _citations(raw) -> tuple[Citation, ...]:
    return tuple(
        Citation(evidence_id=DSEvidenceId.from_string(c["evidence_id"]), relevance=c["relevance"])
        for c in raw
    )


def _token(doc: dict) -> DesignToken:
    value = (
        TokenValue.of(doc["literal"]) if doc["literal"] is not None
        else TokenValue.alias(doc["ref"])
    )
    return DesignToken(
        id=TokenId.from_string(doc["id"]),
        key=doc["key"],
        category=TokenCategory(doc["category"]),
        tier=TokenTier(doc["tier"]),
        value=value,
        description=doc.get("description", ""),
        citations=_citations(doc["citations"]),
        tags=frozenset(Tag.of(t) for t in doc.get("tags", ())),
    )


def _component(doc: dict) -> ComponentSpec:
    a = doc["accessibility"]
    p = doc["performance"]
    return ComponentSpec(
        id=ComponentSpecId.from_string(doc["id"]),
        component=ComponentType(doc["component"]),
        atomic_level=AtomicLevel(doc["atomic_level"]),
        token_refs=tuple(doc["token_refs"]),
        properties=tuple(
            ComponentProperty(name=pr["name"], type=PropertyType(pr["type"]),
                              options=tuple(pr["options"]), default=pr["default"],
                              required=pr["required"])
            for pr in doc["properties"]
        ),
        variants=tuple(
            ComponentVariant(name=v["name"], property_values=dict(v["property_values"]),
                             description=v["description"])
            for v in doc["variants"]
        ),
        states=ComponentStateSpec(states=tuple(
            StateTokens(state=StateKind(st["state"]), token_refs=dict(st["token_refs"]))
            for st in doc["states"]
        )),
        responsive=ResponsiveSpec(
            behavior={Breakpoint(bp): note for bp, note in doc["responsive"].items()}
        ),
        accessibility=AccessibilitySpec(
            role=a["role"], keyboard=tuple(a["keyboard"]), min_contrast=a["min_contrast"],
            focus_visible=a["focus_visible"], notes=a["notes"],
        ),
        performance=PerformanceBudget(
            lazy_load=p["lazy_load"], max_dom_nodes=p["max_dom_nodes"],
            blocks_lcp=p["blocks_lcp"], notes=p["notes"],
        ),
        mappings={
            Platform(m["platform"]): PlatformMapping(
                platform=Platform(m["platform"]), primitive=m["primitive"],
                identifier=m["identifier"], settings=tuple(m["settings"]),
                capabilities=tuple(m["capabilities"]), notes=m["notes"],
            )
            for m in doc["mappings"]
        },
        citations=_citations(doc["citations"]),
        tags=frozenset(Tag.of(t) for t in doc.get("tags", ())),
    )


def _graph(doc: dict) -> DSGraph:
    return DSGraph.of(
        GraphKind(doc["kind"]),
        [DSNode(id=DSNodeId.from_string(n["id"]), kind=NodeKind(n["kind"]), label=n["label"],
                evidence_ids=_ev_ids(n["evidence_ids"])) for n in doc["nodes"]],
        [DSEdge(id=DSEdgeId.from_string(e["id"]), source=DSNodeId.from_string(e["source"]),
                target=DSNodeId.from_string(e["target"]), relation=GraphRelation(e["relation"]))
         for e in doc["edges"]],
    )


def _bp_map(raw) -> dict:
    return {Breakpoint(bp): v for bp, v in raw.items()}


def from_document(doc: dict) -> DesignSystemSpecification:
    """Reconstruct a specification from its document, re-validating every invariant."""
    sc = doc["scales"]
    sy = doc["systems"]
    q = doc["quality"]
    graphs_by_kind = {GraphKind(g["kind"]): _graph(g) for g in doc["graphs"]}
    return DesignSystemSpecification(
        id=DesignSystemSpecId.from_string(doc["id"]),
        lineage_id=DesignSystemSpecLineageId.from_string(doc["lineage_id"]),
        version=doc["version"],
        project_id=doc["project_id"],
        token_set=TokenSet.of(_token(t) for t in doc["tokens"]),
        typography=TypographyScale(
            base_px=sc["typography"]["base_px"], ratio=Ratio.of(sc["typography"]["ratio"]),
            role_tokens=tuple(sc["typography"]["role_tokens"]),
        ),
        spacing=SpacingScale(base_px=sc["spacing"]["base_px"],
                             step_tokens=tuple(sc["spacing"]["step_tokens"])),
        radius=RadiusScale(step_tokens=tuple(sc["radius"]["step_tokens"])),
        elevation=ElevationScale(level_tokens=tuple(sc["elevation"]["level_tokens"])),
        shadow=ShadowScale(step_tokens=tuple(sc["shadow"]["step_tokens"])),
        border=BorderScale(width_tokens=tuple(sc["border"]["width_tokens"])),
        breakpoints=BreakpointSystem(_bp_map(sy["breakpoints"])),
        grid=GridSystem(columns=_bp_map(sy["grid"]["columns"]),
                        gutter_tokens=_bp_map(sy["grid"]["gutter_tokens"])),
        container=ContainerRules(_bp_map(sy["container"])),
        motion=MotionSystem(duration_tokens=tuple(sy["motion"]["duration_tokens"]),
                            easing_tokens=tuple(sy["motion"]["easing_tokens"])),
        interaction=InteractionTokens(
            focus_ring_token=sy["interaction"]["focus_ring_token"],
            hit_target_token=sy["interaction"]["hit_target_token"],
            transition_token=sy["interaction"]["transition_token"],
        ),
        states=tuple(
            StateTokens(state=StateKind(s["state"]), token_refs=dict(s["token_refs"]))
            for s in doc["states"]
        ),
        component_specs=ComponentSpecSet.of(_component(s) for s in doc["components"]),
        theme_set=ThemeSet.of(
            Theme(id=ThemeId.from_string(t["id"]), mode=ThemeMode(t["mode"]), name=t["name"],
                  overrides=dict(t["overrides"]))
            for t in doc["themes"]
        ),
        localization=Localization(
            directions=tuple(Direction(d) for d in doc["localization"]["directions"]),
            locales=tuple(doc["localization"]["locales"]),
            mirror_properties=tuple(doc["localization"]["mirror_properties"]),
        ),
        constraint_set=ConstraintSet.of(
            Constraint(id=ConstraintId.from_string(c["id"]), kind=ConstraintKind(c["kind"]),
                       enforcement=EnforcementLevel(c["enforcement"]), statement=c["statement"],
                       rationale=c["rationale"], parameters=dict(c["parameters"]),
                       citations=_citations(c["citations"]))
            for c in doc["constraints"]
        ),
        graphs=DesignSystemGraphs(
            token=graphs_by_kind[GraphKind.TOKEN],
            component=graphs_by_kind[GraphKind.COMPONENT],
            variant=graphs_by_kind[GraphKind.VARIANT],
            theme=graphs_by_kind[GraphKind.THEME],
            constraint=graphs_by_kind[GraphKind.CONSTRAINT],
            dependency=graphs_by_kind[GraphKind.DEPENDENCY],
        ),
        evidence_graph=EvidenceGraph.of(
            DSEvidence(id=DSEvidenceId.from_string(e["id"]),
                       provenance=ProvenanceKind(e["provenance"]), external_ref=e["external_ref"],
                       claim=e["claim"], confidence=Confidence(e["confidence"]),
                       statement=e.get("statement", ""), source_name=e.get("source_name", ""),
                       tags=frozenset(Tag.of(t) for t in e.get("tags", ())))
            for e in doc["evidence"]
        ),
        quality=DesignSystemQualityMetrics(
            token_integrity=Percentage(q["token_integrity"]),
            component_coverage=Percentage(q["component_coverage"]),
            theme_parity=Percentage(q["theme_parity"]),
            grounding=Percentage(q["grounding"]),
            confidence=Confidence(q["confidence"]),
        ),
        created_at=datetime.fromisoformat(doc["created_at"]),
    )
