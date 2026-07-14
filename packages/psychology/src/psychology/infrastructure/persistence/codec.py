"""Codec — serializes a CustomerPsychologyReport to a JSON document and back.

A report is a deep, immutable aggregate; it is stored and loaded whole as one JSON
document. This codec is the single, exhaustive translation. Reconstruction goes through
the normal aggregate constructor, so a decoded report is re-validated (its provenance
integrity re-checked, its graphs re-checked for acyclicity) — a corrupt document cannot
yield an invalid or ungrounded model.

Pure functions, no I/O.
"""

from __future__ import annotations

from datetime import datetime

from psychology.domain.evidence.evidence import EvidenceGraph, PsychologyEvidence
from psychology.domain.frameworks.behavioral_economics import (
    BehavioralPrinciple,
    BehavioralPrincipleSet,
)
from psychology.domain.frameworks.fogg import FoggAnalysis, FoggLever
from psychology.domain.frameworks.hook import HookLoop
from psychology.domain.frameworks.lens import FrameworkLens
from psychology.domain.frameworks.maslow import MaslowMapping
from psychology.domain.graph.graphs import PsychologyGraphs
from psychology.domain.graph.psych_graph import PsychEdge, PsychGraph, PsychNode
from psychology.domain.journey.buying_journey import BuyingJourney, BuyingStage
from psychology.domain.journey.decision_journey import DecisionJourney, DecisionStage
from psychology.domain.matrices.cells import (
    BehaviorCell,
    ConfidenceCell,
    EmotionCell,
    MotivationCell,
    ObjectionCell,
    RetentionCell,
    RiskCell,
    TrustCell,
    ValueCell,
)
from psychology.domain.matrices.matrices import (
    BehaviorMatrix,
    ConfidenceMatrix,
    EmotionMatrix,
    MotivationMatrix,
    ObjectionMatrix,
    PsychologyMatrices,
    RetentionMatrix,
    RiskMatrix,
    TrustMatrix,
    ValueMatrix,
)
from psychology.domain.persona.buying_persona import BuyingPersona, BuyingPersonaSet
from psychology.domain.persona.jtbd import ForcesOfProgress, JobToBeDone, JTBDSet
from psychology.domain.persona.persona import CustomerPersona, PersonaSet
from psychology.domain.quality.quality import PsychologyQualityMetrics
from psychology.domain.report.report import CustomerPsychologyReport
from psychology.domain.shared.ids import (
    BuyingPersonaId,
    CustomerPersonaId,
    DecisionTriggerId,
    DriverId,
    JobToBeDoneId,
    MatrixCellId,
    PsychEdgeId,
    PsychNodeId,
    PsychologyEvidenceId,
    PsychologyReportId,
    PsychologyReportLineageId,
    TrustRequirementId,
)
from psychology.domain.shared.value_objects import (
    AnxietyKind,
    AwarenessLevel,
    BehavioralPrincipleKind,
    BuyingRole,
    Confidence,
    CustomerIntent,
    DriverKind,
    EmotionKind,
    FrictionKind,
    GraphKind,
    GraphRelation,
    Intensity,
    JobType,
    JourneyPhase,
    Likelihood,
    MaslowNeed,
    NodeKind,
    ObjectionKind,
    Percentage,
    Priority,
    ProvenanceKind,
    RiskKind,
    SophisticationLevel,
    Tag,
    TrustRequirementKind,
)
from psychology.domain.state.confidence import (
    DecisionTrigger,
    PurchaseConfidence,
    TrustRequirement,
)
from psychology.domain.state.drivers import Driver, PurchaseMotivation
from psychology.domain.state.friction import (
    PurchaseAnxiety,
    PurchaseFriction,
    RiskPerception,
)
from psychology.domain.state.profile import PsychologicalProfile

__all__ = ["from_document", "to_document"]


def _ids(items) -> list[str]:
    return [str(i) for i in items]


def _eids(raw) -> tuple[PsychologyEvidenceId, ...]:
    return tuple(PsychologyEvidenceId.from_string(x) for x in raw)


