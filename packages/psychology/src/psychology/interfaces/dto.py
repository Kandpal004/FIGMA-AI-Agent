"""Serializable view DTOs — the read models the inbound layer returns.

Callers receive these flat, primitive-typed projections of a
:class:`CustomerPsychologyReport` (or a :class:`UXDirectiveBundle`) — never the domain
aggregate. Pure data with ``from_*`` builders; no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from psychology.domain.graph.psych_graph import PsychGraph
from psychology.domain.matrices.matrices import PsychologyMatrices
from psychology.domain.report.bundle import UXDirectiveBundle
from psychology.domain.report.report import CustomerPsychologyReport

__all__ = [
    "GraphView",
    "MatrixView",
    "ProfileView",
    "PsychologyTraceView",
    "QualityView",
    "ReportView",
    "UXDirectiveBundleView",
]


def _ids(items) -> list[str]:
    return [str(i) for i in items]


def _iso(value) -> str:
    return value.isoformat() if isinstance(value, datetime) else str(value)


def _matrices_view(m: PsychologyMatrices) -> dict:
    return {
        "objection": [
            {"objection": c.objection, "kind": c.kind.value, "phase": c.phase.value,
             "resolution": c.resolution_strategy, "evidence_ids": _ids(c.evidence_ids)}
            for c in m.objection
        ],
        "trust": [
            {"requirement": c.requirement, "kind": c.kind.value, "signal": c.signal_needed,
             "phase": c.phase.value, "salience": int(c.salience), "evidence_ids": _ids(c.evidence_ids)}
            for c in m.trust
        ],
        "motivation": [
            {"motivation": c.motivation, "need": c.maslow_need.value, "driver": c.driver_kind.value,
             "intensity": int(c.intensity), "evidence_ids": _ids(c.evidence_ids)}
            for c in m.motivation
        ],
        "emotion": [
            {"emotion": c.emotion.value, "phase": c.phase.value, "trigger": c.trigger,
             "intended_shift": c.intended_shift.value, "evidence_ids": _ids(c.evidence_ids)}
            for c in m.emotion
        ],
        "behavior": [
            {"behavior": c.target_behavior, "motivation": int(c.motivation), "ability": int(c.ability),
             "prompt": c.prompt, "feasibility": c.feasibility.value, "evidence_ids": _ids(c.evidence_ids)}
            for c in m.behavior
        ],
        "risk": [
            {"risk": c.risk, "kind": c.kind.value, "likelihood": int(c.likelihood),
             "impact": int(c.impact), "severity": c.severity, "mitigation": c.mitigation,
             "evidence_ids": _ids(c.evidence_ids)}
            for c in m.risk
        ],
        "value": [
            {"value_perception": c.value_perception, "price_relation": c.price_relation,
             "framing": c.framing, "evidence_ids": _ids(c.evidence_ids)}
            for c in m.value
        ],
        "confidence": [
            {"factor": c.factor, "current_level": int(c.current_level), "lever": c.lever,
             "evidence_ids": _ids(c.evidence_ids)}
            for c in m.confidence
        ],
        "retention": [
            {"driver": c.driver, "lifecycle_stage": c.lifecycle_stage, "mechanism": c.mechanism,
             "evidence_ids": _ids(c.evidence_ids)}
            for c in m.retention
        ],
    }


def _graph_view(g: PsychGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [
            {"id": str(n.id), "kind": n.kind.value, "label": n.label, "evidence_ids": _ids(n.evidence_ids)}
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
    coverage: float
    grounding: float
    framework_validation: float
    confidence: float
    is_fully_grounded: bool


@dataclass(frozen=True, slots=True)
class ProfileView:
    target_customer: str
    awareness: str
    sophistication: str
    intent: str
    confidence_level: int
    motivations: list[str]
    anxieties: list[str]
    frictions: list[str]
    risks: list[str]
    trust_requirements: list[str]
    decision_triggers: list[str]
    drivers: dict[str, list[str]]


@dataclass(frozen=True, slots=True)
class MatrixView:
    matrices: dict


@dataclass(frozen=True, slots=True)
class GraphView:
    graph: dict


@dataclass(frozen=True, slots=True)
class ReportView:
    """The full, flat projection of a customer psychology report."""

    report_id: str
    lineage_id: str
    version: int
    project_id: str
    awareness: str
    sophistication: str
    is_usable: bool
    created_at: str
    quality: QualityView
    profile: ProfileView
    personas: list[dict]
    buying_personas: list[dict]
    jtbd: list[dict]
    buying_journey: list[dict]
    decision_journey: list[dict]
    matrices: dict
    frameworks: dict
    graphs: dict
    evidence_count: int

    @classmethod
    def from_report(cls, r: CustomerPsychologyReport) -> ReportView:
        p = r.profile
        quality = QualityView(
            overall_score=r.quality.overall_score.value, band=r.quality.band.value,
            coverage=r.quality.coverage.value, grounding=r.quality.grounding.value,
            framework_validation=r.quality.framework_validation.value,
            confidence=r.quality.confidence.value, is_fully_grounded=r.quality.is_fully_grounded,
        )
        drivers: dict[str, list[str]] = {}
        for d in p.drivers:
            drivers.setdefault(d.kind.value, []).append(d.description)
        profile = ProfileView(
            target_customer=p.target_customer, awareness=p.awareness.value,
            sophistication=p.sophistication.value, intent=p.intent.value,
            confidence_level=int(p.confidence.level),
            motivations=[m.description for m in p.motivations],
            anxieties=[a.description for a in p.anxieties],
            frictions=[f.description for f in p.frictions],
            risks=[rk.description for rk in p.risks],
            trust_requirements=[t.description for t in p.trust_requirements],
            decision_triggers=[t.description for t in p.decision_triggers],
            drivers=drivers,
        )
        frameworks = {
            "applied": sorted(f.value for f in r.frameworks.applied_frameworks()),
            "maslow": {"dominant_need": r.frameworks.maslow.dominant_need.value,
                       "active_needs": [n.value for n in r.frameworks.maslow.active_needs]},
            "fogg": {"primary_lever": r.frameworks.fogg.primary_lever.value,
                     "conclusion": r.frameworks.fogg.conclusion},
            "hook": {"trigger": r.frameworks.hook.trigger, "action": r.frameworks.hook.action,
                     "variable_reward": r.frameworks.hook.variable_reward,
                     "investment": r.frameworks.hook.investment},
            "principles": [{"kind": pr.kind.value, "application": pr.application}
                           for pr in r.frameworks.principles],
        }
        graphs = {g.kind.value: _graph_view(g) for g in r.graphs.all()}
        return cls(
            report_id=str(r.id), lineage_id=str(r.lineage_id), version=r.version,
            project_id=r.project_id, awareness=p.awareness.value, sophistication=p.sophistication.value,
            is_usable=r.is_usable, created_at=_iso(r.created_at), quality=quality, profile=profile,
            personas=[
                {"id": str(x.id), "name": x.name, "archetype": x.archetype, "awareness": x.awareness.value,
                 "goals": list(x.goals), "fears": list(x.fears), "evidence_ids": _ids(x.evidence_ids)}
                for x in r.personas
            ],
            buying_personas=[
                {"id": str(x.id), "name": x.name, "role": x.role.value, "must_believe": list(x.must_believe),
                 "blocked_by": list(x.blocked_by), "evidence_ids": _ids(x.evidence_ids)}
                for x in r.buying_personas
            ],
            jtbd=[
                {"statement": j.statement, "type": j.job_type.value,
                 "net_progress": j.forces.net_progress, "favours_switch": j.forces.favours_switch,
                 "evidence_ids": _ids(j.evidence_ids)}
                for j in r.jobs
            ],
            buying_journey=[
                {"phase": s.phase.value, "goal": s.customer_goal, "driver": s.dominant_driver.value,
                 "emotion": s.emotion.value, "anxieties": list(s.anxieties), "frictions": list(s.frictions),
                 "trust_needed": list(s.trust_needed), "evidence_ids": _ids(s.evidence_ids)}
                for s in r.buying_journey
            ],
            decision_journey=[
                {"order": s.order, "commitment": s.commitment, "emotion": s.emotion.value,
                 "peak_end_weight": int(s.peak_end_weight), "is_peak": s.is_peak_moment,
                 "anxiety": s.anxiety, "evidence_ids": _ids(s.evidence_ids)}
                for s in r.decision_journey
            ],
            matrices=_matrices_view(r.matrices),
            frameworks=frameworks,
            graphs=graphs,
            evidence_count=r.evidence_count(),
        )


@dataclass(frozen=True, slots=True)
class UXDirectiveBundleView:
    """The neutral UX/CRO brief downstream design phases consume, flattened for transport."""

    report_id: str
    project_id: str
    target_customer: str
    awareness: str
    sophistication: str
    intent: str
    journey_stages: list[dict]
    objections: list[dict]
    decision_triggers: list[dict]
    feasible_behaviors: list[dict]
    is_usable: bool
    created_at: str

    @classmethod
    def from_bundle(cls, b: UXDirectiveBundle) -> UXDirectiveBundleView:
        return cls(
            report_id=str(b.report_id), project_id=b.project_id, target_customer=b.target_customer,
            awareness=b.awareness.value, sophistication=b.sophistication.value, intent=b.intent.value,
            journey_stages=[
                {"phase": s.phase.value, "goal": s.customer_goal, "emotion": s.emotion.value,
                 "anxieties": list(s.anxieties), "frictions": list(s.frictions),
                 "trust_needed": list(s.trust_needed)}
                for s in b.journey_stages
            ],
            objections=[
                {"objection": o.objection, "resolution": o.resolution_strategy, "phase": o.phase.value}
                for o in b.objections
            ],
            decision_triggers=[
                {"description": t.description, "activates": t.activates.value, "phase": t.phase.value}
                for t in b.decision_triggers
            ],
            feasible_behaviors=[
                {"behavior": c.target_behavior, "prompt": c.prompt, "feasibility": c.feasibility.value}
                for c in b.feasible_behaviors
            ],
            is_usable=b.is_usable, created_at=_iso(b.created_at),
        )


@dataclass(frozen=True, slots=True)
class PsychologyTraceView:
    """An explanation of one graph node: the node, what it points to, and its evidence."""

    node: dict
    successors: list[dict]
    evidence: list[dict]
