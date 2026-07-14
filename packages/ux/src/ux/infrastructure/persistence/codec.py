"""Codec — serializes a UXStrategyReport to a JSON document and back.

A report is a deep, immutable aggregate; it is stored and loaded whole as one JSON
document. This codec is the single, exhaustive translation. Reconstruction goes through
the normal aggregate constructor, so a decoded report is re-validated (its provenance
integrity re-checked, its graphs and flows re-checked for acyclicity) — a corrupt document
cannot yield an invalid or ungrounded strategy.

Pure functions, no I/O.
"""

from __future__ import annotations

from datetime import datetime

from ux.domain.analysis.dropoff import DropoffAnalysis, DropoffRisk
from ux.domain.analysis.friction import FrictionAnalysis, FrictionPoint
from ux.domain.evidence.evidence import EvidenceGraph, UXEvidence
from ux.domain.flow.flow import Flow, FlowSet, FlowStep, FlowTransition
from ux.domain.goals.goal import BusinessGoal, GoalSet, UserGoal
from ux.domain.goals.mental_model import MentalModel
from ux.domain.graph.graphs import UXGraphs
from ux.domain.graph.ux_graph import UXEdge, UXGraph, UXNode
from ux.domain.journey.journey import JourneyStage, UXJourney
from ux.domain.journey.journeys import JourneyMap
from ux.domain.laws.lens import UXLawApplication, UXLawLens
from ux.domain.page.cta import CallToAction
from ux.domain.page.objective import PageObjective, SuccessMetric
from ux.domain.page.page_strategy import PageStrategy, PageStrategySet
from ux.domain.page.priority import (
    ContentItem,
    ContentPriority,
    InformationItem,
    InformationPriority,
)
from ux.domain.quality.quality import UXQualityMetrics
from ux.domain.report.report import UXStrategyReport
from ux.domain.shared.ids import (
    BusinessGoalId,
    CallToActionId,
    FrictionPointId,
    PageStrategyId,
    SuccessMetricId,
    UXEdgeId,
    UXEvidenceId,
    UXNodeId,
    UXReportId,
    UXReportLineageId,
    UserGoalId,
)
from ux.domain.shared.value_objects import (
    Confidence,
    ContentType,
    CTAType,
    DropoffKind,
    FlowKind,
    FrictionKind,
    GraphKind,
    GraphRelation,
    Impact,
    InformationLevel,
    InteractionPattern,
    JourneyKind,
    JourneyPhase,
    MetricKind,
    NavPattern,
    NodeKind,
    PageKind,
    Percentage,
    Priority,
    ProvenanceKind,
    RuleEnforcement,
    Severity,
    Tag,
    UXLaw,
    WCAGLevel,
)
from ux.domain.strategy.strategies import (
    ContentStrategy,
    ErrorRecoveryStrategy,
    InteractionStrategy,
    NavigationStrategy,
    ProgressiveDisclosureStrategy,
    TrustStrategy,
    UXStrategies,
)

__all__ = ["from_document", "to_document"]


def _ids(items) -> list[str]:
    return [str(i) for i in items]


def _eids(raw) -> tuple[UXEvidenceId, ...]:
    return tuple(UXEvidenceId.from_string(x) for x in raw)


