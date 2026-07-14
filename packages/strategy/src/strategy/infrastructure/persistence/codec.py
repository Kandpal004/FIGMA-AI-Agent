"""Codec — serializes a BusinessStrategyReport to a JSON document and back.

A report is a deep, immutable aggregate; it is stored and loaded whole as one JSON
document. This codec is the single, exhaustive translation. Reconstruction goes through
the normal aggregate constructor, so a decoded report is re-validated (its provenance
integrity re-checked) — a corrupt document cannot yield an invalid or ungrounded
strategy.

Pure functions, no I/O.
"""

from __future__ import annotations

from datetime import datetime

from strategy.domain.analysis.opportunity import (
    BusinessOpportunity,
    OpportunityRegister,
    RevenueOpportunity,
)
from strategy.domain.analysis.risk import BusinessRisk, RiskRegister
from strategy.domain.customer.icp import IdealCustomerProfile
from strategy.domain.customer.journey import CustomerJourney, JourneyStage
from strategy.domain.customer.jtbd import JobToBeDone, JTBDSet
from strategy.domain.customer.model import CustomerModel
from strategy.domain.customer.persona import CustomerPersona, PersonaSet
from strategy.domain.customer.psychology import (
    EmotionalTrigger,
    Objection,
    PainPoint,
    PurchaseMotivation,
)
from strategy.domain.decision.decision import StrategicDecision
from strategy.domain.decision.decision_graph import DecisionEdge, DecisionGraph
from strategy.domain.decision.strategy_graph import (
    StrategyComponent,
    StrategyEdge,
    StrategyGraph,
)
from strategy.domain.evidence.evidence import EvidenceGraph, StrategyEvidence
from strategy.domain.goals.business_goal import BusinessGoal, GoalSet
from strategy.domain.messaging.brand_voice import BrandPersonality, BrandVoice
from strategy.domain.messaging.messaging import MessagingFramework, MessagingPillar
from strategy.domain.positioning.positioning import (
    BrandPositioning,
    CustomerPositioning,
    PositioningStrategy,
    VisualPositioning,
)
from strategy.domain.positioning.tier import PositioningStatement
from strategy.domain.pricing.pricing import (
    OfferStrategy,
    PricingSignal,
    PricingStrategy,
    UrgencyStrategy,
)
from strategy.domain.prioritization.priority_matrix import (
    PrioritizedItem,
    PriorityMatrix,
)
from strategy.domain.quality.quality import StrategyQualityMetrics
from strategy.domain.report.report import BusinessStrategyReport
from strategy.domain.retention.retention import RetentionLever, RetentionStrategy
from strategy.domain.shared.ids import (
    BusinessGoalId,
    BusinessOpportunityId,
    BusinessRiskId,
    CustomerPersonaId,
    DecisionEdgeId,
    JobToBeDoneId,
    MessagingPillarId,
    PrioritizedItemId,
    RevenueOpportunityId,
    StrategicDecisionId,
    StrategyComponentId,
    StrategyEdgeId,
    StrategyEvidenceId,
    StrategyReportId,
    StrategyReportLineageId,
    TrustElementId,
)
from strategy.domain.shared.value_objects import (
    Confidence,
    ConsideredAlternative,
    DecisionRelation,
    DecisionType,
    EffortScore,
    EmotionKind,
    GoalCategory,
    GoalHorizon,
    ImpactScore,
    JobType,
    JourneyPhase,
    Likelihood,
    MessagingTone,
    Money,
    OpportunityCategory,
    Percentage,
    PersonalityTrait,
    PricingPosture,
    PricingSignalKind,
    Priority,
    ProvenanceKind,
    ReachScore,
    RetentionLeverKind,
    RiskCategory,
    Severity,
    SocialProofKind,
    StrategyRelation,
    StrategyTier,
    Tag,
    TrustElementKind,
    UrgencyKind,
)
from strategy.domain.trust.trust import (
    SocialProofStrategy,
    TrustElement,
    TrustStrategy,
)
from strategy.domain.value.usp import UniqueSellingProposition
from strategy.domain.value.value_proposition import ValueProposition

__all__ = ["from_document", "to_document"]


# --------------------------- small helpers ------------------------------ #
def _ids(items) -> list[str]:
    return [str(i) for i in items]


