"""Codec — serializes a DesignLanguageSpecification to a JSON document and back.

A specification is a deep, immutable aggregate; it is stored and loaded whole as one JSON
document. This codec is the single, exhaustive translation. Reconstruction goes through the
normal aggregate constructor, so a decoded specification is re-validated (its provenance and
graph integrity re-checked) — a corrupt document cannot yield an ungrounded language.

Pure functions, no I/O.
"""

from __future__ import annotations

from datetime import datetime

from design_language.domain.dna.visual_dna import VisualDNA
from design_language.domain.evidence.evidence import DLEvidence, EvidenceGraph
from design_language.domain.graph.dl_graph import DLEdge, DLGraph, DLNode
from design_language.domain.graph.graphs import DesignLanguageGraphs
from design_language.domain.language.selection import LanguageSelection
from design_language.domain.personality.personality import Personality, PersonalitySet
from design_language.domain.philosophy.philosophy import Philosophy, PhilosophySet
from design_language.domain.quality.quality import DesignLanguageQualityMetrics
from design_language.domain.report.explanation import LanguageExplanation
from design_language.domain.report.report import DesignLanguageSpecification
from design_language.domain.rules.composition import CompositionRule, CompositionRuleSet
from design_language.domain.rules.consistency import ConsistencyRule, ConsistencyRuleSet
from design_language.domain.rules.constraint import ConstraintSet, VisualConstraint
from design_language.domain.shared.ids import (
    ConstraintId,
    DesignLanguageSpecId,
    DesignLanguageSpecLineageId,
    DLEdgeId,
    DLEvidenceId,
    DLNodeId,
    PhilosophyId,
    RuleId,
)
from design_language.domain.shared.value_objects import (
    AlignmentApproach,
    ColorRole,
    ColorStrategy,
    CompositionKind,
    Confidence,
    ConsideredAlternative,
    ConsistencyKind,
    ConstraintKind,
    ContrastLevel,
    Density,
    GraphKind,
    GraphRelation,
    IndustryPreset,
    LanguageArchetype,
    Level,
    NodeKind,
    Percentage,
    PersonalityKind,
    PhilosophyKind,
    ProvenanceKind,
    Ratio,
    ResponsiveApproach,
    Rhythm,
    Tag,
    VisualStyle,
    VisualWeight,
)
from design_language.domain.system.grid_system import GridSystem
from design_language.domain.system.responsive import ResponsiveStrategy
from design_language.domain.tokens.color import ColorPhilosophy
from design_language.domain.tokens.scales import (
    ContrastTargets,
    ElevationScale,
    MotionTokens,
    RadiusScale,
    SpacingScale,
    TypeScale,
)
from design_language.domain.tokens.visual_tokens import VisualTokens

__all__ = ["from_document", "to_document"]


def _ids(ids) -> list[str]:
    return [str(i) for i in ids]