# --------------------------- serialize ---------------------------------- #
def to_document(r: UXStrategyReport) -> dict:
    return {
        "id": str(r.id),
        "lineage_id": str(r.lineage_id),
        "version": r.version,
        "project_id": r.project_id,
        "created_at": r.created_at.isoformat(),
        "quality": {
            "coverage": r.quality.coverage.value, "grounding": r.quality.grounding.value,
            "heuristic_validation": r.quality.heuristic_validation.value,
            "confidence": r.quality.confidence.value,
        },
        "evidence": [
            {"id": str(e.id), "provenance": e.provenance.value, "external_ref": e.external_ref,
             "claim": e.claim, "confidence": e.confidence.value, "statement": e.statement,
             "source_name": e.source_name, "tags": [t.value for t in e.tags]}
            for e in r.evidence_graph
        ],
        "goals": {
            "user": [
                {"id": str(g.id), "statement": g.statement, "is_primary": g.is_primary,
                 "priority": int(g.priority), "evidence_ids": _ids(g.evidence_ids)}
                for g in r.goals.user_goals
            ],
            "business": [
                {"id": str(g.id), "statement": g.statement, "priority": int(g.priority),
                 "evidence_ids": _ids(g.evidence_ids)}
                for g in r.goals.business_goals
            ],
        },
        "mental_model": {
            "summary": r.mental_model.summary, "expectations": list(r.mental_model.expectations),
            "familiar_patterns": list(r.mental_model.familiar_patterns),
            "anti_patterns": list(r.mental_model.anti_patterns),
            "evidence_ids": _ids(r.mental_model.evidence_ids),
        },
        "pages": [_page_doc(p) for p in r.pages],
        "journeys": {j.kind.value: _journey_doc(j) for j in r.journeys.all()},
        "flows": [_flow_doc(f) for f in r.flows],
        "strategies": _strategies_doc(r.strategies),
        "friction": [
            {"id": str(p.id), "location": p.location, "kind": p.kind.value, "severity": int(p.severity),
             "phase": p.phase.value, "page": (p.page.value if p.page else None), "remedy": p.remedy,
             "evidence_ids": _ids(p.evidence_ids)}
            for p in r.friction
        ],
        "dropoff": [
            {"stage": d.stage.value, "kind": d.kind.value, "likelihood": int(d.likelihood),
             "impact": int(d.impact), "mitigation": d.mitigation, "evidence_ids": _ids(d.evidence_ids)}
            for d in r.dropoff
        ],
        "laws": [
            {"law": a.law.value, "where_applies": a.where_applies, "rationale": a.rationale,
             "enforcement": a.enforcement.value, "wcag_level": (a.wcag_level.value if a.wcag_level else None),
             "guardrail": a.guardrail, "evidence_ids": _ids(a.evidence_ids)}
            for a in r.laws
        ],
        "graphs": {g.kind.value: _graph_doc(g) for g in r.graphs.all()},
    }


def _page_doc(p: PageStrategy) -> dict:
    return {
        "id": str(p.id), "page": p.page.value,
        "objective": {"statement": p.objective.statement, "why_it_exists": p.objective.why_it_exists,
                      "serves_user_goal": p.objective.serves_user_goal,
                      "serves_business_goal": p.objective.serves_business_goal,
                      "evidence_ids": _ids(p.objective.evidence_ids)},
        "ctas": [
            {"id": str(c.id), "type": c.type.value, "action": c.action, "label_intent": c.label_intent,
             "target": (c.target.value if c.target else None), "priority": int(c.priority),
             "evidence_ids": _ids(c.evidence_ids)}
            for c in p.ctas
        ],
        "success_metrics": [
            {"id": str(m.id), "kind": m.kind.value, "target": m.target, "priority": int(m.priority),
             "evidence_ids": _ids(m.evidence_ids)}
            for m in p.success_metrics
        ],
        "information_priority": {
            "items": [{"label": i.label, "level": i.level.value} for i in p.information_priority.items],
            "evidence_ids": _ids(p.information_priority.evidence_ids),
        },
        "content_priority": {
            "items": [{"content_type": i.content_type.value, "rank": i.rank} for i in p.content_priority.items],
            "evidence_ids": _ids(p.content_priority.evidence_ids),
        },
        "applicable_laws": [law.value for law in p.applicable_laws],
        "evidence_ids": _ids(p.evidence_ids),
    }


def _journey_doc(j: UXJourney) -> dict:
    return {
        "kind": j.kind.value,
        "stages": [
            {"phase": s.phase.value, "user_goal": s.user_goal, "task": s.task, "emotion": s.emotion,
             "friction": list(s.friction), "trust_needed": list(s.trust_needed),
             "exit_risk": int(s.exit_risk), "note": s.note, "evidence_ids": _ids(s.evidence_ids)}
            for s in j
        ],
    }


def _flow_doc(f: Flow) -> dict:
    return {
        "kind": f.kind.value,
        "steps": [
            {"order": s.order, "action": s.action, "page": (s.page.value if s.page else None),
             "is_decision_point": s.is_decision_point, "evidence_ids": _ids(s.evidence_ids)}
            for s in f
        ],
        "transitions": [
            {"from_order": t.from_order, "to_order": t.to_order, "condition": t.condition}
            for t in f.transitions
        ],
    }


