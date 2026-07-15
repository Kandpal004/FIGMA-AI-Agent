"""Codec — serializes a ComponentCompositionSpecification to a JSON document and back.

A specification is a deep, immutable aggregate; it is stored and loaded whole as one JSON
document. This codec is the single, exhaustive translation. Reconstruction goes through the
normal aggregate constructor, so a decoded specification is re-validated (its provenance and
coherence re-checked, its graphs re-checked for acyclicity) — a corrupt document cannot yield an
incoherent or ungrounded composition.

Pure functions, no I/O.
"""

from __future__ import annotations

from datetime import datetime

from component_intelligence.domain.compatibility.compatibility import (
    CompatibilityLink,
    CompatibilitySet,
)
from component_intelligence.domain.component.behaviour import (
    AnimationRule,
    InteractionRule,
    MobileBehaviour,
    ResponsiveRule,
)
from component_intelligence.domain.component.contract import (
    ExpectedOutput,
    FailureCriterion,
    RequiredInput,
    SuccessCriterion,
)
from component_intelligence.domain.component.decision import ComponentDecision
from component_intelligence.domain.component.impact import ComponentImpacts
from component_intelligence.domain.component.purpose import ComponentPurposes
from component_intelligence.domain.component.usage import UsageGuidance
from component_intelligence.domain.component.variant import ComponentState, Variant
from component_intelligence.domain.composition.composition import ComponentComposition
from component_intelligence.domain.evidence.evidence import CIEvidence, EvidenceGraph
from component_intelligence.domain.graph.ci_graph import CIEdge, CIGraph, CINode
from component_intelligence.domain.graph.graphs import ComponentGraphs
from component_intelligence.domain.quality.quality import CompositionQualityMetrics
from component_intelligence.domain.report.report import ComponentCompositionSpecification
from component_intelligence.domain.rules.composition_rules import (
    CompositionRule,
    CompositionRuleSet,
)
from component_intelligence.domain.rules.placement_rules import PlacementRule, PlacementRuleSet
from component_intelligence.domain.rules.responsive_rules import (
    ResponsiveCompositionRule,
    ResponsiveRuleSet,
)
from component_intelligence.domain.rules.reuse_rules import ReuseRule, ReuseRuleSet
from component_intelligence.domain.rules.visibility_rules import VisibilityRule, VisibilityRuleSet
from component_intelligence.domain.shared.ids import (
    CIEdgeId,
    CIEvidenceId,
    CINodeId,
    CompatibilityId,
    ComponentSpecId,
    ComponentSpecLineageId,
    DecisionId,
    RuleId,
)
from component_intelligence.domain.shared.value_objects import (
    AnimationKind,
    AtomicLevel,
    Breakpoint,
    CompatibilityKind,
    ComponentStateKind,
    ComponentType,
    CompositionRuleKind,
    Confidence,
    ConsideredAlternative,
    DataKind,
    EffectLevel,
    GraphKind,
    GraphRelation,
    IOKind,
    ImpactLevel,
    Inclusion,
    InteractionKind,
    NodeKind,
    PageType,
    Percentage,
    PlacementRegion,
    Priority,
    ProvenanceKind,
    ResponsiveIntent,
    Tag,
    VisibilityKind,
)

__all__ = ["from_document", "to_document"]


def _ids(ids) -> list[str]:
    return [str(i) for i in ids]