def _eids(raw) -> tuple[StrategyEvidenceId, ...]:
    return tuple(StrategyEvidenceId.from_string(x) for x in raw)


def _alt_doc(a: ConsideredAlternative) -> dict:
    return {"option": a.option, "reason_rejected": a.reason_rejected}


def _alt(doc: dict) -> ConsideredAlternative:
    return ConsideredAlternative(option=doc["option"], reason_rejected=doc["reason_rejected"])


def _alts(raw) -> tuple[ConsideredAlternative, ...]:
    return tuple(_alt(a) for a in raw)


def _money_doc(m: Money) -> dict:
    return {"amount": m.amount, "currency": m.currency}


# --------------------------- serialize ---------------------------------- #
def to_document(r: BusinessStrategyReport) -> dict:
    return {
        "id": str(r.id),
        "lineage_id": str(r.lineage_id),
        "version": r.version,
        "project_id": r.project_id,
        "created_at": r.created_at.isoformat(),
        "quality": {
            "coverage": r.quality.coverage.value,
            "grounding": r.quality.grounding.value,
            "confidence": r.quality.confidence.value,
            "completeness": r.quality.completeness.value,
        },
        "evidence": [
            {
                "id": str(e.id),
                "provenance": e.provenance.value,
                "external_ref": e.external_ref,
                "claim": e.claim,
                "confidence": e.confidence.value,
                "statement": e.statement,
                "source_name": e.source_name,
                "tags": [t.value for t in e.tags],
            }
            for e in r.evidence_graph
        ],
        "goals": [
            {
                "id": str(g.id), "statement": g.statement, "category": g.category.value,
                "horizon": g.horizon.value, "priority": int(g.priority),
                "metric": g.metric, "target": g.target, "evidence_ids": _ids(g.evidence_ids),
            }
            for g in r.goals
        ],
        "customer": _customer_doc(r.customer),
        "positioning": _positioning_doc(r.positioning),
        "value_proposition": {
            "headline_promise": r.value_proposition.headline_promise,
            "primary_benefit": r.value_proposition.primary_benefit,
            "differentiators": list(r.value_proposition.differentiators),
            "proof_points": list(r.value_proposition.proof_points),
            "target_jtbd_ids": _ids(r.value_proposition.target_jtbd_ids),
            "evidence_ids": _ids(r.value_proposition.evidence_ids),
        },
        "usp": {
            "statement": r.usp.statement, "defensibility": r.usp.defensibility,
            "evidence_ids": _ids(r.usp.evidence_ids),
        },
        "messaging": {
            "primary_message": r.messaging.primary_message,
            "evidence_ids": _ids(r.messaging.evidence_ids),
            "pillars": [
                {"id": str(p.id), "theme": p.theme, "message": p.message,
                 "supporting_points": list(p.supporting_points),
                 "evidence_ids": _ids(p.evidence_ids)}
                for p in r.messaging.pillars
            ],
        },
        "brand_voice": {
            "tone": r.brand_voice.tone.value, "principles": list(r.brand_voice.principles),
            "avoid": list(r.brand_voice.avoid), "vocabulary": list(r.brand_voice.vocabulary),
            "evidence_ids": _ids(r.brand_voice.evidence_ids),
        },
        "brand_personality": {
            "traits": [t.value for t in r.brand_personality.traits],
            "archetype": r.brand_personality.archetype,
            "descriptors": list(r.brand_personality.descriptors),
            "evidence_ids": _ids(r.brand_personality.evidence_ids),
        },
        "trust": _trust_doc(r.trust),
        "pricing": _pricing_doc(r.pricing),
        "retention": {
            "lifecycle_focus": r.retention.lifecycle_focus,
            "evidence_ids": _ids(r.retention.evidence_ids),
            "levers": [
                {"kind": x.kind.value, "rationale": x.rationale, "priority": int(x.priority),
                 "evidence_ids": _ids(x.evidence_ids)}
                for x in r.retention.levers
            ],
        },
        "decision_graph": _decision_graph_doc(r.decision_graph),
        "strategy_graph": _strategy_graph_doc(r.strategy_graph),
        "priority_matrix": [
            {"id": str(i.id), "decision_id": str(i.decision_id), "title": i.title,
             "reach": int(i.reach), "impact": int(i.impact), "confidence": i.confidence.value,
             "effort": int(i.effort), "evidence_ids": _ids(i.evidence_ids)}
            for i in r.priority_matrix
        ],
        "risks": [
            {"id": str(rk.id), "category": rk.category.value, "description": rk.description,
             "severity": int(rk.severity), "likelihood": int(rk.likelihood),
             "mitigation": rk.mitigation, "evidence_ids": _ids(rk.evidence_ids)}
            for rk in r.risk_register
        ],
        "opportunities": {
            "business": [
                {"id": str(o.id), "category": o.category.value, "description": o.description,
                 "impact": int(o.impact), "confidence": o.confidence.value,
                 "evidence_ids": _ids(o.evidence_ids)}
                for o in r.opportunity_register.business
            ],
            "revenue": [
                {"id": str(o.id), "category": o.category.value, "description": o.description,
                 "expected_value": _money_doc(o.expected_value), "confidence": o.confidence.value,
                 "lever": o.lever, "assumptions": list(o.assumptions),
                 "evidence_ids": _ids(o.evidence_ids)}
                for o in r.opportunity_register.revenue
            ],
        },
    }