def _strategies_doc(s: UXStrategies) -> dict:
    return {
        "navigation": {"pattern": s.navigation.pattern.value, "primary_nav": list(s.navigation.primary_nav),
                       "wayfinding": s.navigation.wayfinding, "principles": list(s.navigation.principles),
                       "evidence_ids": _ids(s.navigation.evidence_ids)},
        "content": {"hierarchy_intent": s.content.hierarchy_intent, "leads_with": list(s.content.leads_with),
                    "principles": list(s.content.principles), "evidence_ids": _ids(s.content.evidence_ids)},
        "interaction": {"patterns": [p.value for p in s.interaction.patterns],
                        "feedback_intent": s.interaction.feedback_intent,
                        "principles": list(s.interaction.principles), "evidence_ids": _ids(s.interaction.evidence_ids)},
        "error_recovery": {"prevention": list(s.error_recovery.prevention), "recovery": list(s.error_recovery.recovery),
                           "principles": list(s.error_recovery.principles),
                           "evidence_ids": _ids(s.error_recovery.evidence_ids)},
        "disclosure": {"reveal_first": list(s.disclosure.reveal_first),
                       "reveal_on_demand": list(s.disclosure.reveal_on_demand),
                       "principles": list(s.disclosure.principles), "evidence_ids": _ids(s.disclosure.evidence_ids)},
        "trust": {"trust_moments": list(s.trust.trust_moments), "signals": list(s.trust.signals),
                  "principles": list(s.trust.principles), "evidence_ids": _ids(s.trust.evidence_ids)},
    }


def _graph_doc(g: UXGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [{"id": str(n.id), "kind": n.kind.value, "label": n.label,
                   "evidence_ids": _ids(n.evidence_ids)} for n in g],
        "edges": [{"id": str(e.id), "source": str(e.source), "target": str(e.target),
                   "relation": e.relation.value} for e in g.edges],
    }


# --------------------------- deserialize -------------------------------- #
def from_document(doc: dict) -> UXStrategyReport:
    evidence_graph = EvidenceGraph.of(
        UXEvidence(
            id=UXEvidenceId.from_string(e["id"]), provenance=ProvenanceKind(e["provenance"]),
            external_ref=e["external_ref"], claim=e["claim"], confidence=Confidence.of(e["confidence"]),
            statement=e.get("statement", ""), source_name=e.get("source_name", ""),
            tags=frozenset(Tag.of(t) for t in e.get("tags", ())),
        )
        for e in doc["evidence"]
    )
    quality = UXQualityMetrics(
        coverage=Percentage.of(doc["quality"]["coverage"]),
        grounding=Percentage.of(doc["quality"]["grounding"]),
        heuristic_validation=Percentage.of(doc["quality"]["heuristic_validation"]),
        confidence=Confidence.of(doc["quality"]["confidence"]),
    )
    mm = doc["mental_model"]
    return UXStrategyReport(
        id=UXReportId.from_string(doc["id"]),
        lineage_id=UXReportLineageId.from_string(doc["lineage_id"]),
        version=doc["version"], project_id=doc["project_id"],
        goals=_goals(doc["goals"]),
        mental_model=MentalModel(
            summary=mm["summary"], expectations=tuple(mm.get("expectations", ())),
            familiar_patterns=tuple(mm.get("familiar_patterns", ())),
            anti_patterns=tuple(mm.get("anti_patterns", ())), evidence_ids=_eids(mm["evidence_ids"]),
        ),
        pages=PageStrategySet.of(_page(p) for p in doc["pages"]),
        journeys=_journeys(doc["journeys"]),
        flows=FlowSet.of(_flow(f) for f in doc["flows"]),
        strategies=_strategies(doc["strategies"]),
        friction=FrictionAnalysis.of(
            FrictionPoint(
                id=FrictionPointId.from_string(p["id"]), location=p["location"], kind=FrictionKind(p["kind"]),
                severity=Severity(p["severity"]), phase=JourneyPhase(p["phase"]),
                page=PageKind(p["page"]) if p.get("page") else None, remedy=p.get("remedy", ""),
                evidence_ids=_eids(p["evidence_ids"]),
            )
            for p in doc["friction"]
        ),
        dropoff=DropoffAnalysis.of(
            DropoffRisk(
                stage=JourneyPhase(d["stage"]), kind=DropoffKind(d["kind"]),
                likelihood=Severity(d["likelihood"]), impact=Impact(d["impact"]),
                mitigation=d.get("mitigation", ""), evidence_ids=_eids(d["evidence_ids"]),
            )
            for d in doc["dropoff"]
        ),
        laws=UXLawLens.of(
            UXLawApplication(
                law=UXLaw(a["law"]), where_applies=a["where_applies"], rationale=a.get("rationale", ""),
                enforcement=RuleEnforcement(a["enforcement"]),
                wcag_level=WCAGLevel(a["wcag_level"]) if a.get("wcag_level") else None,
                guardrail=a.get("guardrail", ""), evidence_ids=_eids(a["evidence_ids"]),
            )
            for a in doc["laws"]
        ),
        graphs=_graphs(doc["graphs"]),
        evidence_graph=evidence_graph, quality=quality,
        created_at=datetime.fromisoformat(doc["created_at"]),
    )


