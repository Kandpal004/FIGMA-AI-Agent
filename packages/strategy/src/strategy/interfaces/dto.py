"""Serializable view DTOs — the read models the inbound layer returns.

Callers receive these flat, primitive-typed projections of a
:class:`BusinessStrategyReport` (or a :class:`DesignDirectiveBundle`) — never the
domain aggregate. Pure data with ``from_*`` builders; no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from strategy.domain.decision.decision import StrategicDecision
from strategy.domain.report.bundle import DesignDirectiveBundle
from strategy.domain.report.report import BusinessStrategyReport

__all__ = [
    "DecisionTraceView",
    "DecisionView",
    "DesignDirectiveBundleView",
    "GoalView",
    "OpportunityView",
    "PersonaView",
    "PositioningView",
    "PriorityItemView",
    "QualityView",
    "ReportView",
    "RiskView",
]


def _ids(items) -> list[str]:
    return [str(i) for i in items]


def _iso(value) -> str:
    return value.isoformat() if isinstance(value, datetime) else str(value)


@dataclass(frozen=True, slots=True)
class QualityView:
    overall_score: float
    band: str
    coverage: float
    grounding: float
    confidence: float
    completeness: float
    is_fully_grounded: bool


@dataclass(frozen=True, slots=True)
class GoalView:
    id: str
    statement: str
    category: str
    horizon: str
    priority: int
    metric: str
    target: str
    evidence_ids: list[str]


@dataclass(frozen=True, slots=True)
class PersonaView:
    id: str
    name: str
    archetype: str
    confidence: float
    goals: list[str]
    frustrations: list[str]
    evidence_ids: list[str]


@dataclass(frozen=True, slots=True)
class PositioningView:
    tier: str
    statement: str
    brand_perception: str
    customer_shift: str
    visual_adjectives: list[str]
    design_principles: list[str]
    considered: list[dict]
    evidence_ids: list[str]


@dataclass(frozen=True, slots=True)
class DecisionView:
    id: str
    type: str
    title: str
    statement: str
    rationale: str
    confidence: float
    priority: int
    considered: list[dict]
    evidence_ids: list[str]

    @classmethod
    def from_decision(cls, d: StrategicDecision) -> DecisionView:
        return cls(
            id=str(d.id), type=d.type.value, title=d.title, statement=d.statement,
            rationale=d.rationale, confidence=d.confidence.value, priority=int(d.priority),
            considered=[
                {"option": a.option, "reason_rejected": a.reason_rejected}
                for a in d.considered
            ],
            evidence_ids=_ids(d.evidence_ids),
        )


@dataclass(frozen=True, slots=True)
class PriorityItemView:
    id: str
    decision_id: str
    title: str
    reach: int
    impact: int
    effort: int
    confidence: float
    score: float
    quadrant: str


@dataclass(frozen=True, slots=True)
class RiskView:
    id: str
    category: str
    description: str
    severity: int
    likelihood: int
    score: int
    level: str
    mitigation: str
    evidence_ids: list[str]


@dataclass(frozen=True, slots=True)
class OpportunityView:
    id: str
    kind: str
    category: str
    description: str
    impact: float
    confidence: float
    expected_value: float | None
    currency: str | None
    evidence_ids: list[str]


@dataclass(frozen=True, slots=True)
class ReportView:
    """The full, flat projection of a business strategy report."""

    report_id: str
    lineage_id: str
    version: int
    project_id: str
    tier: str
    is_usable: bool
    created_at: str
    quality: QualityView
    goals: list[GoalView]
    personas: list[PersonaView]
    icp_summary: str
    positioning: PositioningView
    value_proposition: str
    usp: str
    primary_message: str
    brand_tone: str
    decisions: list[DecisionView]
    priority_matrix: list[PriorityItemView]
    risks: list[RiskView]
    opportunities: list[OpportunityView]
    evidence_count: int

    @classmethod
    def from_report(cls, r: BusinessStrategyReport) -> ReportView:
        quality = QualityView(
            overall_score=r.quality.overall_score.value, band=r.quality.band.value,
            coverage=r.quality.coverage.value, grounding=r.quality.grounding.value,
            confidence=r.quality.confidence.value, completeness=r.quality.completeness.value,
            is_fully_grounded=r.quality.is_fully_grounded,
        )
        positioning = PositioningView(
            tier=r.positioning.tier.value, statement=r.positioning.statement.statement,
            brand_perception=r.positioning.brand.perception,
            customer_shift=r.positioning.customer.desired_shift,
            visual_adjectives=list(r.positioning.visual.adjectives),
            design_principles=list(r.positioning.visual.design_principles),
            considered=[
                {"option": a.option, "reason_rejected": a.reason_rejected}
                for a in r.positioning.statement.considered
            ],
            evidence_ids=_ids(r.positioning.evidence_ids()),
        )
        risks = [
            RiskView(
                id=str(rk.id), category=rk.category.value, description=rk.description,
                severity=int(rk.severity), likelihood=int(rk.likelihood), score=rk.score,
                level=rk.level.value, mitigation=rk.mitigation, evidence_ids=_ids(rk.evidence_ids),
            )
            for rk in r.risk_register.by_severity()
        ]
        opportunities = [
            OpportunityView(
                id=str(o.id), kind="business", category=o.category.value, description=o.description,
                impact=float(int(o.impact)), confidence=o.confidence.value,
                expected_value=None, currency=None, evidence_ids=_ids(o.evidence_ids),
            )
            for o in r.opportunity_register.business
        ] + [
            OpportunityView(
                id=str(o.id), kind="revenue", category=o.category.value, description=o.description,
                impact=0.0, confidence=o.confidence.value,
                expected_value=o.expected_value.amount, currency=o.expected_value.currency,
                evidence_ids=_ids(o.evidence_ids),
            )
            for o in r.opportunity_register.revenue
        ]
        return cls(
            report_id=str(r.id), lineage_id=str(r.lineage_id), version=r.version,
            project_id=r.project_id, tier=r.tier.value, is_usable=r.is_usable,
            created_at=_iso(r.created_at), quality=quality,
            goals=[
                GoalView(
                    id=str(g.id), statement=g.statement, category=g.category.value,
                    horizon=g.horizon.value, priority=int(g.priority), metric=g.metric,
                    target=g.target, evidence_ids=_ids(g.evidence_ids),
                )
                for g in r.goals.by_priority()
            ],
            personas=[
                PersonaView(
                    id=str(p.id), name=p.name, archetype=p.archetype, confidence=p.confidence.value,
                    goals=list(p.goals), frustrations=list(p.frustrations),
                    evidence_ids=_ids(p.evidence_ids),
                )
                for p in r.customer.personas
            ],
            icp_summary=r.customer.icp.summary,
            positioning=positioning,
            value_proposition=r.value_proposition.headline_promise,
            usp=r.usp.statement,
            primary_message=r.messaging.primary_message,
            brand_tone=r.brand_voice.tone.value,
            decisions=[DecisionView.from_decision(d) for d in r.decision_graph],
            priority_matrix=[
                PriorityItemView(
                    id=str(i.id), decision_id=str(i.decision_id), title=i.title,
                    reach=int(i.reach), impact=int(i.impact), effort=int(i.effort),
                    confidence=i.confidence.value, score=i.score, quadrant=i.quadrant.value,
                )
                for i in r.priority_matrix.ranked()
            ],
            risks=risks,
            opportunities=opportunities,
            evidence_count=r.evidence_count(),
        )


@dataclass(frozen=True, slots=True)
class DesignDirectiveBundleView:
    """The neutral brief downstream design phases consume, flattened for transport."""

    report_id: str
    project_id: str
    tier: str
    positioning_statement: str
    primary_message: str
    tone: str
    visual_adjectives: list[str]
    design_principles: list[str]
    references_to_avoid: list[str]
    emotions: list[str]
    required_trust: list[str]
    prioritized_decisions: list[DecisionView]
    is_usable: bool
    created_at: str

    @classmethod
    def from_bundle(cls, b: DesignDirectiveBundle) -> DesignDirectiveBundleView:
        return cls(
            report_id=str(b.report_id), project_id=b.project_id, tier=b.tier.value,
            positioning_statement=b.positioning_statement, primary_message=b.primary_message,
            tone=b.tone.value, visual_adjectives=list(b.visual_adjectives),
            design_principles=list(b.design_principles),
            references_to_avoid=list(b.references_to_avoid),
            emotions=[e.value for e in b.emotions],
            required_trust=[t.value for t in b.required_trust],
            prioritized_decisions=[DecisionView.from_decision(d) for d in b.prioritized_decisions],
            is_usable=b.is_usable, created_at=_iso(b.created_at),
        )


@dataclass(frozen=True, slots=True)
class DecisionTraceView:
    """An explanation of one decision: the decision, what it derives from, its evidence."""

    decision: DecisionView
    derives_from: list[DecisionView]
    evidence: list[dict]
