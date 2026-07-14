"""Serializable view DTOs — the specification projected for transport.

The facade never returns domain aggregates; it returns these flat, immutable views. They
project a :class:`DesignLanguageSpecification` (and the neutral :class:`DesignSystemBundle`)
into plain ``dict``-friendly structures an API, the orchestration layer, or a future Design
System engine can serialize — carrying the full language (DNA, tokens, philosophies,
personalities, systems, selection, rules, constraints, graphs, and explanation) but no domain
objects and no concrete pixels.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from design_language.domain.graph.dl_graph import DLGraph
from design_language.domain.report.bundle import DesignSystemBundle
from design_language.domain.report.report import DesignLanguageSpecification

__all__ = [
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


def _dna_view(spec: DesignLanguageSpecification) -> dict:
    d = spec.visual_dna
    return {
        "visual_style": d.visual_style.value, "luxury_level": int(d.luxury_level),
        "minimalism_level": int(d.minimalism_level), "density": d.density.value,
        "visual_weight": d.visual_weight.value, "contrast": d.contrast.value,
        "rhythm": d.rhythm.value, "essence": d.essence,
        "traits": [t.value for t in d.traits], "is_distinctive": d.is_distinctive,
        "evidence_ids": _ids(d.evidence_ids),
    }


def _tokens_view(spec: DesignLanguageSpecification) -> dict:
    t = spec.tokens
    return {
        "spacing": {"base_unit": t.spacing.base_unit, "ratio": t.spacing.ratio.value, "steps": t.spacing.steps},
        "type_scale": {"ratio": t.type_scale.ratio.value, "steps": t.type_scale.steps},
        "radius": {"steps": t.radius.steps, "sharpness": t.radius.sharpness},
        "elevation": {"levels": t.elevation.levels, "posture": t.elevation.posture},
        "motion": {"duration_tiers": t.motion.duration_tiers, "easing": t.motion.easing},
        "color": {"strategy": t.color.strategy.value, "roles": [r.value for r in t.color.roles],
                  "accent_count": t.color.accent_count},
        "contrast": {"text_min": t.contrast.text_min, "ui_min": t.contrast.ui_min},
    }


def _philosophies_view(spec: DesignLanguageSpecification) -> dict:
    return {
        p.kind.value: {"approach": p.approach, "principles": list(p.principles),
                       "evidence_ids": _ids(p.evidence_ids)}
        for p in spec.philosophies
    }


def _personalities_view(spec: DesignLanguageSpecification) -> dict:
    return {
        p.kind.value: {"character": p.character, "attributes": list(p.attributes),
                       "evidence_ids": _ids(p.evidence_ids)}
        for p in spec.personalities
    }


def _selection_view(spec: DesignLanguageSpecification) -> dict:
    s = spec.language_selection
    return {
        "archetype": s.archetype.value, "rationale": s.rationale,
        "business_alignment": s.business_alignment,
        "influences": [t.value for t in s.influences],
        "considered": [{"option": a.option, "reason_rejected": a.reason_rejected}
                       for a in s.considered],
        "evidence_ids": _ids(s.evidence_ids),
    }


def _graph_view(g: DLGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [{"id": str(n.id), "kind": n.kind.value, "label": n.label,
                   "evidence_ids": _ids(n.evidence_ids)} for n in g],
        "edges": [{"source": str(e.source), "target": str(e.target), "relation": e.relation.value}
                  for e in g.edges],
    }


def _grid_view(spec: DesignLanguageSpecification) -> dict:
    g = spec.grid_system
    return {"columns": g.columns, "alignment": g.alignment.value, "gutter_steps": g.gutter_steps,
            "margin_steps": g.margin_steps, "max_container_steps": g.max_container_steps}


def _responsive_view(spec: DesignLanguageSpecification) -> dict:
    r = spec.responsive_strategy
    return {"approach": r.approach.value, "breakpoint_tiers": r.breakpoint_tiers,
            "scales_fluidly": r.scales_fluidly, "principles": list(r.principles)}


def _explanation_view(spec: DesignLanguageSpecification) -> dict:
    e = spec.explanation
    return {"why_selected": e.why_selected, "business_alignment": e.business_alignment,
            "why_rejected": list(e.why_rejected)}


def _consistency_view(spec: DesignLanguageSpecification) -> list[dict]:
    return [{"id": str(r.id), "kind": r.kind.value, "statement": r.statement,
             "applies_to": r.applies_to, "evidence_ids": _ids(r.evidence_ids)}
            for r in spec.consistency_rules]


def _composition_view(spec: DesignLanguageSpecification) -> list[dict]:
    return [{"id": str(r.id), "kind": r.kind.value, "statement": r.statement,
             "evidence_ids": _ids(r.evidence_ids)} for r in spec.composition_rules]


def _constraints_view(spec: DesignLanguageSpecification) -> list[dict]:
    return [{"id": str(c.id), "kind": c.kind.value, "statement": c.statement,
             "boundary": c.boundary, "rationale": c.rationale, "evidence_ids": _ids(c.evidence_ids)}
            for c in spec.constraints]


@dataclass(frozen=True, slots=True)
class QualityView:
    overall_score: float
    band: str
    coverage: float
    grounding: float
    consistency: float
    confidence: float
    is_fully_grounded: bool


@dataclass(frozen=True, slots=True)
class GraphView:
    graph: dict


@dataclass(frozen=True, slots=True)
class SpecificationView:
    """The full, flat projection of a design-language specification."""

    spec_id: str
    lineage_id: str
    version: int
    project_id: str
    industry: str
    is_production_ready: bool
    created_at: str
    quality: QualityView
    visual_dna: dict
    tokens: dict
    grid_system: dict
    responsive_strategy: dict
    philosophies: dict
    personalities: dict
    language_selection: dict
    consistency_rules: list[dict]
    composition_rules: list[dict]
    constraints: list[dict]
    graphs: dict
    explanation: dict
    determined_attribute_count: int
    evidence_count: int

    @classmethod
    def from_specification(cls, spec: DesignLanguageSpecification) -> SpecificationView:
        quality = QualityView(
            overall_score=spec.quality.overall_score.value, band=spec.quality.band.value,
            coverage=spec.quality.coverage.value, grounding=spec.quality.grounding.value,
            consistency=spec.quality.consistency.value, confidence=spec.quality.confidence.value,
            is_fully_grounded=spec.quality.is_fully_grounded,
        )
        return cls(
            spec_id=str(spec.id), lineage_id=str(spec.lineage_id), version=spec.version,
            project_id=spec.project_id, industry=spec.industry.value,
            is_production_ready=spec.is_production_ready, created_at=_iso(spec.created_at),
            quality=quality, visual_dna=_dna_view(spec), tokens=_tokens_view(spec),
            grid_system=_grid_view(spec), responsive_strategy=_responsive_view(spec),
            philosophies=_philosophies_view(spec), personalities=_personalities_view(spec),
            language_selection=_selection_view(spec),
            consistency_rules=_consistency_view(spec), composition_rules=_composition_view(spec),
            constraints=_constraints_view(spec),
            graphs={g.kind.value: _graph_view(g) for g in spec.graphs.all()},
            explanation=_explanation_view(spec),
            determined_attribute_count=spec.determined_attribute_count(),
            evidence_count=spec.evidence_count(),
        )


@dataclass(frozen=True, slots=True)
class DesignSystemBundleView:
    """The neutral design language a downstream Design System consumes."""

    spec_id: str
    project_id: str
    industry: str
    is_production_ready: bool
    created_at: str
    selection: dict
    visual_dna: dict
    tokens: dict
    grid_system: dict
    responsive_strategy: dict
    philosophies: dict
    personalities: dict
    consistency_rules: list[dict]
    composition_rules: list[dict]
    constraints: list[dict]

    @classmethod
    def from_bundle(
        cls, bundle: DesignSystemBundle, spec: DesignLanguageSpecification
    ) -> DesignSystemBundleView:
        return cls(
            spec_id=str(bundle.spec_id), project_id=bundle.project_id,
            industry=bundle.industry.value, is_production_ready=bundle.is_production_ready,
            created_at=_iso(bundle.created_at), selection=_selection_view(spec),
            visual_dna=_dna_view(spec), tokens=_tokens_view(spec), grid_system=_grid_view(spec),
            responsive_strategy=_responsive_view(spec), philosophies=_philosophies_view(spec),
            personalities=_personalities_view(spec), consistency_rules=_consistency_view(spec),
            composition_rules=_composition_view(spec), constraints=_constraints_view(spec),
        )


@dataclass(frozen=True, slots=True)
class TraceView:
    """An explanation of one graph node: the node, its successors, and its evidence."""

    node: dict
    successors: list[dict]
    evidence: list[dict]
