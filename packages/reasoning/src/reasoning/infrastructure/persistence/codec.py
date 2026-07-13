"""Codec — serializes a DesignStrategy to a JSON document and back.

A produced strategy is a deep, immutable aggregate (three graphs, nine sections,
risk/confidence/trade-offs/alternatives). It is always loaded and saved whole, so
it is persisted as one JSON document. This codec is the single, exhaustive
translation between the aggregate and that document; reconstruction goes through
the normal :class:`DesignStrategy` constructor, so a decoded strategy is
re-validated (its evidence/reason integrity re-checked) — a corrupt document
cannot yield an invalid aggregate.

Pure functions, no I/O.
"""

from __future__ import annotations

from datetime import datetime

from reasoning.domain.alternative.alternative import AlternativeStrategy
from reasoning.domain.confidence.confidence import ConfidenceScore, StrategyConfidence
from reasoning.domain.evidence.evidence import EvidenceGraph, EvidenceRef
from reasoning.domain.graph.decision import DecisionGraph, DecisionNode, DecisionOption
from reasoning.domain.graph.reason import ReasonGraph, ReasonNode
from reasoning.domain.request.request import ReasoningContext  # noqa: F401  (documents linkage)
from reasoning.domain.risk.risk import Risk, RiskAssessment, RiskCategory
from reasoning.domain.shared.ids import (
    AlternativeId,
    DecisionNodeId,
    EvidenceId,
    ReasonNodeId,
    ReasoningRunId,
    RiskId,
    StrategyId,
    TradeOffId,
)
from reasoning.domain.shared.value_objects import (
    Likelihood,
    ReasoningDimension,
    Severity,
    StrategyStance,
)
from reasoning.domain.strategy.gap import KnowledgeGap
from reasoning.domain.strategy.sections import (
    BusinessObjective,
    CompetitiveStrategy,
    ConversionStrategy,
    CustomerProfile,
    ExperienceStrategy,
    PlatformStrategy,
    ReviewStrategy,
    VisualStrategy,
)
from reasoning.domain.strategy.statement import EvidencedStatement
from reasoning.domain.strategy.strategy import DesignStrategy
from reasoning.domain.strategy.structure import (
    SectionRecommendation,
    SectionStatus,
    StructureStrategy,
)
from reasoning.domain.tradeoff.tradeoff import TradeOff

__all__ = ["from_document", "to_document"]


# --------------------------- helpers ------------------------------------ #
def _ids(items) -> list[str]:
    return [str(i) for i in items]


def _stmt(s: EvidencedStatement) -> dict:
    return {
        "dimension": s.dimension.value,
        "statement": s.statement,
        "evidence_ids": _ids(s.evidence_ids),
        "confidence": s.confidence,
        "reason_id": str(s.reason_id) if s.reason_id else None,
    }


def _stmts(items) -> list[dict]:
    return [_stmt(s) for s in items]


def _option(o: DecisionOption) -> dict:
    return {"label": o.label, "evidence_ids": _ids(o.evidence_ids), "score": o.score, "note": o.note}