# --------------------------------------------------------------------------- #
# Encode                                                                       #
# --------------------------------------------------------------------------- #
def _decision_doc(d: ComponentDecision) -> dict:
    return {
        "id": str(d.id), "component": d.component.value, "atomic_level": d.atomic_level.value,
        "inclusion": d.inclusion.value, "priority": int(d.priority),
        "purposes": {"business": d.purposes.business_purpose, "user": d.purposes.user_purpose,
                     "conversion": d.purposes.conversion_purpose, "trust": d.purposes.trust_purpose,
                     "evidence_ids": _ids(d.purposes.evidence_ids)},
        "impacts": {"seo": d.impacts.seo.value, "accessibility": d.impacts.accessibility.value,
                    "performance": d.impacts.performance.value,
                    "conversion_effect": d.impacts.conversion_effect.value,
                    "friction_effect": d.impacts.friction_effect.value,
                    "trust_effect": d.impacts.trust_effect.value,
                    "evidence_ids": _ids(d.impacts.evidence_ids)},
        "mobile_behaviour": d.mobile_behaviour.intent,
        "usage": {"page_affinity": [p.value for p in d.usage.page_affinity],
                  "when_to_use": list(d.usage.when_to_use),
                  "when_not_to_use": list(d.usage.when_not_to_use),
                  "conflicts_with": [c.value for c in d.usage.conflicts_with],
                  "evidence_ids": _ids(d.usage.evidence_ids)},
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
        "variants": [{"name": v.name, "purpose": v.purpose} for v in d.variants],
        "states": [{"kind": s.kind.value, "description": s.description} for s in d.states],
        "design_token_refs": list(d.design_token_refs),
        "considered_alternative": (
            {"option": d.considered_alternative.option,
             "reason_rejected": d.considered_alternative.reason_rejected}
            if d.considered_alternative else None),
        "evidence_ids": _ids(d.evidence_ids),
    }


def _graph_doc(g: CIGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [{"id": str(n.id), "kind": n.kind.value, "label": n.label,
                   "evidence_ids": _ids(n.evidence_ids)} for n in g],
        "edges": [{"id": str(e.id), "source": str(e.source), "target": str(e.target),
                   "relation": e.relation.value} for e in g.edges],
    }


def to_document(spec: ComponentCompositionSpecification) -> dict:
    """Serialize a specification to a JSON-safe document."""
    return {
        "id": str(spec.id), "lineage_id": str(spec.lineage_id), "version": spec.version,
        "project_id": spec.project_id, "created_at": spec.created_at.isoformat(),
        "components": [_decision_doc(d) for d in spec.composition],
        "compatibility": [{"id": str(link.id), "source": link.source.value, "target": link.target.value,
                           "kind": link.kind.value, "rationale": link.rationale,
                           "evidence_ids": _ids(link.evidence_ids)} for link in spec.compatibility],
        "composition_rules": [{"id": str(r.id), "kind": r.kind.value, "statement": r.statement,
                               "evidence_ids": _ids(r.evidence_ids)} for r in spec.composition_rules],
        "placement_rules": [{"id": str(r.id), "component": r.component.value, "page": r.page.value,
                             "region": r.region.value, "order": r.order,
                             "evidence_ids": _ids(r.evidence_ids)} for r in spec.placement_rules],
        "visibility_rules": [{"id": str(r.id), "component": r.component.value, "kind": r.kind.value,
                              "condition": r.condition, "evidence_ids": _ids(r.evidence_ids)}
                             for r in spec.visibility_rules],
        "responsive_rules": [{"id": str(r.id), "component": r.component.value,
                              "breakpoint": r.breakpoint.value, "intent": r.intent.value,
                              "statement": r.statement, "evidence_ids": _ids(r.evidence_ids)}
                             for r in spec.responsive_rules],
        "reuse_rules": [{"id": str(r.id), "component": r.component.value,
                         "shared_across": [p.value for p in r.shared_across], "statement": r.statement,
                         "evidence_ids": _ids(r.evidence_ids)} for r in spec.reuse_rules],
        "graphs": [_graph_doc(g) for g in spec.graphs.all()],
        "evidence": [{"id": str(e.id), "provenance": e.provenance.value, "external_ref": e.external_ref,
                      "claim": e.claim, "confidence": e.confidence.value, "statement": e.statement,
                      "source_name": e.source_name, "tags": sorted(t.value for t in e.tags)}
                     for e in spec.evidence_graph],
        "quality": {"coverage": spec.quality.coverage.value, "grounding": spec.quality.grounding.value,
                    "coherence": spec.quality.coherence.value, "confidence": spec.quality.confidence.value},
    }


