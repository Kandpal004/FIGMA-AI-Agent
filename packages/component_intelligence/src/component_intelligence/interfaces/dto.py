"""Serializable view DTOs — the specification projected for transport.

The facade never returns domain aggregates; it returns these flat, immutable views. They
project a :class:`ComponentCompositionSpecification` (and the neutral
:class:`ComponentSpecBundle`) into plain ``dict``-friendly structures an API, the orchestration
layer, or a future Design System engine can serialize — carrying the full intelligence (per
component: purposes, impacts, behaviours, contracts, usage, variants, states) plus the
compatibility web, the rules, and the two graphs, but no domain objects and no component code.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from component_intelligence.domain.component.decision import ComponentDecision
from component_intelligence.domain.graph.ci_graph import CIGraph
from component_intelligence.domain.report.bundle import ComponentSpecBundle
from component_intelligence.domain.report.report import ComponentCompositionSpecification

__all__ = [
    "ComponentSpecBundleView",
    "ComponentView",
    "GraphView",
    "QualityView",
    "SpecificationView",
    "TraceView",
]


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _ids(ids) -> list[str]:
    return [str(i) for i in ids]


def _decision_view(d: ComponentDecision) -> dict:
    return {
        "id": str(d.id), "component": d.component.value, "atomic_level": d.atomic_level.value,
        "inclusion": d.inclusion.value, "priority": int(d.priority),
        "purposes": {
            "business": d.purposes.business_purpose, "user": d.purposes.user_purpose,
            "conversion": d.purposes.conversion_purpose, "trust": d.purposes.trust_purpose,
        },
        "impacts": {
            "seo": d.impacts.seo.value, "accessibility": d.impacts.accessibility.value,
            "performance": d.impacts.performance.value,
            "conversion_effect": d.impacts.conversion_effect.value,
            "friction_effect": d.impacts.friction_effect.value,
            "trust_effect": d.impacts.trust_effect.value,
        },
        "mobile_behaviour": d.mobile_behaviour.intent,
        "responsive_rules": [{"breakpoint": r.breakpoint.value, "intent": r.intent.value}
                             for r in d.responsive_rules],
        "interaction_rules": [{"kind": i.kind.value, "intent": i.intent} for i in d.interaction_rules],
        "animation_rules": [{"kind": a.kind.value, "intent": a.intent} for a in d.animation_rules],
        "dependencies": [c.value for c in d.dependencies],
        "required_inputs": [{"kind": i.kind.value, "description": i.description, "required": i.required}
                            for i in d.required_inputs],
        "expected_outputs": [{"kind": o.kind.value, "name": o.name} for o in d.expected_outputs],
        "success_criteria": [c.statement for c in d.success_criteria],
        "failure_criteria": [c.statement for c in d.failure_criteria],
        "usage": {
            "page_affinity": [p.value for p in d.usage.page_affinity],
            "when_to_use": list(d.usage.when_to_use),
            "when_not_to_use": list(d.usage.when_not_to_use),
            "conflicts_with": [c.value for c in d.usage.conflicts_with],
        },
        "variants": [{"name": v.name, "purpose": v.purpose} for v in d.variants],
        "states": [{"kind": s.kind.value, "description": s.description} for s in d.states],
        "design_token_refs": list(d.design_token_refs),
        "considered_alternative": (
            {"option": d.considered_alternative.option,
             "reason_rejected": d.considered_alternative.reason_rejected}
            if d.considered_alternative else None
        ),
        "improves_conversion": d.improves_conversion, "builds_trust": d.builds_trust,
        "evidence_ids": _ids(d.evidence_ids),
    }


def _compatibility_view(spec: ComponentCompositionSpecification) -> dict:
    def links(kind):
        return [{"source": link.source.value, "target": link.target.value,
                 "rationale": link.rationale} for link in spec.compatibility.by_kind(kind)]
    from component_intelligence.domain.shared.value_objects import CompatibilityKind
    return {
        "requires": links(CompatibilityKind.REQUIRES),
        "conflicts": links(CompatibilityKind.CONFLICTS_WITH),
        "enhances": links(CompatibilityKind.ENHANCES),
        "replaces": links(CompatibilityKind.REPLACES),
    }


def _graph_view(g: CIGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [{"id": str(n.id), "kind": n.kind.value, "label": n.label,
                   "evidence_ids": _ids(n.evidence_ids)} for n in g],
        "edges": [{"source": str(e.source), "target": str(e.target), "relation": e.relation.value}
                  for e in g.edges],
    }


def _composition_rules(spec) -> list[dict]:
    return [{"id": str(r.id), "kind": r.kind.value, "statement": r.statement,
             "evidence_ids": _ids(r.evidence_ids)} for r in spec.composition_rules]


def _placement_rules(spec) -> list[dict]:
    return [{"id": str(r.id), "component": r.component.value, "page": r.page.value,
             "region": r.region.value, "order": r.order, "evidence_ids": _ids(r.evidence_ids)}
            for r in spec.placement_rules]


def _visibility_rules(spec) -> list[dict]:
    return [{"id": str(r.id), "component": r.component.value, "kind": r.kind.value,
             "condition": r.condition, "evidence_ids": _ids(r.evidence_ids)}
            for r in spec.visibility_rules]


def _responsive_rules(spec) -> list[dict]:
    return [{"id": str(r.id), "component": r.component.value, "breakpoint": r.breakpoint.value,
             "intent": r.intent.value, "statement": r.statement, "evidence_ids": _ids(r.evidence_ids)}
            for r in spec.responsive_rules]


def _reuse_rules(spec) -> list[dict]:
    return [{"id": str(r.id), "component": r.component.value,
             "shared_across": [p.value for p in r.shared_across], "statement": r.statement,
             "evidence_ids": _ids(r.evidence_ids)} for r in spec.reuse_rules]


@dataclass(frozen=True, slots=True)
class QualityView:
    overall_score: float
    band: str
    coverage: float
    grounding: float
    coherence: float
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
    """The full, flat projection of a component-composition specification."""

    spec_id: str
    lineage_id: str
    version: int
    project_id: str
    is_production_ready: bool
    created_at: str
    quality: QualityView
    components: list[dict]
    compatibility: dict
    composition_rules: list[dict]
    placement_rules: list[dict]
    visibility_rules: list[dict]
    responsive_rules: list[dict]
    reuse_rules: list[dict]
    graphs: dict
    component_count: int
    included_count: int
    evidence_count: int

    @classmethod
    def from_specification(cls, spec: ComponentCompositionSpecification) -> SpecificationView:
        quality = QualityView(
            overall_score=spec.quality.overall_score.value, band=spec.quality.band.value,
            coverage=spec.quality.coverage.value, grounding=spec.quality.grounding.value,
            coherence=spec.quality.coherence.value, confidence=spec.quality.confidence.value,
            is_fully_grounded=spec.quality.is_fully_grounded,
        )
        return cls(
            spec_id=str(spec.id), lineage_id=str(spec.lineage_id), version=spec.version,
            project_id=spec.project_id, is_production_ready=spec.is_production_ready,
            created_at=_iso(spec.created_at), quality=quality,
            components=[_decision_view(d) for d in spec.composition],
            compatibility=_compatibility_view(spec),
            composition_rules=_composition_rules(spec), placement_rules=_placement_rules(spec),
            visibility_rules=_visibility_rules(spec), responsive_rules=_responsive_rules(spec),
            reuse_rules=_reuse_rules(spec),
            graphs={g.kind.value: _graph_view(g) for g in spec.graphs.all()},
            component_count=spec.component_count(), included_count=spec.included_count(),
            evidence_count=spec.evidence_count(),
        )


@dataclass(frozen=True, slots=True)
class ComponentSpecBundleView:
    """The neutral component specification a downstream Design System consumes."""

    spec_id: str
    project_id: str
    is_production_ready: bool
    created_at: str
    components: list[dict]
    compatibility: dict
    composition_rules: list[dict]
    placement_rules: list[dict]
    visibility_rules: list[dict]
    responsive_rules: list[dict]
    reuse_rules: list[dict]

    @classmethod
    def from_bundle(
        cls, bundle: ComponentSpecBundle, spec: ComponentCompositionSpecification
    ) -> ComponentSpecBundleView:
        return cls(
            spec_id=str(bundle.spec_id), project_id=bundle.project_id,
            is_production_ready=bundle.is_production_ready, created_at=_iso(bundle.created_at),
            components=[_decision_view(d) for d in bundle.components],
            compatibility=_compatibility_view(spec),
            composition_rules=_composition_rules(spec), placement_rules=_placement_rules(spec),
            visibility_rules=_visibility_rules(spec), responsive_rules=_responsive_rules(spec),
            reuse_rules=_reuse_rules(spec),
        )


@dataclass(frozen=True, slots=True)
class TraceView:
    """An explanation of one graph node: the node, its successors, and its evidence."""

    node: dict
    successors: list[dict]
    evidence: list[dict]
