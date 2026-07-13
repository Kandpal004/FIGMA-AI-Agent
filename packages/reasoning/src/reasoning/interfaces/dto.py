"""Serializable view DTOs — the read models the inbound layer returns.

Callers (the Director, an API, tests) receive these flat, primitive-typed
projections of a :class:`DesignStrategy` — never the domain aggregate. Pure data
with ``from_*`` builders; no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from reasoning.domain.evidence.evidence import EvidenceRef
from reasoning.domain.graph.decision import DecisionNode
from reasoning.domain.graph.reason import ReasonNode
from reasoning.domain.risk.risk import Risk
from reasoning.domain.strategy.statement import EvidencedStatement
from reasoning.domain.strategy.strategy import DesignStrategy
from reasoning.domain.strategy.structure import SectionRecommendation
from reasoning.domain.tradeoff.tradeoff import TradeOff
from reasoning.domain.alternative.alternative import AlternativeStrategy
from reasoning.domain.strategy.gap import KnowledgeGap

__all__ = [
    "AlternativeView",
    "ConfidenceView",
    "DesignStrategyView",
    "EvidenceView",
    "GapView",
    "ReasoningTraceView",
    "RiskView",
    "SectionView",
    "StatementView",
    "TradeOffView",
]


def _statements(items: tuple[EvidencedStatement, ...]) -> list["StatementView"]:
    return [StatementView.from_statement(s) for s in items]


@dataclass(frozen=True, slots=True)
class StatementView:
    dimension: str
    statement: str
    confidence: float
    evidence_ids: list[str]

    @classmethod
    def from_statement(cls, s: EvidencedStatement) -> "StatementView":
        return cls(
            dimension=s.dimension.value,
            statement=s.statement,
            confidence=s.confidence,
            evidence_ids=[str(e) for e in s.evidence_ids],
        )


@dataclass(frozen=True, slots=True)
class EvidenceView:
    evidence_id: str
    knowledge_id: str
    entry_version_id: str
    dimension: str
    category: str
    title: str
    statement: str
    source_name: str
    confidence: float
    relevance: str

    @classmethod
    def from_ref(cls, e: EvidenceRef) -> "EvidenceView":
        return cls(
            evidence_id=str(e.id),
            knowledge_id=e.knowledge_id,
            entry_version_id=e.entry_version_id,
            dimension=e.dimension.value,
            category=e.category,
            title=e.title,
            statement=e.statement,
            source_name=e.source_name,
            confidence=e.confidence,
            relevance=e.relevance,
        )


@dataclass(frozen=True, slots=True)
class SectionView:
    name: str
    status: str
    rationale: str
    confidence: float
    order: int
    evidence_ids: list[str]

    @classmethod
    def from_section(cls, s: SectionRecommendation) -> "SectionView":
        return cls(
            name=s.name,
            status=s.status.value,
            rationale=s.rationale,
            confidence=s.confidence,
            order=s.order,
            evidence_ids=[str(e) for e in s.evidence_ids],
        )


@dataclass(frozen=True, slots=True)
class RiskView:
    category: str
    description: str
    severity: int
    likelihood: int
    score: int
    level: str
    mitigation: str

    @classmethod
    def from_risk(cls, r: Risk) -> "RiskView":
        return cls(
            category=r.category.value,
            description=r.description,
            severity=int(r.severity),
            likelihood=int(r.likelihood),
            score=r.score,
            level=r.level.value,
            mitigation=r.mitigation,
        )


@dataclass(frozen=True, slots=True)
class ConfidenceView:
    overall: float
    band: str
    by_dimension: dict[str, float]


@dataclass(frozen=True, slots=True)
class TradeOffView:
    dimension: str
    chosen: str
    sacrificed: str
    rationale: str

    @classmethod
    def from_tradeoff(cls, t: TradeOff) -> "TradeOffView":
        return cls(dimension=t.dimension.value, chosen=t.chosen,
                   sacrificed=t.sacrificed, rationale=t.rationale)


@dataclass(frozen=True, slots=True)
class AlternativeView:
    stance: str
    summary: str
    confidence: float
    key_differences: list[str]
    why_not_chosen: str

    @classmethod
    def from_alternative(cls, a: AlternativeStrategy) -> "AlternativeView":
        return cls(stance=a.stance.value, summary=a.summary, confidence=a.confidence.value,
                   key_differences=list(a.key_differences), why_not_chosen=a.why_not_chosen)


@dataclass(frozen=True, slots=True)
class GapView:
    dimension: str
    question: str
    detail: str
    suggested_action: str

    @classmethod
    def from_gap(cls, g: KnowledgeGap) -> "GapView":
        return cls(dimension=g.dimension.value, question=g.question,
                   detail=g.detail, suggested_action=g.suggested_action)


@dataclass(frozen=True, slots=True)
class DesignStrategyView:
    """The full, flat projection of a produced design strategy."""

    strategy_id: str
    run_id: str
    project_id: str
    section_id: str
    page_type: str
    stance: str
    is_actionable: bool
    has_gaps: bool
    created_at: str
    business_objective: StatementView | None
    customer_who: StatementView | None
    target_market: StatementView | None
    problems: list[StatementView]
    objections: list[StatementView]
    emotional_triggers: list[StatementView]
    trust_mechanisms: list[StatementView]
    cro_principles: list[StatementView]
    ux_principles: list[StatementView]
    accessibility_rules: list[StatementView]
    shopify_constraints: list[StatementView]
    magento_constraints: list[StatementView]
    competitors: list[StatementView]
    design_system: StatementView | None
    typography: StatementView | None
    spacing: StatementView | None
    visual_hierarchy: StatementView | None
    sections: list[SectionView]
    review_points: list[StatementView]
    reason_count: int
    decision_count: int
    evidence_count: int
    risk_overall_level: str
    risks: list[RiskView]
    confidence: ConfidenceView
    tradeoffs: list[TradeOffView]
    alternatives: list[AlternativeView]
    gaps: list[GapView]

    @classmethod
    def from_strategy(cls, s: DesignStrategy) -> "DesignStrategyView":
        conf = ConfidenceView(
            overall=s.confidence.overall.value,
            band=s.confidence.overall.band.value,
            by_dimension={d.value: c.value for d, c in s.confidence.by_dimension.items()},
        )
        return cls(
            strategy_id=str(s.id),
            run_id=str(s.run_id),
            project_id=s.project_id,
            section_id=s.section_id,
            page_type=s.page_type,
            stance=s.stance.value,
            is_actionable=s.is_actionable,
            has_gaps=s.has_gaps,
            created_at=s.created_at.isoformat() if isinstance(s.created_at, datetime) else str(s.created_at),
            business_objective=(
                StatementView.from_statement(s.business.objective)
                if s.business.objective else None
            ),
            customer_who=StatementView.from_statement(s.customer.who) if s.customer.who else None,
            target_market=(
                StatementView.from_statement(s.customer.target_market)
                if s.customer.target_market else None
            ),
            problems=_statements(s.customer.problems),
            objections=_statements(s.customer.objections),
            emotional_triggers=_statements(s.customer.emotional_triggers),
            trust_mechanisms=_statements(s.customer.trust_mechanisms),
            cro_principles=_statements(s.conversion.principles),
            ux_principles=_statements(s.experience.ux_principles),
            accessibility_rules=_statements(s.experience.accessibility_rules),
            shopify_constraints=_statements(s.platform.shopify_constraints),
            magento_constraints=_statements(s.platform.magento_constraints),
            competitors=_statements(s.competitive.competitors_to_research),
            design_system=StatementView.from_statement(s.visual.design_system) if s.visual.design_system else None,
            typography=StatementView.from_statement(s.visual.typography) if s.visual.typography else None,
            spacing=StatementView.from_statement(s.visual.spacing) if s.visual.spacing else None,
            visual_hierarchy=StatementView.from_statement(s.visual.visual_hierarchy) if s.visual.visual_hierarchy else None,
            sections=[SectionView.from_section(sec) for sec in s.structure.sections],
            review_points=_statements(s.review.review_points),
            reason_count=len(s.reason_graph),
            decision_count=s.decision_count(),
            evidence_count=s.evidence_count(),
            risk_overall_level=s.risk_assessment.overall_level.value,
            risks=[RiskView.from_risk(r) for r in s.risk_assessment.risks],
            confidence=conf,
            tradeoffs=[TradeOffView.from_tradeoff(t) for t in s.tradeoffs],
            alternatives=[AlternativeView.from_alternative(a) for a in s.alternatives],
            gaps=[GapView.from_gap(g) for g in s.gaps],
        )


@dataclass(frozen=True, slots=True)
class ReasoningTraceView:
    """An explanation of one decision: the decision, its reasons, and evidence."""

    decision_question: str
    chosen: str
    considered: list[str]
    confidence: float
    reasons: list[dict[str, object]]
    evidence: list[EvidenceView]

    @classmethod
    def build(
        cls,
        decision: DecisionNode,
        reasons: list[ReasonNode],
        evidence: list[EvidenceRef],
    ) -> "ReasoningTraceView":
        return cls(
            decision_question=decision.question,
            chosen=decision.chosen.label,
            considered=[o.label for o in decision.considered],
            confidence=decision.confidence,
            reasons=[
                {"question": r.question, "conclusion": r.conclusion, "confidence": r.confidence}
                for r in reasons
            ],
            evidence=[EvidenceView.from_ref(e) for e in evidence],
        )