# --------------------------------------------------------------------------- #
# Encode                                                                       #
# --------------------------------------------------------------------------- #
def to_document(spec: DesignLanguageSpecification) -> dict:
    """Serialize a specification to a JSON-safe document."""
    d, t = spec.visual_dna, spec.tokens
    sel = spec.language_selection
    return {
        "id": str(spec.id), "lineage_id": str(spec.lineage_id), "version": spec.version,
        "project_id": spec.project_id, "industry": spec.industry.value,
        "created_at": spec.created_at.isoformat(),
        "visual_dna": {
            "visual_style": d.visual_style.value, "luxury_level": int(d.luxury_level),
            "minimalism_level": int(d.minimalism_level), "density": d.density.value,
            "visual_weight": d.visual_weight.value, "contrast": d.contrast.value,
            "rhythm": d.rhythm.value, "essence": d.essence,
            "traits": [tag.value for tag in d.traits], "evidence_ids": _ids(d.evidence_ids),
        },
        "tokens": {
            "spacing": {"base_unit": t.spacing.base_unit, "ratio": t.spacing.ratio.value, "steps": t.spacing.steps},
            "type_scale": {"ratio": t.type_scale.ratio.value, "steps": t.type_scale.steps},
            "radius": {"steps": t.radius.steps, "sharpness": t.radius.sharpness},
            "elevation": {"levels": t.elevation.levels, "posture": t.elevation.posture},
            "motion": {"duration_tiers": t.motion.duration_tiers, "easing": t.motion.easing},
            "color": {"strategy": t.color.strategy.value, "roles": [r.value for r in t.color.roles],
                      "accent_count": t.color.accent_count,
                      "contrast": {"text_min": t.color.contrast.text_min, "ui_min": t.color.contrast.ui_min},
                      "evidence_ids": _ids(t.color.evidence_ids)},
            "contrast": {"text_min": t.contrast.text_min, "ui_min": t.contrast.ui_min},
            "evidence_ids": _ids(t.evidence_ids),
        },
        "philosophies": [
            {"id": str(p.id), "kind": p.kind.value, "approach": p.approach,
             "principles": list(p.principles), "evidence_ids": _ids(p.evidence_ids)}
            for p in spec.philosophies
        ],
        "personalities": [
            {"kind": p.kind.value, "character": p.character, "attributes": list(p.attributes),
             "evidence_ids": _ids(p.evidence_ids)}
            for p in spec.personalities
        ],
        "grid_system": {
            "columns": spec.grid_system.columns, "alignment": spec.grid_system.alignment.value,
            "gutter_steps": spec.grid_system.gutter_steps, "margin_steps": spec.grid_system.margin_steps,
            "max_container_steps": spec.grid_system.max_container_steps,
            "evidence_ids": _ids(spec.grid_system.evidence_ids),
        },
        "responsive_strategy": {
            "approach": spec.responsive_strategy.approach.value,
            "breakpoint_tiers": spec.responsive_strategy.breakpoint_tiers,
            "scales_fluidly": spec.responsive_strategy.scales_fluidly,
            "principles": list(spec.responsive_strategy.principles),
            "evidence_ids": _ids(spec.responsive_strategy.evidence_ids),
        },
        "language_selection": {
            "archetype": sel.archetype.value, "rationale": sel.rationale,
            "business_alignment": sel.business_alignment,
            "influences": [tag.value for tag in sel.influences],
            "considered": [{"option": a.option, "reason_rejected": a.reason_rejected} for a in sel.considered],
            "evidence_ids": _ids(sel.evidence_ids),
        },
        "consistency_rules": [
            {"id": str(r.id), "kind": r.kind.value, "statement": r.statement,
             "applies_to": r.applies_to, "evidence_ids": _ids(r.evidence_ids)}
            for r in spec.consistency_rules
        ],
        "composition_rules": [
            {"id": str(r.id), "kind": r.kind.value, "statement": r.statement,
             "evidence_ids": _ids(r.evidence_ids)}
            for r in spec.composition_rules
        ],
        "constraints": [
            {"id": str(c.id), "kind": c.kind.value, "statement": c.statement,
             "boundary": c.boundary, "rationale": c.rationale, "evidence_ids": _ids(c.evidence_ids)}
            for c in spec.constraints
        ],
        "graphs": [
            {"kind": g.kind.value,
             "nodes": [{"id": str(n.id), "kind": n.kind.value, "label": n.label,
                        "evidence_ids": _ids(n.evidence_ids)} for n in g],
             "edges": [{"id": str(e.id), "source": str(e.source), "target": str(e.target),
                        "relation": e.relation.value} for e in g.edges]}
            for g in spec.graphs.all()
        ],
        "evidence": [
            {"id": str(e.id), "provenance": e.provenance.value, "external_ref": e.external_ref,
             "claim": e.claim, "confidence": e.confidence.value, "statement": e.statement,
             "source_name": e.source_name, "tags": sorted(tg.value for tg in e.tags)}
            for e in spec.evidence_graph
        ],
        "quality": {
            "coverage": spec.quality.coverage.value, "grounding": spec.quality.grounding.value,
            "consistency": spec.quality.consistency.value, "confidence": spec.quality.confidence.value,
        },
        "explanation": {
            "why_selected": spec.explanation.why_selected,
            "business_alignment": spec.explanation.business_alignment,
            "why_rejected": list(spec.explanation.why_rejected),
            "evidence_ids": _ids(spec.explanation.evidence_ids),
        },
    }