def _customer_doc(c: CustomerModel) -> dict:
    return {
        "icp": {
            "summary": c.icp.summary, "segments": list(c.icp.segments),
            "attributes": list(c.icp.attributes),
            "qualifying_signals": list(c.icp.qualifying_signals),
            "disqualifiers": list(c.icp.disqualifiers), "evidence_ids": _ids(c.icp.evidence_ids),
        },
        "personas": [
            {"id": str(p.id), "name": p.name, "archetype": p.archetype,
             "confidence": p.confidence.value, "demographics": dict(p.demographics),
             "psychographics": dict(p.psychographics), "goals": list(p.goals),
             "frustrations": list(p.frustrations), "evidence_ids": _ids(p.evidence_ids)}
            for p in c.personas
        ],
        "jobs": [
            {"id": str(j.id), "when_situation": j.when_situation, "motivation": j.motivation,
             "expected_outcome": j.expected_outcome, "job_type": j.job_type.value,
             "evidence_ids": _ids(j.evidence_ids)}
            for j in c.jobs
        ],
        "journey": [
            {"phase": s.phase.value, "customer_goal": s.customer_goal,
             "touchpoints": list(s.touchpoints), "pains": list(s.pains),
             "objections": list(s.objections), "required_trust": list(s.required_trust),
             "emotions": [e.value for e in s.emotions], "evidence_ids": _ids(s.evidence_ids)}
            for s in c.journey
        ],
        "pains": [
            {"description": p.description, "severity": int(p.severity), "phase": p.phase.value,
             "evidence_ids": _ids(p.evidence_ids)}
            for p in c.pains
        ],
        "objections": [
            {"objection": o.objection, "rebuttal_strategy": o.rebuttal_strategy,
             "evidence_ids": _ids(o.evidence_ids)}
            for o in c.objections
        ],
        "motivations": [
            {"description": m.description, "weight": m.weight.value,
             "evidence_ids": _ids(m.evidence_ids)}
            for m in c.motivations
        ],
        "emotions": [
            {"emotion": e.emotion.value, "trigger": e.trigger,
             "intended_response": e.intended_response, "evidence_ids": _ids(e.evidence_ids)}
            for e in c.emotions
        ],
    }


def _positioning_doc(p: PositioningStrategy) -> dict:
    s = p.statement
    return {
        "statement": {
            "tier": s.tier.value, "for_customer": s.for_customer, "need": s.need,
            "category": s.category, "benefit": s.benefit, "confidence": s.confidence.value,
            "unlike": s.unlike, "reason_to_believe": s.reason_to_believe,
            "considered": [_alt_doc(a) for a in s.considered], "evidence_ids": _ids(s.evidence_ids),
        },
        "brand": {
            "perception": p.brand.perception, "market_frame": p.brand.market_frame,
            "differentiators": list(p.brand.differentiators), "evidence_ids": _ids(p.brand.evidence_ids),
        },
        "customer": {
            "current_alternative": p.customer.current_alternative,
            "desired_shift": p.customer.desired_shift, "gains": list(p.customer.gains),
            "evidence_ids": _ids(p.customer.evidence_ids),
        },
        "visual": {
            "tier": p.visual.tier.value, "adjectives": list(p.visual.adjectives),
            "design_principles": list(p.visual.design_principles),
            "references_to_avoid": list(p.visual.references_to_avoid),
            "evidence_ids": _ids(p.visual.evidence_ids),
        },
    }


