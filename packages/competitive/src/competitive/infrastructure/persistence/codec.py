"""Codec — serializes a CompetitorIntelligenceReport to a JSON document and back.

A report is a deep, immutable aggregate; it is stored and loaded whole as one JSON
document. This codec is the single, exhaustive translation. Reconstruction goes
through the normal aggregate constructor, so a decoded report is re-validated (its
evidence integrity re-checked) — a corrupt document cannot yield an invalid report.

Pure functions, no I/O.
"""

from __future__ import annotations

from datetime import datetime

from competitive.domain.competitor.competitor import Competitor
from competitive.domain.competitor.profile import CompetitorProfile, DimensionAssessment
from competitive.domain.evidence.evidence import EvidenceGraph, EvidenceRef
from competitive.domain.matrix.benchmark import BenchmarkCell, BenchmarkMatrix
from competitive.domain.matrix.best_practice import BestPractice, BestPracticeMatrix
from competitive.domain.matrix.gap import Gap, GapAnalysis
from competitive.domain.matrix.recommendation import Recommendation, RecommendationMatrix
from competitive.domain.matrix.risk import CompetitiveRisk, RiskMatrix
from competitive.domain.matrix.swot import SWOTItem, SWOTMatrix, SWOTQuadrant
from competitive.domain.pattern.pattern import PatternInstance, RecurringPattern
from competitive.domain.report.report import CompetitorIntelligenceReport
from competitive.domain.shared.ids import (
    CompetitorId,
    EvidenceId,
    PatternId,
    ProfileId,
    RecommendationId,
    ReportId,
    ReportLineageId,
    RiskId,
)
from competitive.domain.shared.value_objects import (
    CompetitorDimension as Dim,
    CompetitorTier,
    Confidence,
    Likelihood,
    PatternKind,
    Prevalence,
    RecommendationAction,
    Score,
    Severity,
)

__all__ = ["from_document", "to_document"]


def _ids(items) -> list[str]:
    return [str(i) for i in items]


def _eids(raw) -> tuple[EvidenceId, ...]:
    return tuple(EvidenceId.from_string(x) for x in raw)