# --------------------------- serialize ---------------------------------- #
def to_document(r: CustomerPsychologyReport) -> dict:
    return {
        "id": str(r.id),
        "lineage_id": str(r.lineage_id),
        "version": r.version,
        "project_id": r.project_id,
        "created_at": r.created_at.isoformat(),
        "quality": {
            "coverage": r.quality.coverage.value, "grounding": r.quality.grounding.value,
            "framework_validation": r.quality.framework_validation.value,
            "confidence": r.quality.confidence.value,
        },
        "evidence": [
            {"id": str(e.id), "provenance": e.provenance.value, "external_ref": e.external_ref,
             "claim": e.claim, "confidence": e.confidence.value, "statement": e.statement,
             "source_name": e.source_name, "tags": [t.value for t in e.tags]}
            for e in r.evidence_graph
        ],
        "profile": _profile_doc(r.profile),
        "personas": [
            {"id": str(p.id), "name": p.name, "archetype": p.archetype, "awareness": p.awareness.value,
             "confidence": p.confidence.value, "demographics": dict(p.demographics),
             "psychographics": dict(p.psychographics), "goals": list(p.goals), "fears": list(p.fears),
             "evidence_ids": _ids(p.evidence_ids)}
            for p in r.personas
        ],
        "buying_personas": [
            {"id": str(p.id), "name": p.name, "role": p.role.value, "awareness": p.awareness.value,
             "sophistication": p.sophistication.value, "must_believe": list(p.must_believe),
             "blocked_by": list(p.blocked_by), "decision_criteria": list(p.decision_criteria),
             "evidence_ids": _ids(p.evidence_ids)}
            for p in r.buying_personas
        ],
        "jobs": [
            {"id": str(j.id), "when_situation": j.when_situation, "motivation": j.motivation,
             "expected_outcome": j.expected_outcome, "job_type": j.job_type.value,
             "forces": {"push": int(j.forces.push), "pull": int(j.forces.pull),
                        "anxiety": int(j.forces.anxiety), "habit": int(j.forces.habit)},
             "evidence_ids": _ids(j.evidence_ids)}
            for j in r.jobs
        ],
        "buying_journey": [
            {"phase": s.phase.value, "customer_goal": s.customer_goal, "dominant_driver": s.dominant_driver.value,
             "emotion": s.emotion.value, "dominant_motivation": s.dominant_motivation,
             "anxieties": list(s.anxieties), "frictions": list(s.frictions), "trust_needed": list(s.trust_needed),
             "evidence_ids": _ids(s.evidence_ids)}
            for s in r.buying_journey
        ],
        "decision_journey": [
            {"order": s.order, "commitment": s.commitment, "emotion": s.emotion.value,
             "peak_end_weight": int(s.peak_end_weight), "micro_decision": s.micro_decision,
             "anxiety": s.anxiety, "evidence_ids": _ids(s.evidence_ids)}
            for s in r.decision_journey
        ],
        "matrices": _matrices_doc(r.matrices),
        "frameworks": _frameworks_doc(r.frameworks),
        "graphs": {g.kind.value: _graph_doc(g) for g in r.graphs.all()},
    }


def _profile_doc(p: PsychologicalProfile) -> dict:
    return {
        "target_customer": p.target_customer, "awareness": p.awareness.value,
        "sophistication": p.sophistication.value, "intent": p.intent.value,
        "confidence": {"level": int(p.confidence.level), "boosters": list(p.confidence.boosters),
                       "blockers": list(p.confidence.blockers), "evidence_ids": _ids(p.confidence.evidence_ids)},
        "motivations": [
            {"description": m.description, "maslow_need": m.maslow_need.value, "intensity": int(m.intensity),
             "evidence_ids": _ids(m.evidence_ids)} for m in p.motivations
        ],
        "anxieties": [
            {"kind": a.kind.value, "description": a.description, "intensity": int(a.intensity),
             "phase": a.phase.value, "evidence_ids": _ids(a.evidence_ids)} for a in p.anxieties
        ],
        "frictions": [
            {"kind": f.kind.value, "description": f.description, "intensity": int(f.intensity),
             "phase": f.phase.value, "evidence_ids": _ids(f.evidence_ids)} for f in p.frictions
        ],
        "risks": [
            {"kind": rk.kind.value, "description": rk.description, "likelihood": int(rk.likelihood),
             "impact": int(rk.impact), "mitigation": rk.mitigation, "evidence_ids": _ids(rk.evidence_ids)}
            for rk in p.risks
        ],
        "trust_requirements": [
            {"id": str(t.id), "kind": t.kind.value, "description": t.description, "phase": t.phase.value,
             "priority": int(t.priority), "evidence_ids": _ids(t.evidence_ids)} for t in p.trust_requirements
        ],
        "decision_triggers": [
            {"id": str(t.id), "description": t.description, "activates": t.activates.value,
             "phase": t.phase.value, "evidence_ids": _ids(t.evidence_ids)} for t in p.decision_triggers
        ],
        "drivers": [
            {"id": str(d.id), "kind": d.kind.value, "description": d.description, "intensity": int(d.intensity),
             "evidence_ids": _ids(d.evidence_ids)} for d in p.drivers
        ],
    }