def _trust_doc(t: TrustStrategy) -> dict:
    return {
        "evidence_ids": _ids(t.evidence_ids),
        "elements": [
            {"id": str(e.id), "kind": e.kind.value, "rationale": e.rationale,
             "phase": e.phase.value, "priority": int(e.priority), "evidence_ids": _ids(e.evidence_ids)}
            for e in t.elements
        ],
        "social_proof": {
            "kinds": [k.value for k in t.social_proof.kinds],
            "placement_intent": t.social_proof.placement_intent,
            "evidence_ids": _ids(t.social_proof.evidence_ids),
        },
    }


def _pricing_doc(p: PricingStrategy) -> dict:
    return {
        "posture": p.posture.value, "evidence_ids": _ids(p.evidence_ids),
        "signals": [
            {"kind": s.kind.value, "rationale": s.rationale, "evidence_ids": _ids(s.evidence_ids)}
            for s in p.signals
        ],
        "offer": {
            "offers": list(p.offer.offers), "framing": p.offer.framing,
            "evidence_ids": _ids(p.offer.evidence_ids),
        },
        "urgency": {
            "kinds": [k.value for k in p.urgency.kinds],
            "honesty_guardrail": p.urgency.honesty_guardrail,
            "evidence_ids": _ids(p.urgency.evidence_ids),
        },
    }


def _decision_graph_doc(g: DecisionGraph) -> dict:
    return {
        "decisions": [
            {"id": str(d.id), "type": d.type.value, "title": d.title, "statement": d.statement,
             "confidence": d.confidence.value, "priority": int(d.priority),
             "rationale": d.rationale, "considered": [_alt_doc(a) for a in d.considered],
             "evidence_ids": _ids(d.evidence_ids)}
            for d in g
        ],
        "edges": [
            {"id": str(e.id), "source": str(e.source), "target": str(e.target),
             "relation": e.relation.value, "evidence_ids": _ids(e.evidence_ids)}
            for e in g.edges
        ],
    }


def _strategy_graph_doc(g: StrategyGraph) -> dict:
    return {
        "components": [
            {"id": str(c.id), "domain": c.domain.value, "name": c.name, "summary": c.summary}
            for c in g
        ],
        "edges": [
            {"id": str(e.id), "source": str(e.source), "target": str(e.target),
             "relation": e.relation.value}
            for e in g.edges
        ],
    }


