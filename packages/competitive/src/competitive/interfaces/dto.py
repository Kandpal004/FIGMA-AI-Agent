"""Serializable view DTOs — the read models the inbound layer returns.

Callers receive these flat, primitive-typed projections of a
:class:`CompetitorIntelligenceReport` — never the domain aggregate. Pure data with
``from_*`` builders; no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from competitive.domain.evidence.evidence import EvidenceRef
from competitive.domain.matrix.recommendation import Recommendation
from competitive.domain.report.report import CompetitorIntelligenceReport

__all__ = [
    "BenchmarkCellView",
    "CompetitorView",
    "EvidenceTraceView",
    "EvidenceView",
    "GapView",
    "PatternView",
    "RecommendationView",
    "ReportView",
    "RiskView",
    "SwotItemView",
]


def _ids(items) -> list[str]:
    return [str(i) for i in items]


@dataclass(frozen=True, slots=True)
class CompetitorView:
    id: str
    name: str
    tier: str
    domain: str
    industry: str
    market: str
    country: str
    positioning: str


@dataclass(frozen=True, slots=True)
class PatternView:
    id: str
    kind: str
    dimension: str
    name: str
    description: str
    prevalence_count: int
    prevalence_total: int
    prevalence_band: str
    action: str
    exemplar_ids: list[str]
    evidence_ids: list[str]


@dataclass(frozen=True, slots=True)
class BenchmarkCellView:
    competitor_id: str
    dimension: str
    score: float
    band: str


@dataclass(frozen=True, slots=True)
class GapView:
    dimension: str
    client_score: float
    benchmark_score: float
    size: float
    severity: int
    recommended_action: str
    evidence_ids: list[str]


@dataclass(frozen=True, slots=True)
class SwotItemView:
    quadrant: str
    statement: str
    dimension: str | None
    confidence: float
    evidence_ids: list[str]


@dataclass(frozen=True, slots=True)
class RiskView:
    id: str
    dimension: str
    description: str
    severity: int
    likelihood: int
    score: int
    level: str
    threat_source: str
    mitigation: str
    evidence_ids: list[str]


@dataclass(frozen=True, slots=True)
class RecommendationView:
    id: str
    action: str
    dimension: str
    title: str
    rationale: str
    priority: int
    confidence: float
    evidence_ids: list[str]
    pattern_id: str | None

    @classmethod
    def from_recommendation(cls, r: Recommendation) -> RecommendationView:
        return cls(
            id=str(r.id), action=r.action.value, dimension=r.dimension.value, title=r.title,
            rationale=r.rationale, priority=int(r.priority), confidence=r.confidence.value,
            evidence_ids=_ids(r.evidence_ids),
            pattern_id=str(r.pattern_id) if r.pattern_id else None,
        )


@dataclass(frozen=True, slots=True)
class EvidenceView:
    evidence_id: str
    knowledge_id: str
    entry_version_id: str
    dimension: str | None
    category: str
    title: str
    statement: str
    source_name: str
    confidence: float
    relevance: str

    @classmethod
    def from_ref(cls, e: EvidenceRef) -> EvidenceView:
        return cls(
            evidence_id=str(e.id), knowledge_id=e.knowledge_id, entry_version_id=e.entry_version_id,
            dimension=e.dimension.value if e.dimension else None, category=e.category,
            title=e.title, statement=e.statement, source_name=e.source_name,
            confidence=e.confidence, relevance=e.relevance,
        )


@dataclass(frozen=True, slots=True)
class ReportView:
    """The full, flat projection of a competitor intelligence report."""

    report_id: str
    lineage_id: str
    version: int
    industry: str
    market: str
    country: str
    business_goals: list[str]
    is_actionable: bool
    confidence: float
    created_at: str
    competitors: list[CompetitorView]
    patterns_to_adopt: list[PatternView]
    patterns_to_avoid: list[PatternView]
    all_patterns: list[PatternView]
    benchmark: list[BenchmarkCellView]
    category_benchmarks: dict[str, float]
    client_scores: dict[str, float]
    gaps: list[GapView]
    overall_gap_index: float
    swot: list[SwotItemView]
    best_practices: list[PatternView]
    risks: list[RiskView]
    risk_overall_level: str
    recommendations: list[RecommendationView]
    evidence: list[EvidenceView]

    @classmethod
    def from_report(cls, r: CompetitorIntelligenceReport) -> ReportView:
        def pattern_view(p) -> PatternView:
            return PatternView(
                id=str(p.id), kind=p.kind.value, dimension=p.dimension.value, name=p.name,
                description=p.description, prevalence_count=p.prevalence.count,
                prevalence_total=p.prevalence.total, prevalence_band=p.prevalence.band.value,
                action=p.action.value, exemplar_ids=_ids(p.exemplar_competitor_ids),
                evidence_ids=_ids(p.evidence_ids),
            )

        def bp_view(bp) -> PatternView:
            return PatternView(
                id=str(bp.pattern_id), kind=bp.kind.value, dimension=bp.dimension.value, name=bp.name,
                description=bp.description, prevalence_count=bp.prevalence.count,
                prevalence_total=bp.prevalence.total, prevalence_band=bp.prevalence.band.value,
                action="adopt", exemplar_ids=[], evidence_ids=_ids(bp.evidence_ids),
            )

        return cls(
            report_id=str(r.id), lineage_id=str(r.lineage_id), version=r.version,
            industry=r.industry, market=r.market, country=r.country,
            business_goals=list(r.business_goals), is_actionable=r.is_actionable,
            confidence=r.confidence.value,
            created_at=r.created_at.isoformat() if isinstance(r.created_at, datetime) else str(r.created_at),
            competitors=[
                CompetitorView(id=str(c.id), name=c.name, tier=c.tier.value, domain=c.domain,
                               industry=c.industry, market=c.market, country=c.country,
                               positioning=c.positioning)
                for c in r.competitors
            ],
            patterns_to_adopt=[pattern_view(p) for p in r.patterns_to_adopt()],
            patterns_to_avoid=[pattern_view(p) for p in r.patterns_to_avoid()],
            all_patterns=[pattern_view(p) for p in r.patterns],
            benchmark=[
                BenchmarkCellView(
                    competitor_id=str(cell.competitor_id), dimension=cell.dimension.value,
                    score=cell.score.value,
                    band=(r.benchmark.band(cell.competitor_id, cell.dimension) or "").value
                    if r.benchmark.band(cell.competitor_id, cell.dimension) else "",
                )
                for cell in r.benchmark.cells
            ],
            category_benchmarks={d.value: s.value for d, s in r.benchmark.category_benchmarks.items()},
            client_scores={d.value: s.value for d, s in r.benchmark.client_scores.items()},
            gaps=[
                GapView(dimension=g.dimension.value, client_score=g.client_score.value,
                        benchmark_score=g.benchmark_score.value, size=g.size, severity=int(g.severity),
                        recommended_action=g.recommended_action.value, evidence_ids=_ids(g.evidence_ids))
                for g in r.gap_analysis.gaps
            ],
            overall_gap_index=r.gap_analysis.overall_gap_index,
            swot=[
                SwotItemView(quadrant=i.quadrant.value, statement=i.statement,
                             dimension=i.dimension.value if i.dimension else None,
                             confidence=i.confidence.value, evidence_ids=_ids(i.evidence_ids))
                for i in r.swot.items
            ],
            best_practices=[bp_view(bp) for bp in r.best_practices.practices],
            risks=[
                RiskView(id=str(rk.id), dimension=rk.dimension.value, description=rk.description,
                         severity=int(rk.severity), likelihood=int(rk.likelihood), score=rk.score,
                         level=rk.level.value, threat_source=rk.threat_source, mitigation=rk.mitigation,
                         evidence_ids=_ids(rk.evidence_ids))
                for rk in r.risk_matrix.risks
            ],
            risk_overall_level=r.risk_matrix.overall_level.value,
            recommendations=[RecommendationView.from_recommendation(rec)
                             for rec in r.recommendations.by_priority()],
            evidence=[EvidenceView.from_ref(e) for e in r.evidence_graph],
        )


@dataclass(frozen=True, slots=True)
class EvidenceTraceView:
    """An explanation of one recommendation: the recommendation and its evidence."""

    recommendation: RecommendationView
    evidence: list[EvidenceView]