# --------------------------- serialize ---------------------------------- #
def to_document(r: CompetitorIntelligenceReport) -> dict:
    return {
        "id": str(r.id),
        "lineage_id": str(r.lineage_id),
        "version": r.version,
        "industry": r.industry,
        "market": r.market,
        "country": r.country,
        "business_goals": list(r.business_goals),
        "confidence": r.confidence.value,
        "created_at": r.created_at.isoformat(),
        "competitors": [
            {"id": str(c.id), "name": c.name, "domain": c.domain, "tier": c.tier.value,
             "industry": c.industry, "market": c.market, "country": c.country,
             "positioning": c.positioning}
            for c in r.competitors
        ],
        "profiles": [
            {"id": str(p.id), "competitor_id": str(p.competitor_id),
             "assessments": [
                 {"dimension": a.dimension.value, "score": a.score.value, "summary": a.summary,
                  "confidence": a.confidence.value, "observation_count": a.observation_count}
                 for a in p.assessments],
             "strengths": list(p.strengths), "weaknesses": list(p.weaknesses),
             "opportunities": list(p.opportunities), "threats": list(p.threats)}
            for p in r.profiles
        ],
        "patterns": [
            {"id": str(p.id), "kind": p.kind.value, "dimension": p.dimension.value, "name": p.name,
             "description": p.description, "count": p.prevalence.count, "total": p.prevalence.total,
             "action": p.action.value, "confidence": p.confidence.value,
             "evidence_ids": _ids(p.evidence_ids),
             "instances": [{"competitor_id": str(i.competitor_id), "dimension": i.dimension.value,
                            "note": i.note} for i in p.instances]}
            for p in r.patterns
        ],
        "benchmark": {
            "cells": [{"competitor_id": str(c.competitor_id), "dimension": c.dimension.value,
                       "score": c.score.value} for c in r.benchmark.cells],
            "client_scores": {d.value: s.value for d, s in r.benchmark.client_scores.items()},
            "category_benchmarks": {d.value: s.value for d, s in r.benchmark.category_benchmarks.items()},
        },
        "swot": [
            {"quadrant": i.quadrant.value, "statement": i.statement, "confidence": i.confidence.value,
             "dimension": i.dimension.value if i.dimension else None, "evidence_ids": _ids(i.evidence_ids)}
            for i in r.swot.items
        ],
        "gaps": [
            {"dimension": g.dimension.value, "client_score": g.client_score.value,
             "benchmark_score": g.benchmark_score.value, "severity": int(g.severity),
             "recommended_action": g.recommended_action.value, "evidence_ids": _ids(g.evidence_ids)}
            for g in r.gap_analysis.gaps
        ],
        "best_practices": [
            {"pattern_id": str(bp.pattern_id), "kind": bp.kind.value, "dimension": bp.dimension.value,
             "name": bp.name, "description": bp.description, "count": bp.prevalence.count,
             "total": bp.prevalence.total, "confidence": bp.confidence.value,
             "evidence_ids": _ids(bp.evidence_ids)}
            for bp in r.best_practices.practices
        ],
        "risks": [
            {"id": str(rk.id), "dimension": rk.dimension.value, "description": rk.description,
             "severity": int(rk.severity), "likelihood": int(rk.likelihood),
             "threat_source": rk.threat_source, "mitigation": rk.mitigation,
             "evidence_ids": _ids(rk.evidence_ids)}
            for rk in r.risk_matrix.risks
        ],
        "recommendations": [
            {"id": str(rc.id), "action": rc.action.value, "dimension": rc.dimension.value,
             "title": rc.title, "rationale": rc.rationale, "priority": int(rc.priority),
             "confidence": rc.confidence.value, "evidence_ids": _ids(rc.evidence_ids),
             "pattern_id": str(rc.pattern_id) if rc.pattern_id else None}
            for rc in r.recommendations.recommendations
        ],
        "evidence": [
            {"id": str(e.id), "knowledge_id": e.knowledge_id, "entry_version_id": e.entry_version_id,
             "category": e.category, "title": e.title, "statement": e.statement,
             "source_name": e.source_name, "confidence": e.confidence, "relevance": e.relevance,
             "dimension": e.dimension.value if e.dimension else None}
            for e in r.evidence_graph
        ],
    }