# --------------------------------------------------------------------------- #
# Decode                                                                       #
# --------------------------------------------------------------------------- #
def _ev_ids(raw) -> tuple[CIEvidenceId, ...]:
    return tuple(CIEvidenceId.from_string(i) for i in raw)


def _decision(doc: dict) -> ComponentDecision:
    p, im, u = doc["purposes"], doc["impacts"], doc["usage"]
    ca = doc["considered_alternative"]
    return ComponentDecision(
        id=DecisionId.from_string(doc["id"]), component=ComponentType(doc["component"]),
        atomic_level=AtomicLevel(doc["atomic_level"]), inclusion=Inclusion(doc["inclusion"]),
        priority=Priority(doc["priority"]),
        purposes=ComponentPurposes(
            business_purpose=p["business"], user_purpose=p["user"],
            conversion_purpose=p["conversion"], trust_purpose=p["trust"],
            evidence_ids=_ev_ids(p["evidence_ids"])),
        impacts=ComponentImpacts(
            seo=ImpactLevel(im["seo"]), accessibility=ImpactLevel(im["accessibility"]),
            performance=ImpactLevel(im["performance"]),
            conversion_effect=EffectLevel(im["conversion_effect"]),
            friction_effect=EffectLevel(im["friction_effect"]),
            trust_effect=EffectLevel(im["trust_effect"]), evidence_ids=_ev_ids(im["evidence_ids"])),
        mobile_behaviour=MobileBehaviour(doc["mobile_behaviour"]),
        usage=UsageGuidance(
            page_affinity=tuple(PageType(x) for x in u["page_affinity"]),
            when_to_use=tuple(u["when_to_use"]), when_not_to_use=tuple(u["when_not_to_use"]),
            conflicts_with=tuple(ComponentType(x) for x in u["conflicts_with"]),
            evidence_ids=_ev_ids(u["evidence_ids"])),
        responsive_rules=tuple(ResponsiveRule(breakpoint=Breakpoint(r["breakpoint"]),
                               intent=ResponsiveIntent(r["intent"])) for r in doc["responsive_rules"]),
        interaction_rules=tuple(InteractionRule(kind=InteractionKind(i["kind"]), intent=i["intent"])
                                for i in doc["interaction_rules"]),
        animation_rules=tuple(AnimationRule(kind=AnimationKind(a["kind"]), intent=a["intent"])
                              for a in doc["animation_rules"]),
        dependencies=tuple(ComponentType(c) for c in doc["dependencies"]),
        required_inputs=tuple(RequiredInput(kind=DataKind(i["kind"]), description=i["description"],
                              required=i["required"]) for i in doc["required_inputs"]),
        expected_outputs=tuple(ExpectedOutput(kind=IOKind(o["kind"]), name=o["name"])
                               for o in doc["expected_outputs"]),
        success_criteria=tuple(SuccessCriterion(s) for s in doc["success_criteria"]),
        failure_criteria=tuple(FailureCriterion(s) for s in doc["failure_criteria"]),
        variants=tuple(Variant(name=v["name"], purpose=v["purpose"]) for v in doc["variants"]),
        states=tuple(ComponentState(kind=ComponentStateKind(s["kind"]), description=s["description"])
                     for s in doc["states"]),
        design_token_refs=tuple(doc["design_token_refs"]),
        considered_alternative=(ConsideredAlternative(option=ca["option"],
                                reason_rejected=ca["reason_rejected"]) if ca else None),
        evidence_ids=_ev_ids(doc["evidence_ids"]),
    )