def _goals(doc: dict) -> GoalSet:
    return GoalSet.of(
        user_goals=[
            UserGoal(id=UserGoalId.from_string(g["id"]), statement=g["statement"],
                     is_primary=g.get("is_primary", False), priority=Priority(g["priority"]),
                     evidence_ids=_eids(g["evidence_ids"]))
            for g in doc["user"]
        ],
        business_goals=[
            BusinessGoal(id=BusinessGoalId.from_string(g["id"]), statement=g["statement"],
                         priority=Priority(g["priority"]), evidence_ids=_eids(g["evidence_ids"]))
            for g in doc["business"]
        ],
    )


def _page(doc: dict) -> PageStrategy:
    obj = doc["objective"]
    info = doc["information_priority"]
    content = doc["content_priority"]
    return PageStrategy(
        id=PageStrategyId.from_string(doc["id"]), page=PageKind(doc["page"]),
        objective=PageObjective(
            statement=obj["statement"], why_it_exists=obj["why_it_exists"],
            serves_user_goal=obj.get("serves_user_goal", ""), serves_business_goal=obj.get("serves_business_goal", ""),
            evidence_ids=_eids(obj["evidence_ids"]),
        ),
        ctas=tuple(
            CallToAction(id=CallToActionId.from_string(c["id"]), type=CTAType(c["type"]), action=c["action"],
                         label_intent=c.get("label_intent", ""),
                         target=PageKind(c["target"]) if c.get("target") else None,
                         priority=Priority(c["priority"]), evidence_ids=_eids(c["evidence_ids"]))
            for c in doc["ctas"]
        ),
        success_metrics=tuple(
            SuccessMetric(id=SuccessMetricId.from_string(m["id"]), kind=MetricKind(m["kind"]),
                          target=m.get("target", ""), priority=Priority(m["priority"]),
                          evidence_ids=_eids(m["evidence_ids"]))
            for m in doc["success_metrics"]
        ),
        information_priority=InformationPriority(
            items=tuple(InformationItem(label=i["label"], level=InformationLevel(i["level"])) for i in info["items"]),
            evidence_ids=_eids(info["evidence_ids"]),
        ),
        content_priority=ContentPriority(
            items=tuple(ContentItem(content_type=ContentType(i["content_type"]), rank=i["rank"]) for i in content["items"]),
            evidence_ids=_eids(content["evidence_ids"]),
        ),
        applicable_laws=tuple(UXLaw(law) for law in doc.get("applicable_laws", ())),
        evidence_ids=_eids(doc["evidence_ids"]),
    )


def _journey(doc: dict) -> UXJourney:
    return UXJourney.of(
        JourneyKind(doc["kind"]),
        (
            JourneyStage(
                phase=JourneyPhase(s["phase"]), user_goal=s["user_goal"], task=s.get("task", ""),
                emotion=s.get("emotion", ""), friction=tuple(s.get("friction", ())),
                trust_needed=tuple(s.get("trust_needed", ())), exit_risk=Severity(s["exit_risk"]),
                note=s.get("note", ""), evidence_ids=_eids(s["evidence_ids"]),
            )
            for s in doc["stages"]
        ),
    )