# --------------------------- serialize ---------------------------------- #
def to_document(s: DesignStrategy) -> dict:
    """Serialize a strategy to a JSON-safe document."""
    return {
        "id": str(s.id),
        "run_id": str(s.run_id),
        "project_id": s.project_id,
        "section_id": s.section_id,
        "page_type": s.page_type,
        "stance": s.stance.value,
        "created_at": s.created_at.isoformat(),
        "evidence": [
            {
                "id": str(e.id), "knowledge_id": e.knowledge_id,
                "entry_version_id": e.entry_version_id, "dimension": e.dimension.value,
                "category": e.category, "title": e.title, "statement": e.statement,
                "source_name": e.source_name, "confidence": e.confidence, "relevance": e.relevance,
            }
            for e in s.evidence_graph
        ],
        "reasons": [
            {
                "id": str(r.id), "dimension": r.dimension.value, "question": r.question,
                "conclusion": r.conclusion, "confidence": r.confidence,
                "evidence_ids": _ids(r.evidence_ids), "premise_ids": _ids(r.premise_ids),
            }
            for r in s.reason_graph
        ],
        "decisions": [
            {
                "id": str(d.id), "dimension": d.dimension.value, "question": d.question,
                "chosen": _option(d.chosen), "considered": [_option(o) for o in d.considered],
                "confidence": d.confidence, "reason_ids": _ids(d.reason_ids),
                "depends_on": _ids(d.depends_on),
            }
            for d in s.decision_graph
        ],
        "structure": [
            {
                "name": sec.name, "status": sec.status.value, "rationale": sec.rationale,
                "evidence_ids": _ids(sec.evidence_ids), "confidence": sec.confidence, "order": sec.order,
            }
            for sec in s.structure.sections
        ],
        "business": {
            "objective": _stmt(s.business.objective) if s.business.objective else None,
            "secondary": _stmts(s.business.secondary),
        },
        "customer": {
            "who": _stmt(s.customer.who) if s.customer.who else None,
            "target_market": _stmt(s.customer.target_market) if s.customer.target_market else None,
            "problems": _stmts(s.customer.problems),
            "objections": _stmts(s.customer.objections),
            "emotional_triggers": _stmts(s.customer.emotional_triggers),
            "trust_mechanisms": _stmts(s.customer.trust_mechanisms),
        },
        "conversion": {"principles": _stmts(s.conversion.principles)},
        "experience": {
            "ux_principles": _stmts(s.experience.ux_principles),
            "accessibility_rules": _stmts(s.experience.accessibility_rules),
        },
        "platform": {
            "shopify_constraints": _stmts(s.platform.shopify_constraints),
            "magento_constraints": _stmts(s.platform.magento_constraints),
        },
        "competitive": {"competitors_to_research": _stmts(s.competitive.competitors_to_research)},
        "visual": {
            "design_system": _stmt(s.visual.design_system) if s.visual.design_system else None,
            "typography": _stmt(s.visual.typography) if s.visual.typography else None,
            "spacing": _stmt(s.visual.spacing) if s.visual.spacing else None,
            "visual_hierarchy": _stmt(s.visual.visual_hierarchy) if s.visual.visual_hierarchy else None,
        },
        "review": {"review_points": _stmts(s.review.review_points)},
        "risks": [
            {
                "id": str(r.id), "category": r.category.value, "description": r.description,
                "severity": int(r.severity), "likelihood": int(r.likelihood),
                "threatens": _ids(r.threatens), "mitigation": r.mitigation,
                "evidence_ids": _ids(r.evidence_ids),
            }
            for r in s.risk_assessment.risks
        ],
        "confidence": {
            "overall": s.confidence.overall.value,
            "by_dimension": {d.value: c.value for d, c in s.confidence.by_dimension.items()},
        },
        "tradeoffs": [
            {
                "id": str(t.id), "dimension": t.dimension.value, "chosen": t.chosen,
                "sacrificed": t.sacrificed, "rationale": t.rationale,
                "decision_id": str(t.decision_id) if t.decision_id else None,
                "evidence_ids": _ids(t.evidence_ids),
            }
            for t in s.tradeoffs
        ],
        "alternatives": [
            {
                "id": str(a.id), "stance": a.stance.value, "summary": a.summary,
                "confidence": a.confidence.value, "key_differences": list(a.key_differences),
                "why_not_chosen": a.why_not_chosen,
            }
            for a in s.alternatives
        ],
        "gaps": [
            {
                "dimension": g.dimension.value, "question": g.question,
                "detail": g.detail, "suggested_action": g.suggested_action,
            }
            for g in s.gaps
        ],
    }


# --------------------------- deserialize -------------------------------- #
def _rstmt(d: dict | None) -> EvidencedStatement | None:
    if d is None:
        return None
    return EvidencedStatement(
        dimension=ReasoningDimension(d["dimension"]),
        statement=d["statement"],
        evidence_ids=tuple(EvidenceId.from_string(x) for x in d["evidence_ids"]),
        confidence=d["confidence"],
        reason_id=ReasonNodeId.from_string(d["reason_id"]) if d["reason_id"] else None,
    )


def _rstmts(items) -> tuple[EvidencedStatement, ...]:
    return tuple(_rstmt(d) for d in items)  # type: ignore[misc]


def _roption(d: dict) -> DecisionOption:
    return DecisionOption(
        label=d["label"],
        evidence_ids=tuple(EvidenceId.from_string(x) for x in d["evidence_ids"]),
        score=d["score"],
        note=d.get("note", ""),
    )