# --------------------------------------------------------------------------- #
# Decode                                                                       #
# --------------------------------------------------------------------------- #
def _ev_ids(raw) -> tuple[DLEvidenceId, ...]:
    return tuple(DLEvidenceId.from_string(i) for i in raw)


def _tokens(doc: dict) -> VisualTokens:
    c = doc["color"]
    return VisualTokens(
        spacing=SpacingScale(base_unit=doc["spacing"]["base_unit"],
                             ratio=Ratio(doc["spacing"]["ratio"]), steps=doc["spacing"]["steps"]),
        type_scale=TypeScale(ratio=Ratio(doc["type_scale"]["ratio"]), steps=doc["type_scale"]["steps"]),
        radius=RadiusScale(steps=doc["radius"]["steps"], sharpness=doc["radius"]["sharpness"]),
        elevation=ElevationScale(levels=doc["elevation"]["levels"], posture=doc["elevation"]["posture"]),
        motion=MotionTokens(duration_tiers=doc["motion"]["duration_tiers"], easing=doc["motion"]["easing"]),
        color=ColorPhilosophy(
            strategy=ColorStrategy(c["strategy"]), roles=tuple(ColorRole(r) for r in c["roles"]),
            accent_count=c["accent_count"],
            contrast=ContrastTargets(text_min=c["contrast"]["text_min"], ui_min=c["contrast"]["ui_min"]),
            evidence_ids=_ev_ids(c["evidence_ids"]),
        ),
        contrast=ContrastTargets(text_min=doc["contrast"]["text_min"], ui_min=doc["contrast"]["ui_min"]),
        evidence_ids=_ev_ids(doc["evidence_ids"]),
    )


def _graph(doc: dict) -> DLGraph:
    return DLGraph.of(
        GraphKind(doc["kind"]),
        [DLNode(id=DLNodeId.from_string(n["id"]), kind=NodeKind(n["kind"]), label=n["label"],
                evidence_ids=_ev_ids(n["evidence_ids"])) for n in doc["nodes"]],
        [DLEdge(id=DLEdgeId.from_string(e["id"]), source=DLNodeId.from_string(e["source"]),
                target=DLNodeId.from_string(e["target"]), relation=GraphRelation(e["relation"]))
         for e in doc["edges"]],
    )