def _cell_common(c) -> dict:
    return {"id": str(c.id), "evidence_ids": _ids(c.evidence_ids)}


def _matrices_doc(m: PsychologyMatrices) -> dict:
    return {
        "objection": [{**_cell_common(c), "objection": c.objection, "kind": c.kind.value,
                       "phase": c.phase.value, "resolution_strategy": c.resolution_strategy,
                       "confidence": c.confidence.value} for c in m.objection],
        "trust": [{**_cell_common(c), "requirement": c.requirement, "kind": c.kind.value,
                   "signal_needed": c.signal_needed, "phase": c.phase.value, "salience": int(c.salience)}
                  for c in m.trust],
        "motivation": [{**_cell_common(c), "motivation": c.motivation, "maslow_need": c.maslow_need.value,
                        "driver_kind": c.driver_kind.value, "intensity": int(c.intensity)} for c in m.motivation],
        "emotion": [{**_cell_common(c), "emotion": c.emotion.value, "phase": c.phase.value,
                     "trigger": c.trigger, "intended_shift": c.intended_shift.value} for c in m.emotion],
        "behavior": [{**_cell_common(c), "target_behavior": c.target_behavior, "motivation": int(c.motivation),
                      "ability": int(c.ability), "prompt": c.prompt} for c in m.behavior],
        "risk": [{**_cell_common(c), "risk": c.risk, "kind": c.kind.value, "likelihood": int(c.likelihood),
                  "impact": int(c.impact), "mitigation": c.mitigation} for c in m.risk],
        "value": [{**_cell_common(c), "value_perception": c.value_perception,
                   "price_relation": c.price_relation, "framing": c.framing} for c in m.value],
        "confidence": [{**_cell_common(c), "factor": c.factor, "current_level": int(c.current_level),
                        "lever": c.lever} for c in m.confidence],
        "retention": [{**_cell_common(c), "driver": c.driver, "lifecycle_stage": c.lifecycle_stage,
                       "mechanism": c.mechanism} for c in m.retention],
    }


def _frameworks_doc(f: FrameworkLens) -> dict:
    return {
        "maslow": {"dominant_need": f.maslow.dominant_need.value,
                   "active_needs": [n.value for n in f.maslow.active_needs],
                   "rationale": f.maslow.rationale, "evidence_ids": _ids(f.maslow.evidence_ids)},
        "fogg": {"primary_lever": f.fogg.primary_lever.value, "conclusion": f.fogg.conclusion,
                 "ability_barriers": list(f.fogg.ability_barriers), "prompt_strategy": f.fogg.prompt_strategy,
                 "evidence_ids": _ids(f.fogg.evidence_ids)},
        "hook": {"trigger": f.hook.trigger, "action": f.hook.action, "variable_reward": f.hook.variable_reward,
                 "investment": f.hook.investment, "ethical_guardrail": f.hook.ethical_guardrail,
                 "evidence_ids": _ids(f.hook.evidence_ids)},
        "principles": [
            {"kind": p.kind.value, "application": p.application, "ethical_guardrail": p.ethical_guardrail,
             "evidence_ids": _ids(p.evidence_ids)} for p in f.principles
        ],
    }


def _graph_doc(g: PsychGraph) -> dict:
    return {
        "kind": g.kind.value,
        "nodes": [{"id": str(n.id), "kind": n.kind.value, "label": n.label,
                   "evidence_ids": _ids(n.evidence_ids)} for n in g],
        "edges": [{"id": str(e.id), "source": str(e.source), "target": str(e.target),
                   "relation": e.relation.value} for e in g.edges],
    }