# --------------------------- deserialize -------------------------------- #
def from_document(doc: dict) -> CompetitorIntelligenceReport:
    competitors = tuple(
        Competitor(id=CompetitorId.from_string(c["id"]), name=c["name"], domain=c.get("domain", ""),
                   tier=CompetitorTier(c["tier"]), industry=c.get("industry", ""),
                   market=c.get("market", ""), country=c.get("country", ""),
                   positioning=c.get("positioning", ""))
        for c in doc["competitors"]
    )
    profiles = tuple(
        CompetitorProfile(
            id=ProfileId.from_string(p["id"]), competitor_id=CompetitorId.from_string(p["competitor_id"]),
            assessments=tuple(
                DimensionAssessment(dimension=Dim(a["dimension"]), score=Score.of(a["score"]),
                                    summary=a["summary"], confidence=Confidence.of(a["confidence"]),
                                    observation_count=a["observation_count"])
                for a in p["assessments"]),
            strengths=tuple(p.get("strengths", ())), weaknesses=tuple(p.get("weaknesses", ())),
            opportunities=tuple(p.get("opportunities", ())), threats=tuple(p.get("threats", ())))
        for p in doc["profiles"]
    )
    patterns = tuple(
        RecurringPattern(
            id=PatternId.from_string(p["id"]), kind=PatternKind(p["kind"]), dimension=Dim(p["dimension"]),
            name=p["name"], description=p["description"],
            prevalence=Prevalence(count=p["count"], total=p["total"]),
            action=RecommendationAction(p["action"]), confidence=Confidence.of(p["confidence"]),
            instances=tuple(PatternInstance(competitor_id=CompetitorId.from_string(i["competitor_id"]),
                                            dimension=Dim(i["dimension"]), note=i.get("note", ""))
                            for i in p["instances"]),
            evidence_ids=_eids(p["evidence_ids"]))
        for p in doc["patterns"]
    )
    bm = doc["benchmark"]
    benchmark = BenchmarkMatrix.build(
        cells=[BenchmarkCell(CompetitorId.from_string(c["competitor_id"]), Dim(c["dimension"]),
                             Score.of(c["score"])) for c in bm["cells"]],
        client_scores={Dim(k): Score.of(v) for k, v in bm["client_scores"].items()},
        category_benchmarks={Dim(k): Score.of(v) for k, v in bm["category_benchmarks"].items()})
    swot = SWOTMatrix(items=tuple(
        SWOTItem(quadrant=SWOTQuadrant(i["quadrant"]), statement=i["statement"],
                 confidence=Confidence.of(i["confidence"]),
                 dimension=Dim(i["dimension"]) if i["dimension"] else None,
                 evidence_ids=_eids(i["evidence_ids"]))
        for i in doc["swot"]))
    gap_analysis = GapAnalysis(gaps=tuple(
        Gap(dimension=Dim(g["dimension"]), client_score=Score.of(g["client_score"]),
            benchmark_score=Score.of(g["benchmark_score"]), severity=Severity(g["severity"]),
            recommended_action=RecommendationAction(g["recommended_action"]),
            evidence_ids=_eids(g["evidence_ids"]))
        for g in doc["gaps"]))
    best_practices = BestPracticeMatrix(practices=tuple(
        BestPractice(pattern_id=PatternId.from_string(bp["pattern_id"]), kind=PatternKind(bp["kind"]),
                     dimension=Dim(bp["dimension"]), name=bp["name"], description=bp["description"],
                     prevalence=Prevalence(count=bp["count"], total=bp["total"]),
                     confidence=Confidence.of(bp["confidence"]), evidence_ids=_eids(bp["evidence_ids"]))
        for bp in doc["best_practices"]))
    risk_matrix = RiskMatrix(risks=tuple(
        CompetitiveRisk(id=RiskId.from_string(rk["id"]), dimension=Dim(rk["dimension"]),
                        description=rk["description"], severity=Severity(rk["severity"]),
                        likelihood=Likelihood(rk["likelihood"]), threat_source=rk.get("threat_source", ""),
                        mitigation=rk.get("mitigation", ""), evidence_ids=_eids(rk["evidence_ids"]))
        for rk in doc["risks"]))
    recommendations = RecommendationMatrix(recommendations=tuple(
        Recommendation(id=RecommendationId.from_string(rc["id"]), action=RecommendationAction(rc["action"]),
                       dimension=Dim(rc["dimension"]), title=rc["title"], rationale=rc["rationale"],
                       priority=Severity(rc["priority"]), confidence=Confidence.of(rc["confidence"]),
                       evidence_ids=_eids(rc["evidence_ids"]),
                       pattern_id=PatternId.from_string(rc["pattern_id"]) if rc["pattern_id"] else None)
        for rc in doc["recommendations"]))
    evidence_graph = EvidenceGraph.of(
        EvidenceRef(id=EvidenceId.from_string(e["id"]), knowledge_id=e["knowledge_id"],
                    entry_version_id=e["entry_version_id"], category=e["category"], title=e["title"],
                    statement=e["statement"], source_name=e["source_name"], confidence=e["confidence"],
                    relevance=e.get("relevance", ""),
                    dimension=Dim(e["dimension"]) if e["dimension"] else None)
        for e in doc["evidence"])

    return CompetitorIntelligenceReport(
        id=ReportId.from_string(doc["id"]), lineage_id=ReportLineageId.from_string(doc["lineage_id"]),
        version=doc["version"], industry=doc["industry"], market=doc["market"], country=doc["country"],
        business_goals=tuple(doc["business_goals"]), competitors=competitors, profiles=profiles,
        patterns=patterns, benchmark=benchmark, swot=swot, gap_analysis=gap_analysis,
        best_practices=best_practices, risk_matrix=risk_matrix, recommendations=recommendations,
        evidence_graph=evidence_graph, confidence=Confidence.of(doc["confidence"]),
        created_at=datetime.fromisoformat(doc["created_at"]))