# --------------------------- deserialize -------------------------------- #
def from_document(doc: dict) -> BusinessStrategyReport:
    evidence_graph = EvidenceGraph.of(
        StrategyEvidence(
            id=StrategyEvidenceId.from_string(e["id"]),
            provenance=ProvenanceKind(e["provenance"]),
            external_ref=e["external_ref"],
            claim=e["claim"],
            confidence=Confidence.of(e["confidence"]),
            statement=e.get("statement", ""),
            source_name=e.get("source_name", ""),
            tags=frozenset(Tag.of(t) for t in e.get("tags", ())),
        )
        for e in doc["evidence"]
    )
    goals = GoalSet.of(
        BusinessGoal(
            id=BusinessGoalId.from_string(g["id"]), statement=g["statement"],
            category=GoalCategory(g["category"]), horizon=GoalHorizon(g["horizon"]),
            priority=Priority(g["priority"]), metric=g.get("metric", ""),
            target=g.get("target", ""), evidence_ids=_eids(g["evidence_ids"]),
        )
        for g in doc["goals"]
    )
    quality = StrategyQualityMetrics(
        coverage=Percentage.of(doc["quality"]["coverage"]),
        grounding=Percentage.of(doc["quality"]["grounding"]),
        confidence=Confidence.of(doc["quality"]["confidence"]),
        completeness=Percentage.of(doc["quality"]["completeness"]),
    )

    return BusinessStrategyReport(
        id=StrategyReportId.from_string(doc["id"]),
        lineage_id=StrategyReportLineageId.from_string(doc["lineage_id"]),
        version=doc["version"],
        project_id=doc["project_id"],
        goals=goals,
        customer=_customer(doc["customer"]),
        positioning=_positioning(doc["positioning"]),
        value_proposition=_value(doc["value_proposition"]),
        usp=UniqueSellingProposition(
            statement=doc["usp"]["statement"], defensibility=doc["usp"].get("defensibility", ""),
            evidence_ids=_eids(doc["usp"]["evidence_ids"]),
        ),
        messaging=_messaging(doc["messaging"]),
        brand_voice=BrandVoice(
            tone=MessagingTone(doc["brand_voice"]["tone"]),
            principles=tuple(doc["brand_voice"].get("principles", ())),
            avoid=tuple(doc["brand_voice"].get("avoid", ())),
            vocabulary=tuple(doc["brand_voice"].get("vocabulary", ())),
            evidence_ids=_eids(doc["brand_voice"]["evidence_ids"]),
        ),
        brand_personality=BrandPersonality(
            traits=tuple(PersonalityTrait(t) for t in doc["brand_personality"]["traits"]),
            archetype=doc["brand_personality"].get("archetype", ""),
            descriptors=tuple(doc["brand_personality"].get("descriptors", ())),
            evidence_ids=_eids(doc["brand_personality"]["evidence_ids"]),
        ),
        trust=_trust(doc["trust"]),
        pricing=_pricing(doc["pricing"]),
        retention=_retention(doc["retention"]),
        decision_graph=_decision_graph(doc["decision_graph"]),
        strategy_graph=_strategy_graph(doc["strategy_graph"]),
        priority_matrix=_priority_matrix(doc["priority_matrix"]),
        risk_register=RiskRegister.of(
            BusinessRisk(
                id=BusinessRiskId.from_string(rk["id"]), category=RiskCategory(rk["category"]),
                description=rk["description"], severity=Severity(rk["severity"]),
                likelihood=Likelihood(rk["likelihood"]), mitigation=rk.get("mitigation", ""),
                evidence_ids=_eids(rk["evidence_ids"]),
            )
            for rk in doc["risks"]
        ),
        opportunity_register=_opportunities(doc["opportunities"]),
        evidence_graph=evidence_graph,
        quality=quality,
        created_at=datetime.fromisoformat(doc["created_at"]),
    )


def _customer(doc: dict) -> CustomerModel:
    icp = doc["icp"]
    return CustomerModel(
        icp=IdealCustomerProfile(
            summary=icp["summary"], segments=tuple(icp.get("segments", ())),
            attributes=tuple(icp.get("attributes", ())),
            qualifying_signals=tuple(icp.get("qualifying_signals", ())),
            disqualifiers=tuple(icp.get("disqualifiers", ())),
            evidence_ids=_eids(icp["evidence_ids"]),
        ),
        personas=PersonaSet.of(
            CustomerPersona(
                id=CustomerPersonaId.from_string(p["id"]), name=p["name"], archetype=p["archetype"],
                confidence=Confidence.of(p["confidence"]), demographics=dict(p.get("demographics", {})),
                psychographics=dict(p.get("psychographics", {})), goals=tuple(p.get("goals", ())),
                frustrations=tuple(p.get("frustrations", ())), evidence_ids=_eids(p["evidence_ids"]),
            )
            for p in doc["personas"]
        ),
        jobs=JTBDSet.of(
            JobToBeDone(
                id=JobToBeDoneId.from_string(j["id"]), when_situation=j["when_situation"],
                motivation=j["motivation"], expected_outcome=j["expected_outcome"],
                job_type=JobType(j["job_type"]), evidence_ids=_eids(j["evidence_ids"]),
            )
            for j in doc["jobs"]
        ),
        journey=CustomerJourney.of(
            JourneyStage(
                phase=JourneyPhase(s["phase"]), customer_goal=s["customer_goal"],
                touchpoints=tuple(s.get("touchpoints", ())), pains=tuple(s.get("pains", ())),
                objections=tuple(s.get("objections", ())), required_trust=tuple(s.get("required_trust", ())),
                emotions=tuple(EmotionKind(e) for e in s.get("emotions", ())),
                evidence_ids=_eids(s["evidence_ids"]),
            )
            for s in doc["journey"]
        ),
        pains=tuple(
            PainPoint(description=p["description"], severity=Severity(p["severity"]),
                      phase=JourneyPhase(p["phase"]), evidence_ids=_eids(p["evidence_ids"]))
            for p in doc["pains"]
        ),
        objections=tuple(
            Objection(objection=o["objection"], rebuttal_strategy=o["rebuttal_strategy"],
                      evidence_ids=_eids(o["evidence_ids"]))
            for o in doc["objections"]
        ),
        motivations=tuple(
            PurchaseMotivation(description=m["description"], weight=Confidence.of(m["weight"]),
                               evidence_ids=_eids(m["evidence_ids"]))
            for m in doc["motivations"]
        ),
        emotions=tuple(
            EmotionalTrigger(emotion=EmotionKind(e["emotion"]), trigger=e["trigger"],
                             intended_response=e.get("intended_response", ""),
                             evidence_ids=_eids(e["evidence_ids"]))
            for e in doc["emotions"]
        ),
    )


