"""Serializable view DTOs — the read models the inbound layer returns.

Callers receive these flat, primitive-typed projections of a :class:`UXStrategyReport` (or
a :class:`DesignBriefBundle`) — never the domain aggregate. Pure data with ``from_*``
builders; no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ux.domain.graph.ux_graph import UXGraph
from ux.domain.page.page_strategy import PageStrategy
from ux.domain.report.bundle import DesignBriefBundle
from ux.domain.report.report import UXStrategyReport

__all__ = [
    "DesignBriefBundleView",
    "GraphView",
    "PageView",
    "QualityView",
    "ReportView",
    "UXTraceView",
]


def _ids(items) -> list[str]:
    return [str(i) for i in items]


def _iso(value) -> str:
    return value.isoformat() if isinstance(value, datetime) else str(value)


def _page_view(p: PageStrategy) -> dict:
    return {
        "id": str(p.id), "page": p.page.value,
        "objective": p.objective.statement, "why_it_exists": p.objective.why_it_exists,
        "primary_cta": (p.primary_cta.action if p.primary_cta else None),
        "secondary_ctas": [c.action for c in p.secondary_ctas()],
        "success_metrics": [m.kind.value for m in p.success_metrics],
        "information_priority": [{"label": i.label, "level": i.level.value}
                                 for i in p.information_priority.items],
        "content_priority": [c.content_type.value for c in p.content_priority.items],
        "applicable_laws": [law.value for law in p.applicable_laws],
        "evidence_ids": _ids(p.all_evidence_ids()),
    }


def _journey_view(j) -> dict:
    return {
        "kind": j.kind.value,
        "stages": [
            {"phase": s.phase.value, "user_goal": s.user_goal, "task": s.task,
             "emotion": s.emotion, "friction": list(s.friction), "trust_needed": list(s.trust_needed),
             "exit_risk": int(s.exit_risk), "note": s.note, "evidence_ids": _ids(s.evidence_ids)}
            for s in j
        ],
    }


def _flow_view(f) -> dict:
    return {
        "kind": f.kind.value,
        "steps": [
            {"order": s.order, "action": s.action, "page": (s.page.value if s.page else None),
             "is_decision_point": s.is_decision_point} for s in f
        ],
        "transitions": [
            {"from": t.from_order, "to": t.to_order, "condition": t.condition} for t in f.transitions
        ],
    }


def _graph_view(g: UXGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [{"id": str(n.id), "kind": n.kind.value, "label": n.label,
                   "evidence_ids": _ids(n.evidence_ids)} for n in g],
        "edges": [{"source": str(e.source), "target": str(e.target), "relation": e.relation.value}
                  for e in g.edges],
    }


@dataclass(frozen=True, slots=True)
class QualityView:
    overall_score: float
    band: str
    coverage: float
    grounding: float
    heuristic_validation: float
    confidence: float
    is_fully_grounded: bool


@dataclass(frozen=True, slots=True)
class PageView:
    page: dict


@dataclass(frozen=True, slots=True)
class GraphView:
    graph: dict


@dataclass(frozen=True, slots=True)
class ReportView:
    """The full, flat projection of a UX strategy report."""

    report_id: str
    lineage_id: str
    version: int
    project_id: str
    is_usable: bool
    created_at: str
    quality: QualityView
    primary_user_goal: str
    secondary_user_goals: list[str]
    business_goals: list[str]
    mental_model: str
    pages: list[dict]
    journeys: dict
    flows: list[dict]
    strategies: dict
    friction: list[dict]
    dropoff: list[dict]
    laws: list[dict]
    graphs: dict
    evidence_count: int

    @classmethod
    def from_report(cls, r: UXStrategyReport) -> ReportView:
        quality = QualityView(
            overall_score=r.quality.overall_score.value, band=r.quality.band.value,
            coverage=r.quality.coverage.value, grounding=r.quality.grounding.value,
            heuristic_validation=r.quality.heuristic_validation.value,
            confidence=r.quality.confidence.value, is_fully_grounded=r.quality.is_fully_grounded,
        )
        primary = r.goals.primary_user_goal
        s = r.strategies
        strategies = {
            "navigation": {"pattern": s.navigation.pattern.value, "primary_nav": list(s.navigation.primary_nav),
                           "wayfinding": s.navigation.wayfinding},
            "content": {"hierarchy_intent": s.content.hierarchy_intent, "leads_with": list(s.content.leads_with)},
            "interaction": {"patterns": [p.value for p in s.interaction.patterns],
                            "feedback_intent": s.interaction.feedback_intent},
            "error_recovery": {"prevention": list(s.error_recovery.prevention),
                               "recovery": list(s.error_recovery.recovery)},
            "disclosure": {"reveal_first": list(s.disclosure.reveal_first),
                           "reveal_on_demand": list(s.disclosure.reveal_on_demand)},
            "trust": {"trust_moments": list(s.trust.trust_moments), "signals": list(s.trust.signals)},
        }
        return cls(
            report_id=str(r.id), lineage_id=str(r.lineage_id), version=r.version,
            project_id=r.project_id, is_usable=r.is_usable, created_at=_iso(r.created_at),
            quality=quality,
            primary_user_goal=(primary.statement if primary else ""),
            secondary_user_goals=[g.statement for g in r.goals.secondary_user_goals()],
            business_goals=[g.statement for g in r.goals.business_goals],
            mental_model=r.mental_model.summary,
            pages=[_page_view(p) for p in r.pages],
            journeys={j.kind.value: _journey_view(j) for j in r.journeys.all()},
            flows=[_flow_view(f) for f in r.flows],
            strategies=strategies,
            friction=[
                {"location": fp.location, "kind": fp.kind.value, "severity": int(fp.severity),
                 "phase": fp.phase.value, "remedy": fp.remedy, "evidence_ids": _ids(fp.evidence_ids)}
                for fp in r.friction.by_severity()
            ],
            dropoff=[
                {"stage": dr.stage.value, "kind": dr.kind.value, "likelihood": int(dr.likelihood),
                 "impact": int(dr.impact), "risk_score": dr.risk_score, "mitigation": dr.mitigation,
                 "evidence_ids": _ids(dr.evidence_ids)}
                for dr in r.dropoff.by_risk()
            ],
            laws=[
                {"law": a.law.value, "where_applies": a.where_applies, "rationale": a.rationale,
                 "enforcement": a.enforcement.value,
                 "wcag_level": (a.wcag_level.value if a.wcag_level else None),
                 "evidence_ids": _ids(a.evidence_ids)}
                for a in r.laws
            ],
            graphs={g.kind.value: _graph_view(g) for g in r.graphs.all()},
            evidence_count=r.evidence_count(),
        )


@dataclass(frozen=True, slots=True)
class DesignBriefBundleView:
    """The neutral design brief downstream wireframe/design phases consume."""

    report_id: str
    project_id: str
    primary_user_goal: str
    pages: list[dict]
    navigation: dict
    conversion_journey: dict
    trust_journey: dict
    friction_points: list[dict]
    applicable_laws: list[dict]
    is_usable: bool
    created_at: str

    @classmethod
    def from_bundle(cls, b: DesignBriefBundle) -> DesignBriefBundleView:
        return cls(
            report_id=str(b.report_id), project_id=b.project_id,
            primary_user_goal=b.primary_user_goal,
            pages=[_page_view(p) for p in b.pages],
            navigation={"pattern": b.navigation.pattern.value, "primary_nav": list(b.navigation.primary_nav)},
            conversion_journey=_journey_view(b.conversion_journey),
            trust_journey=_journey_view(b.trust_journey),
            friction_points=[
                {"location": fp.location, "kind": fp.kind.value, "severity": int(fp.severity),
                 "phase": fp.phase.value} for fp in b.friction_points
            ],
            applicable_laws=[{"law": a.law.value, "where_applies": a.where_applies} for a in b.applicable_laws],
            is_usable=b.is_usable, created_at=_iso(b.created_at),
        )


@dataclass(frozen=True, slots=True)
class UXTraceView:
    """An explanation of one graph node: the node, its successors, and its evidence."""

    node: dict
    successors: list[dict]
    evidence: list[dict]