def from_document(doc: dict) -> DesignLanguageSpecification:
    """Reconstruct a specification from its document, re-validating every invariant."""
    d = doc["visual_dna"]
    sel = doc["language_selection"]
    q = doc["quality"]
    exp = doc["explanation"]
    return DesignLanguageSpecification(
        id=DesignLanguageSpecId.from_string(doc["id"]),
        lineage_id=DesignLanguageSpecLineageId.from_string(doc["lineage_id"]),
        version=doc["version"], project_id=doc["project_id"],
        industry=IndustryPreset(doc["industry"]),
        visual_dna=VisualDNA(
            visual_style=VisualStyle(d["visual_style"]), luxury_level=Level(d["luxury_level"]),
            minimalism_level=Level(d["minimalism_level"]), density=Density(d["density"]),
            visual_weight=VisualWeight(d["visual_weight"]), contrast=ContrastLevel(d["contrast"]),
            rhythm=Rhythm(d["rhythm"]), essence=d["essence"],
            traits=tuple(Tag.of(t) for t in d["traits"]), evidence_ids=_ev_ids(d["evidence_ids"]),
        ),
        tokens=_tokens(doc["tokens"]),
        philosophies=PhilosophySet.of(
            Philosophy(id=PhilosophyId.from_string(p["id"]), kind=PhilosophyKind(p["kind"]),
                       approach=p["approach"], principles=tuple(p["principles"]),
                       evidence_ids=_ev_ids(p["evidence_ids"]))
            for p in doc["philosophies"]
        ),
        personalities=PersonalitySet.of(
            Personality(kind=PersonalityKind(p["kind"]), character=p["character"],
                        attributes=tuple(p["attributes"]), evidence_ids=_ev_ids(p["evidence_ids"]))
            for p in doc["personalities"]
        ),
        grid_system=GridSystem(
            columns=doc["grid_system"]["columns"],
            alignment=AlignmentApproach(doc["grid_system"]["alignment"]),
            gutter_steps=doc["grid_system"]["gutter_steps"],
            margin_steps=doc["grid_system"]["margin_steps"],
            max_container_steps=doc["grid_system"]["max_container_steps"],
            evidence_ids=_ev_ids(doc["grid_system"]["evidence_ids"]),
        ),
        responsive_strategy=ResponsiveStrategy(
            approach=ResponsiveApproach(doc["responsive_strategy"]["approach"]),
            breakpoint_tiers=doc["responsive_strategy"]["breakpoint_tiers"],
            scales_fluidly=doc["responsive_strategy"]["scales_fluidly"],
            principles=tuple(doc["responsive_strategy"]["principles"]),
            evidence_ids=_ev_ids(doc["responsive_strategy"]["evidence_ids"]),
        ),
        language_selection=LanguageSelection(
            archetype=LanguageArchetype(sel["archetype"]), rationale=sel["rationale"],
            business_alignment=sel["business_alignment"],
            influences=tuple(Tag.of(t) for t in sel["influences"]),
            considered=tuple(ConsideredAlternative(option=a["option"], reason_rejected=a["reason_rejected"])
                             for a in sel["considered"]),
            evidence_ids=_ev_ids(sel["evidence_ids"]),
        ),
        consistency_rules=ConsistencyRuleSet.of(
            ConsistencyRule(id=RuleId.from_string(r["id"]), kind=ConsistencyKind(r["kind"]),
                            statement=r["statement"], applies_to=r["applies_to"],
                            evidence_ids=_ev_ids(r["evidence_ids"]))
            for r in doc["consistency_rules"]
        ),
        composition_rules=CompositionRuleSet.of(
            CompositionRule(id=RuleId.from_string(r["id"]), kind=CompositionKind(r["kind"]),
                            statement=r["statement"], evidence_ids=_ev_ids(r["evidence_ids"]))
            for r in doc["composition_rules"]
        ),
        constraints=ConstraintSet.of(
            VisualConstraint(id=ConstraintId.from_string(c["id"]), kind=ConstraintKind(c["kind"]),
                             statement=c["statement"], boundary=c["boundary"], rationale=c["rationale"],
                             evidence_ids=_ev_ids(c["evidence_ids"]))
            for c in doc["constraints"]
        ),
        graphs=DesignLanguageGraphs.of(_graph(g) for g in doc["graphs"]),
        evidence_graph=EvidenceGraph.of(
            DLEvidence(id=DLEvidenceId.from_string(e["id"]), provenance=ProvenanceKind(e["provenance"]),
                       external_ref=e["external_ref"], claim=e["claim"],
                       confidence=Confidence(e["confidence"]), statement=e.get("statement", ""),
                       source_name=e.get("source_name", ""),
                       tags=frozenset(Tag.of(t) for t in e.get("tags", ())))
            for e in doc["evidence"]
        ),
        quality=DesignLanguageQualityMetrics(
            coverage=Percentage(q["coverage"]), grounding=Percentage(q["grounding"]),
            consistency=Percentage(q["consistency"]), confidence=Confidence(q["confidence"]),
        ),
        explanation=LanguageExplanation(
            why_selected=exp["why_selected"], business_alignment=exp["business_alignment"],
            why_rejected=tuple(exp["why_rejected"]), evidence_ids=_ev_ids(exp["evidence_ids"]),
        ),
        created_at=datetime.fromisoformat(doc["created_at"]),
    )