def _positioning(doc: dict) -> PositioningStrategy:
    s = doc["statement"]
    return PositioningStrategy(
        statement=PositioningStatement(
            tier=StrategyTier(s["tier"]), for_customer=s["for_customer"], need=s["need"],
            category=s["category"], benefit=s["benefit"], confidence=Confidence.of(s["confidence"]),
            unlike=s.get("unlike", ""), reason_to_believe=s.get("reason_to_believe", ""),
            considered=_alts(s.get("considered", ())), evidence_ids=_eids(s["evidence_ids"]),
        ),
        brand=BrandPositioning(
            perception=doc["brand"]["perception"], market_frame=doc["brand"].get("market_frame", ""),
            differentiators=tuple(doc["brand"].get("differentiators", ())),
            evidence_ids=_eids(doc["brand"]["evidence_ids"]),
        ),
        customer=CustomerPositioning(
            current_alternative=doc["customer"]["current_alternative"],
            desired_shift=doc["customer"]["desired_shift"], gains=tuple(doc["customer"].get("gains", ())),
            evidence_ids=_eids(doc["customer"]["evidence_ids"]),
        ),
        visual=VisualPositioning(
            tier=StrategyTier(doc["visual"]["tier"]), adjectives=tuple(doc["visual"].get("adjectives", ())),
            design_principles=tuple(doc["visual"].get("design_principles", ())),
            references_to_avoid=tuple(doc["visual"].get("references_to_avoid", ())),
            evidence_ids=_eids(doc["visual"]["evidence_ids"]),
        ),
    )


def _value(doc: dict) -> ValueProposition:
    return ValueProposition(
        headline_promise=doc["headline_promise"], primary_benefit=doc["primary_benefit"],
        differentiators=tuple(doc.get("differentiators", ())),
        proof_points=tuple(doc.get("proof_points", ())),
        target_jtbd_ids=tuple(JobToBeDoneId.from_string(x) for x in doc.get("target_jtbd_ids", ())),
        evidence_ids=_eids(doc["evidence_ids"]),
    )


def _messaging(doc: dict) -> MessagingFramework:
    return MessagingFramework(
        primary_message=doc["primary_message"], evidence_ids=_eids(doc["evidence_ids"]),
        pillars=tuple(
            MessagingPillar(
                id=MessagingPillarId.from_string(p["id"]), theme=p["theme"], message=p["message"],
                supporting_points=tuple(p.get("supporting_points", ())),
                evidence_ids=_eids(p["evidence_ids"]),
            )
            for p in doc["pillars"]
        ),
    )


def _trust(doc: dict) -> TrustStrategy:
    sp = doc["social_proof"]
    return TrustStrategy(
        evidence_ids=_eids(doc["evidence_ids"]),
        elements=tuple(
            TrustElement(
                id=TrustElementId.from_string(e["id"]), kind=TrustElementKind(e["kind"]),
                rationale=e["rationale"], phase=JourneyPhase(e["phase"]), priority=Priority(e["priority"]),
                evidence_ids=_eids(e["evidence_ids"]),
            )
            for e in doc["elements"]
        ),
        social_proof=SocialProofStrategy(
            kinds=tuple(SocialProofKind(k) for k in sp.get("kinds", ())),
            placement_intent=sp.get("placement_intent", ""), evidence_ids=_eids(sp["evidence_ids"]),
        ),
    )