def from_document(doc: dict) -> DesignStrategy:
    """Reconstruct a strategy from its document (re-validated on construction)."""
    evidence_graph = EvidenceGraph.of(
        EvidenceRef(
            id=EvidenceId.from_string(e["id"]), knowledge_id=e["knowledge_id"],
            entry_version_id=e["entry_version_id"], dimension=ReasoningDimension(e["dimension"]),
            category=e["category"], title=e["title"], statement=e["statement"],
            source_name=e["source_name"], confidence=e["confidence"], relevance=e.get("relevance", ""),
        )
        for e in doc["evidence"]
    )
    reason_graph = ReasonGraph.of(
        ReasonNode(
            id=ReasonNodeId.from_string(r["id"]), dimension=ReasoningDimension(r["dimension"]),
            question=r["question"], conclusion=r["conclusion"], confidence=r["confidence"],
            evidence_ids=tuple(EvidenceId.from_string(x) for x in r["evidence_ids"]),
            premise_ids=tuple(ReasonNodeId.from_string(x) for x in r["premise_ids"]),
        )
        for r in doc["reasons"]
    )
    decision_graph = DecisionGraph.of(
        DecisionNode(
            id=DecisionNodeId.from_string(d["id"]), dimension=ReasoningDimension(d["dimension"]),
            question=d["question"], chosen=_roption(d["chosen"]),
            considered=tuple(_roption(o) for o in d["considered"]), confidence=d["confidence"],
            reason_ids=tuple(ReasonNodeId.from_string(x) for x in d["reason_ids"]),
            depends_on=tuple(DecisionNodeId.from_string(x) for x in d["depends_on"]),
        )
        for d in doc["decisions"]
    )
    structure = StructureStrategy(sections=tuple(
        SectionRecommendation(
            name=sec["name"], status=SectionStatus(sec["status"]), rationale=sec["rationale"],
            evidence_ids=tuple(EvidenceId.from_string(x) for x in sec["evidence_ids"]),
            confidence=sec["confidence"], order=sec["order"],
        )
        for sec in doc["structure"]
    ))
    risks = tuple(
        Risk(
            id=RiskId.from_string(r["id"]), category=RiskCategory(r["category"]),
            description=r["description"], severity=Severity(r["severity"]),
            likelihood=Likelihood(r["likelihood"]),
            threatens=tuple(DecisionNodeId.from_string(x) for x in r["threatens"]),
            mitigation=r.get("mitigation", ""),
            evidence_ids=tuple(EvidenceId.from_string(x) for x in r["evidence_ids"]),
        )
        for r in doc["risks"]
    )
    confidence = StrategyConfidence(
        overall=ConfidenceScore.of(doc["confidence"]["overall"]),
        by_dimension={
            ReasoningDimension(k): ConfidenceScore.of(v)
            for k, v in doc["confidence"]["by_dimension"].items()
        },
    )
    tradeoffs = tuple(
        TradeOff(
            id=TradeOffId.from_string(t["id"]), dimension=ReasoningDimension(t["dimension"]),
            chosen=t["chosen"], sacrificed=t["sacrificed"], rationale=t["rationale"],
            decision_id=DecisionNodeId.from_string(t["decision_id"]) if t["decision_id"] else None,
            evidence_ids=tuple(EvidenceId.from_string(x) for x in t["evidence_ids"]),
        )
        for t in doc["tradeoffs"]
    )
    alternatives = tuple(
        AlternativeStrategy(
            id=AlternativeId.from_string(a["id"]), stance=StrategyStance(a["stance"]),
            summary=a["summary"], confidence=ConfidenceScore.of(a["confidence"]),
            key_differences=tuple(a["key_differences"]), why_not_chosen=a.get("why_not_chosen", ""),
        )
        for a in doc["alternatives"]
    )
    gaps = tuple(
        KnowledgeGap(
            dimension=ReasoningDimension(g["dimension"]), question=g["question"],
            detail=g.get("detail", ""), suggested_action=g.get("suggested_action", ""),
        )
        for g in doc["gaps"]
    )

    b, c, cv, ex, pf, cp, vi, rv = (
        doc["business"], doc["customer"], doc["conversion"], doc["experience"],
        doc["platform"], doc["competitive"], doc["visual"], doc["review"],
    )
    return DesignStrategy(
        id=StrategyId.from_string(doc["id"]),
        run_id=ReasoningRunId.from_string(doc["run_id"]),
        project_id=doc["project_id"], section_id=doc["section_id"], page_type=doc["page_type"],
        stance=StrategyStance(doc["stance"]),
        business=BusinessObjective(objective=_rstmt(b["objective"]), secondary=_rstmts(b["secondary"])),
        customer=CustomerProfile(
            who=_rstmt(c["who"]), target_market=_rstmt(c["target_market"]),
            problems=_rstmts(c["problems"]), objections=_rstmts(c["objections"]),
            emotional_triggers=_rstmts(c["emotional_triggers"]),
            trust_mechanisms=_rstmts(c["trust_mechanisms"]),
        ),
        conversion=ConversionStrategy(principles=_rstmts(cv["principles"])),
        experience=ExperienceStrategy(
            ux_principles=_rstmts(ex["ux_principles"]),
            accessibility_rules=_rstmts(ex["accessibility_rules"]),
        ),
        platform=PlatformStrategy(
            shopify_constraints=_rstmts(pf["shopify_constraints"]),
            magento_constraints=_rstmts(pf["magento_constraints"]),
        ),
        competitive=CompetitiveStrategy(competitors_to_research=_rstmts(cp["competitors_to_research"])),
        visual=VisualStrategy(
            design_system=_rstmt(vi["design_system"]), typography=_rstmt(vi["typography"]),
            spacing=_rstmt(vi["spacing"]), visual_hierarchy=_rstmt(vi["visual_hierarchy"]),
        ),
        structure=structure,
        review=ReviewStrategy(review_points=_rstmts(rv["review_points"])),
        reason_graph=reason_graph, decision_graph=decision_graph, evidence_graph=evidence_graph,
        risk_assessment=RiskAssessment(risks=risks), confidence=confidence,
        tradeoffs=tradeoffs, alternatives=alternatives, gaps=gaps,
        created_at=datetime.fromisoformat(doc["created_at"]),
    )