# --------------------------- deserialize -------------------------------- #
def from_document(doc: dict) -> CustomerPsychologyReport:
    evidence_graph = EvidenceGraph.of(
        PsychologyEvidence(
            id=PsychologyEvidenceId.from_string(e["id"]), provenance=ProvenanceKind(e["provenance"]),
            external_ref=e["external_ref"], claim=e["claim"], confidence=Confidence.of(e["confidence"]),
            statement=e.get("statement", ""), source_name=e.get("source_name", ""),
            tags=frozenset(Tag.of(t) for t in e.get("tags", ())),
        )
        for e in doc["evidence"]
    )
    quality = PsychologyQualityMetrics(
        coverage=Percentage.of(doc["quality"]["coverage"]),
        grounding=Percentage.of(doc["quality"]["grounding"]),
        framework_validation=Percentage.of(doc["quality"]["framework_validation"]),
        confidence=Confidence.of(doc["quality"]["confidence"]),
    )
    return CustomerPsychologyReport(
        id=PsychologyReportId.from_string(doc["id"]),
        lineage_id=PsychologyReportLineageId.from_string(doc["lineage_id"]),
        version=doc["version"], project_id=doc["project_id"],
        profile=_profile(doc["profile"]),
        personas=_personas(doc["personas"]),
        buying_personas=_buying_personas(doc["buying_personas"]),
        jobs=_jobs(doc["jobs"]),
        buying_journey=_buying_journey(doc["buying_journey"]),
        decision_journey=_decision_journey(doc["decision_journey"]),
        matrices=_matrices(doc["matrices"]),
        frameworks=_frameworks(doc["frameworks"]),
        graphs=_graphs(doc["graphs"]),
        evidence_graph=evidence_graph, quality=quality,
        created_at=datetime.fromisoformat(doc["created_at"]),
    )


def _profile(doc: dict) -> PsychologicalProfile:
    c = doc["confidence"]
    return PsychologicalProfile(
        target_customer=doc["target_customer"], awareness=AwarenessLevel(doc["awareness"]),
        sophistication=SophisticationLevel(doc["sophistication"]), intent=CustomerIntent(doc["intent"]),
        confidence=PurchaseConfidence(level=Intensity(c["level"]), boosters=tuple(c.get("boosters", ())),
                                      blockers=tuple(c.get("blockers", ())), evidence_ids=_eids(c["evidence_ids"])),
        motivations=tuple(
            PurchaseMotivation(description=m["description"], maslow_need=MaslowNeed(m["maslow_need"]),
                               intensity=Intensity(m["intensity"]), evidence_ids=_eids(m["evidence_ids"]))
            for m in doc["motivations"]
        ),
        anxieties=tuple(
            PurchaseAnxiety(kind=AnxietyKind(a["kind"]), description=a["description"],
                            intensity=Intensity(a["intensity"]), phase=JourneyPhase(a["phase"]),
                            evidence_ids=_eids(a["evidence_ids"])) for a in doc["anxieties"]
        ),
        frictions=tuple(
            PurchaseFriction(kind=FrictionKind(f["kind"]), description=f["description"],
                             intensity=Intensity(f["intensity"]), phase=JourneyPhase(f["phase"]),
                             evidence_ids=_eids(f["evidence_ids"])) for f in doc["frictions"]
        ),
        risks=tuple(
            RiskPerception(kind=RiskKind(rk["kind"]), description=rk["description"],
                           likelihood=Likelihood(rk["likelihood"]), impact=Intensity(rk["impact"]),
                           mitigation=rk.get("mitigation", ""), evidence_ids=_eids(rk["evidence_ids"]))
            for rk in doc["risks"]
        ),
        trust_requirements=tuple(
            TrustRequirement(id=TrustRequirementId.from_string(t["id"]), kind=TrustRequirementKind(t["kind"]),
                             description=t["description"], phase=JourneyPhase(t["phase"]),
                             priority=Priority(t["priority"]), evidence_ids=_eids(t["evidence_ids"]))
            for t in doc["trust_requirements"]
        ),
        decision_triggers=tuple(
            DecisionTrigger(id=DecisionTriggerId.from_string(t["id"]), description=t["description"],
                            activates=DriverKind(t["activates"]), phase=JourneyPhase(t["phase"]),
                            evidence_ids=_eids(t["evidence_ids"])) for t in doc["decision_triggers"]
        ),
        drivers=tuple(
            Driver(id=DriverId.from_string(d["id"]), kind=DriverKind(d["kind"]), description=d["description"],
                   intensity=Intensity(d["intensity"]), evidence_ids=_eids(d["evidence_ids"]))
            for d in doc["drivers"]
        ),
    )