def _pricing(doc: dict) -> PricingStrategy:
    return PricingStrategy(
        posture=PricingPosture(doc["posture"]), evidence_ids=_eids(doc["evidence_ids"]),
        signals=tuple(
            PricingSignal(kind=PricingSignalKind(s["kind"]), rationale=s.get("rationale", ""),
                          evidence_ids=_eids(s["evidence_ids"]))
            for s in doc["signals"]
        ),
        offer=OfferStrategy(
            offers=tuple(doc["offer"].get("offers", ())), framing=doc["offer"].get("framing", ""),
            evidence_ids=_eids(doc["offer"]["evidence_ids"]),
        ),
        urgency=UrgencyStrategy(
            kinds=tuple(UrgencyKind(k) for k in doc["urgency"].get("kinds", ())),
            honesty_guardrail=doc["urgency"]["honesty_guardrail"],
            evidence_ids=_eids(doc["urgency"]["evidence_ids"]),
        ),
    )


def _retention(doc: dict) -> RetentionStrategy:
    return RetentionStrategy(
        lifecycle_focus=doc.get("lifecycle_focus", ""), evidence_ids=_eids(doc["evidence_ids"]),
        levers=tuple(
            RetentionLever(kind=RetentionLeverKind(x["kind"]), rationale=x["rationale"],
                           priority=Priority(x["priority"]), evidence_ids=_eids(x["evidence_ids"]))
            for x in doc["levers"]
        ),
    )


def _decision_graph(doc: dict) -> DecisionGraph:
    decisions = tuple(
        StrategicDecision(
            id=StrategicDecisionId.from_string(d["id"]), type=DecisionType(d["type"]),
            title=d["title"], statement=d["statement"], confidence=Confidence.of(d["confidence"]),
            priority=Priority(d["priority"]), rationale=d.get("rationale", ""),
            considered=_alts(d.get("considered", ())), evidence_ids=_eids(d["evidence_ids"]),
        )
        for d in doc["decisions"]
    )
    edges = tuple(
        DecisionEdge(
            id=DecisionEdgeId.from_string(e["id"]),
            source=StrategicDecisionId.from_string(e["source"]),
            target=StrategicDecisionId.from_string(e["target"]),
            relation=DecisionRelation(e["relation"]), evidence_ids=_eids(e["evidence_ids"]),
        )
        for e in doc["edges"]
    )
    return DecisionGraph.of(decisions, edges)


def _strategy_graph(doc: dict) -> StrategyGraph:
    components = tuple(
        StrategyComponent(
            id=StrategyComponentId.from_string(c["id"]), domain=DecisionType(c["domain"]),
            name=c["name"], summary=c.get("summary", ""),
        )
        for c in doc["components"]
    )
    edges = tuple(
        StrategyEdge(
            id=StrategyEdgeId.from_string(e["id"]),
            source=StrategyComponentId.from_string(e["source"]),
            target=StrategyComponentId.from_string(e["target"]),
            relation=StrategyRelation(e["relation"]),
        )
        for e in doc["edges"]
    )
    return StrategyGraph.of(components, edges)


def _priority_matrix(doc: list) -> PriorityMatrix:
    return PriorityMatrix.of(
        PrioritizedItem(
            id=PrioritizedItemId.from_string(i["id"]),
            decision_id=StrategicDecisionId.from_string(i["decision_id"]),
            title=i["title"], reach=ReachScore(i["reach"]), impact=ImpactScore(i["impact"]),
            confidence=Confidence.of(i["confidence"]), effort=EffortScore(i["effort"]),
            evidence_ids=_eids(i["evidence_ids"]),
        )
        for i in doc
    )


def _opportunities(doc: dict) -> OpportunityRegister:
    return OpportunityRegister.of(
        business=[
            BusinessOpportunity(
                id=BusinessOpportunityId.from_string(o["id"]),
                category=OpportunityCategory(o["category"]), description=o["description"],
                impact=ImpactScore(o["impact"]), confidence=Confidence.of(o["confidence"]),
                evidence_ids=_eids(o["evidence_ids"]),
            )
            for o in doc["business"]
        ],
        revenue=[
            RevenueOpportunity(
                id=RevenueOpportunityId.from_string(o["id"]),
                category=OpportunityCategory(o["category"]), description=o["description"],
                expected_value=Money(amount=o["expected_value"]["amount"],
                                     currency=o["expected_value"]["currency"]),
                confidence=Confidence.of(o["confidence"]), lever=o.get("lever", ""),
                assumptions=tuple(o.get("assumptions", ())), evidence_ids=_eids(o["evidence_ids"]),
            )
            for o in doc["revenue"]
        ],
    )