def _graph(doc: dict) -> CIGraph:
    return CIGraph.of(
        GraphKind(doc["kind"]),
        [CINode(id=CINodeId.from_string(n["id"]), kind=NodeKind(n["kind"]), label=n["label"],
                evidence_ids=_ev_ids(n["evidence_ids"])) for n in doc["nodes"]],
        [CIEdge(id=CIEdgeId.from_string(e["id"]), source=CINodeId.from_string(e["source"]),
                target=CINodeId.from_string(e["target"]), relation=GraphRelation(e["relation"]))
         for e in doc["edges"]],
    )


def from_document(doc: dict) -> ComponentCompositionSpecification:
    """Reconstruct a specification from its document, re-validating every invariant."""
    q = doc["quality"]
    return ComponentCompositionSpecification(
        id=ComponentSpecId.from_string(doc["id"]),
        lineage_id=ComponentSpecLineageId.from_string(doc["lineage_id"]),
        version=doc["version"], project_id=doc["project_id"],
        composition=ComponentComposition.of(_decision(d) for d in doc["components"]),
        compatibility=CompatibilitySet.of(
            CompatibilityLink(id=CompatibilityId.from_string(link["id"]),
                              source=ComponentType(link["source"]), target=ComponentType(link["target"]),
                              kind=CompatibilityKind(link["kind"]), rationale=link["rationale"],
                              evidence_ids=_ev_ids(link["evidence_ids"])) for link in doc["compatibility"]),
        composition_rules=CompositionRuleSet.of(
            CompositionRule(id=RuleId.from_string(r["id"]), kind=CompositionRuleKind(r["kind"]),
                            statement=r["statement"], evidence_ids=_ev_ids(r["evidence_ids"]))
            for r in doc["composition_rules"]),
        placement_rules=PlacementRuleSet.of(
            PlacementRule(id=RuleId.from_string(r["id"]), component=ComponentType(r["component"]),
                          page=PageType(r["page"]), region=PlacementRegion(r["region"]), order=r["order"],
                          evidence_ids=_ev_ids(r["evidence_ids"])) for r in doc["placement_rules"]),
        visibility_rules=VisibilityRuleSet.of(
            VisibilityRule(id=RuleId.from_string(r["id"]), component=ComponentType(r["component"]),
                           kind=VisibilityKind(r["kind"]), condition=r["condition"],
                           evidence_ids=_ev_ids(r["evidence_ids"])) for r in doc["visibility_rules"]),
        responsive_rules=ResponsiveRuleSet.of(
            ResponsiveCompositionRule(id=RuleId.from_string(r["id"]), component=ComponentType(r["component"]),
                                      breakpoint=Breakpoint(r["breakpoint"]), intent=ResponsiveIntent(r["intent"]),
                                      statement=r["statement"], evidence_ids=_ev_ids(r["evidence_ids"]))
            for r in doc["responsive_rules"]),
        reuse_rules=ReuseRuleSet.of(
            ReuseRule(id=RuleId.from_string(r["id"]), component=ComponentType(r["component"]),
                      shared_across=tuple(PageType(p) for p in r["shared_across"]),
                      statement=r["statement"], evidence_ids=_ev_ids(r["evidence_ids"]))
            for r in doc["reuse_rules"]),
        graphs=ComponentGraphs.of(_graph(g) for g in doc["graphs"]),
        evidence_graph=EvidenceGraph.of(
            CIEvidence(id=CIEvidenceId.from_string(e["id"]), provenance=ProvenanceKind(e["provenance"]),
                       external_ref=e["external_ref"], claim=e["claim"], confidence=Confidence(e["confidence"]),
                       statement=e.get("statement", ""), source_name=e.get("source_name", ""),
                       tags=frozenset(Tag.of(t) for t in e.get("tags", ()))) for e in doc["evidence"]),
        quality=CompositionQualityMetrics(
            coverage=Percentage(q["coverage"]), grounding=Percentage(q["grounding"]),
            coherence=Percentage(q["coherence"]), confidence=Confidence(q["confidence"])),
        created_at=datetime.fromisoformat(doc["created_at"]),
    )