def _personas(raw) -> PersonaSet:
    return PersonaSet.of(
        CustomerPersona(id=CustomerPersonaId.from_string(p["id"]), name=p["name"], archetype=p["archetype"],
                        awareness=AwarenessLevel(p["awareness"]), confidence=Confidence.of(p["confidence"]),
                        demographics=dict(p.get("demographics", {})), psychographics=dict(p.get("psychographics", {})),
                        goals=tuple(p.get("goals", ())), fears=tuple(p.get("fears", ())),
                        evidence_ids=_eids(p["evidence_ids"]))
        for p in raw
    )


def _buying_personas(raw) -> BuyingPersonaSet:
    return BuyingPersonaSet.of(
        BuyingPersona(id=BuyingPersonaId.from_string(p["id"]), name=p["name"], role=BuyingRole(p["role"]),
                      awareness=AwarenessLevel(p["awareness"]), sophistication=SophisticationLevel(p["sophistication"]),
                      must_believe=tuple(p.get("must_believe", ())), blocked_by=tuple(p.get("blocked_by", ())),
                      decision_criteria=tuple(p.get("decision_criteria", ())), evidence_ids=_eids(p["evidence_ids"]))
        for p in raw
    )


def _jobs(raw) -> JTBDSet:
    return JTBDSet.of(
        JobToBeDone(id=JobToBeDoneId.from_string(j["id"]), when_situation=j["when_situation"],
                    motivation=j["motivation"], expected_outcome=j["expected_outcome"],
                    job_type=JobType(j["job_type"]),
                    forces=ForcesOfProgress(push=Intensity(j["forces"]["push"]), pull=Intensity(j["forces"]["pull"]),
                                            anxiety=Intensity(j["forces"]["anxiety"]), habit=Intensity(j["forces"]["habit"])),
                    evidence_ids=_eids(j["evidence_ids"]))
        for j in raw
    )


def _buying_journey(raw) -> BuyingJourney:
    return BuyingJourney.of(
        BuyingStage(phase=JourneyPhase(s["phase"]), customer_goal=s["customer_goal"],
                    dominant_driver=DriverKind(s["dominant_driver"]), emotion=EmotionKind(s["emotion"]),
                    dominant_motivation=s.get("dominant_motivation", ""), anxieties=tuple(s.get("anxieties", ())),
                    frictions=tuple(s.get("frictions", ())), trust_needed=tuple(s.get("trust_needed", ())),
                    evidence_ids=_eids(s["evidence_ids"]))
        for s in raw
    )


def _decision_journey(raw) -> DecisionJourney:
    return DecisionJourney.of(
        DecisionStage(order=s["order"], commitment=s["commitment"], emotion=EmotionKind(s["emotion"]),
                      peak_end_weight=Intensity(s["peak_end_weight"]), micro_decision=s.get("micro_decision", ""),
                      anxiety=s.get("anxiety", ""), evidence_ids=_eids(s["evidence_ids"]))
        for s in raw
    )