def _journeys(doc: dict) -> JourneyMap:
    return JourneyMap(
        user=_journey(doc["user"]), task=_journey(doc["task"]), decision=_journey(doc["decision"]),
        trust=_journey(doc["trust"]), conversion=_journey(doc["conversion"]),
        mobile=_journey(doc["mobile"]), accessibility=_journey(doc["accessibility"]),
    )


def _flow(doc: dict) -> Flow:
    return Flow.of(
        FlowKind(doc["kind"]),
        (
            FlowStep(order=s["order"], action=s["action"],
                     page=PageKind(s["page"]) if s.get("page") else None,
                     is_decision_point=s.get("is_decision_point", False), evidence_ids=_eids(s["evidence_ids"]))
            for s in doc["steps"]
        ),
        (
            FlowTransition(from_order=t["from_order"], to_order=t["to_order"], condition=t.get("condition", ""))
            for t in doc["transitions"]
        ),
    )


def _strategies(doc: dict) -> UXStrategies:
    n, c, i, e, d, t = (
        doc["navigation"], doc["content"], doc["interaction"],
        doc["error_recovery"], doc["disclosure"], doc["trust"],
    )
    return UXStrategies(
        navigation=NavigationStrategy(pattern=NavPattern(n["pattern"]), primary_nav=tuple(n.get("primary_nav", ())),
                                      wayfinding=n.get("wayfinding", ""), principles=tuple(n.get("principles", ())),
                                      evidence_ids=_eids(n["evidence_ids"])),
        content=ContentStrategy(hierarchy_intent=c["hierarchy_intent"], leads_with=tuple(c.get("leads_with", ())),
                                principles=tuple(c.get("principles", ())), evidence_ids=_eids(c["evidence_ids"])),
        interaction=InteractionStrategy(patterns=tuple(InteractionPattern(p) for p in i.get("patterns", ())),
                                        feedback_intent=i.get("feedback_intent", ""),
                                        principles=tuple(i.get("principles", ())), evidence_ids=_eids(i["evidence_ids"])),
        error_recovery=ErrorRecoveryStrategy(prevention=tuple(e.get("prevention", ())),
                                             recovery=tuple(e.get("recovery", ())),
                                             principles=tuple(e.get("principles", ())), evidence_ids=_eids(e["evidence_ids"])),
        disclosure=ProgressiveDisclosureStrategy(reveal_first=tuple(d.get("reveal_first", ())),
                                                 reveal_on_demand=tuple(d.get("reveal_on_demand", ())),
                                                 principles=tuple(d.get("principles", ())), evidence_ids=_eids(d["evidence_ids"])),
        trust=TrustStrategy(trust_moments=tuple(t.get("trust_moments", ())), signals=tuple(t.get("signals", ())),
                            principles=tuple(t.get("principles", ())), evidence_ids=_eids(t["evidence_ids"])),
    )


def _graph(doc: dict) -> UXGraph:
    nodes = tuple(
        UXNode(id=UXNodeId.from_string(n["id"]), kind=NodeKind(n["kind"]), label=n["label"],
               evidence_ids=_eids(n["evidence_ids"]))
        for n in doc["nodes"]
    )
    edges = tuple(
        UXEdge(id=UXEdgeId.from_string(e["id"]), source=UXNodeId.from_string(e["source"]),
               target=UXNodeId.from_string(e["target"]), relation=GraphRelation(e["relation"]))
        for e in doc["edges"]
    )
    return UXGraph.of(GraphKind(doc["kind"]), nodes, edges)


def _graphs(doc: dict) -> UXGraphs:
    return UXGraphs(
        decision=_graph(doc["decision"]), navigation=_graph(doc["navigation"]),
        content_hierarchy=_graph(doc["content_hierarchy"]), trust_hierarchy=_graph(doc["trust_hierarchy"]),
        interaction=_graph(doc["interaction"]),
    )