def _matrices(doc: dict) -> PsychologyMatrices:
    return PsychologyMatrices(
        objection=ObjectionMatrix.of(
            ObjectionCell(id=MatrixCellId.from_string(c["id"]), objection=c["objection"],
                          kind=ObjectionKind(c["kind"]), phase=JourneyPhase(c["phase"]),
                          resolution_strategy=c["resolution_strategy"], confidence=Confidence.of(c["confidence"]),
                          evidence_ids=_eids(c["evidence_ids"])) for c in doc["objection"]),
        trust=TrustMatrix.of(
            TrustCell(id=MatrixCellId.from_string(c["id"]), requirement=c["requirement"],
                      kind=TrustRequirementKind(c["kind"]), signal_needed=c["signal_needed"],
                      phase=JourneyPhase(c["phase"]), salience=Intensity(c["salience"]),
                      evidence_ids=_eids(c["evidence_ids"])) for c in doc["trust"]),
        motivation=MotivationMatrix.of(
            MotivationCell(id=MatrixCellId.from_string(c["id"]), motivation=c["motivation"],
                           maslow_need=MaslowNeed(c["maslow_need"]), driver_kind=DriverKind(c["driver_kind"]),
                           intensity=Intensity(c["intensity"]), evidence_ids=_eids(c["evidence_ids"]))
            for c in doc["motivation"]),
        emotion=EmotionMatrix.of(
            EmotionCell(id=MatrixCellId.from_string(c["id"]), emotion=EmotionKind(c["emotion"]),
                        phase=JourneyPhase(c["phase"]), trigger=c["trigger"],
                        intended_shift=EmotionKind(c["intended_shift"]), evidence_ids=_eids(c["evidence_ids"]))
            for c in doc["emotion"]),
        behavior=BehaviorMatrix.of(
            BehaviorCell(id=MatrixCellId.from_string(c["id"]), target_behavior=c["target_behavior"],
                         motivation=Intensity(c["motivation"]), ability=Intensity(c["ability"]),
                         prompt=c["prompt"], evidence_ids=_eids(c["evidence_ids"])) for c in doc["behavior"]),
        risk=RiskMatrix.of(
            RiskCell(id=MatrixCellId.from_string(c["id"]), risk=c["risk"], kind=RiskKind(c["kind"]),
                     likelihood=Likelihood(c["likelihood"]), impact=Intensity(c["impact"]),
                     mitigation=c.get("mitigation", ""), evidence_ids=_eids(c["evidence_ids"])) for c in doc["risk"]),
        value=ValueMatrix.of(
            ValueCell(id=MatrixCellId.from_string(c["id"]), value_perception=c["value_perception"],
                      price_relation=c["price_relation"], framing=c.get("framing", ""),
                      evidence_ids=_eids(c["evidence_ids"])) for c in doc["value"]),
        confidence=ConfidenceMatrix.of(
            ConfidenceCell(id=MatrixCellId.from_string(c["id"]), factor=c["factor"],
                           current_level=Intensity(c["current_level"]), lever=c["lever"],
                           evidence_ids=_eids(c["evidence_ids"])) for c in doc["confidence"]),
        retention=RetentionMatrix.of(
            RetentionCell(id=MatrixCellId.from_string(c["id"]), driver=c["driver"],
                          lifecycle_stage=c["lifecycle_stage"], mechanism=c["mechanism"],
                          evidence_ids=_eids(c["evidence_ids"])) for c in doc["retention"]),
    )


def _frameworks(doc: dict) -> FrameworkLens:
    m, f, h = doc["maslow"], doc["fogg"], doc["hook"]
    return FrameworkLens(
        maslow=MaslowMapping(dominant_need=MaslowNeed(m["dominant_need"]),
                             active_needs=tuple(MaslowNeed(n) for n in m.get("active_needs", ())),
                             rationale=m.get("rationale", ""), evidence_ids=_eids(m["evidence_ids"])),
        fogg=FoggAnalysis(primary_lever=FoggLever(f["primary_lever"]), conclusion=f["conclusion"],
                          ability_barriers=tuple(f.get("ability_barriers", ())),
                          prompt_strategy=f.get("prompt_strategy", ""), evidence_ids=_eids(f["evidence_ids"])),
        hook=HookLoop(trigger=h["trigger"], action=h["action"], variable_reward=h["variable_reward"],
                      investment=h["investment"], ethical_guardrail=h["ethical_guardrail"],
                      evidence_ids=_eids(h["evidence_ids"])),
        principles=BehavioralPrincipleSet.of(
            BehavioralPrinciple(kind=BehavioralPrincipleKind(p["kind"]), application=p["application"],
                                ethical_guardrail=p["ethical_guardrail"], evidence_ids=_eids(p["evidence_ids"]))
            for p in doc["principles"]
        ),
    )


def _graph(doc: dict) -> PsychGraph:
    nodes = tuple(
        PsychNode(id=PsychNodeId.from_string(n["id"]), kind=NodeKind(n["kind"]), label=n["label"],
                  evidence_ids=_eids(n["evidence_ids"])) for n in doc["nodes"]
    )
    edges = tuple(
        PsychEdge(id=PsychEdgeId.from_string(e["id"]), source=PsychNodeId.from_string(e["source"]),
                  target=PsychNodeId.from_string(e["target"]), relation=GraphRelation(e["relation"]))
        for e in doc["edges"]
    )
    return PsychGraph.of(GraphKind(doc["kind"]), nodes, edges)


def _graphs(doc: dict) -> PsychologyGraphs:
    return PsychologyGraphs(
        decision=_graph(doc["decision"]), emotion=_graph(doc["emotion"]), trust=_graph(doc["trust"]),
        objection=_graph(doc["objection"]), motivation=_graph(doc["motivation"]), behavior=_graph(doc["behavior"]),
    )
