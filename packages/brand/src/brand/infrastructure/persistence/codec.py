"""Codec — serializes a BrandStrategyReport to a JSON document and back.

A report is a deep, immutable aggregate; it is stored and loaded whole as one JSON
document. This codec is the single, exhaustive translation. Reconstruction goes through
the normal aggregate constructor, so a decoded report is re-validated (its provenance
integrity re-checked) — a corrupt document cannot yield an invalid or ungrounded brand.

Pure functions, no I/O.
"""

from __future__ import annotations

from datetime import datetime

from brand.domain.classification.classification import BrandClassification
from brand.domain.decision.decision import BrandDecision
from brand.domain.decision.decision_graph import BrandDecisionEdge, BrandDecisionGraph
from brand.domain.emotional.emotional import (
    BrandDifferentiator,
    EmotionalPositioning,
    TrustSignal,
)
from brand.domain.emotional.emotional_strategy import EmotionalStrategy
from brand.domain.evidence.evidence import BrandEvidence, EvidenceGraph
from brand.domain.governance.consistency import (
    BrandConsistencyRule,
    ConsistencyRuleSet,
)
from brand.domain.governance.governance import BrandGovernanceRule, GovernanceRuleSet
from brand.domain.governance.governance_model import BrandGovernance
from brand.domain.governance.validation import BrandValidationRule, ValidationRuleSet
from brand.domain.identity.identity import BrandIdentity
from brand.domain.identity.positioning import BrandPositioning
from brand.domain.identity.purpose import BrandMission, BrandPromise, BrandVision
from brand.domain.identity.story import BrandStory
from brand.domain.identity.values import BrandValue, BrandValues
from brand.domain.personality.archetype import ArchetypeBlend
from brand.domain.personality.character import BrandCharacter
from brand.domain.personality.personality import BrandAttribute, BrandPersonality
from brand.domain.personality.voice import BrandTone, BrandVoice, ToneModulation
from brand.domain.quality.quality import BrandQualityMetrics
from brand.domain.report.report import BrandStrategyReport
from brand.domain.shared.ids import (
    BrandAttributeId,
    BrandDecisionEdgeId,
    BrandDecisionId,
    BrandDifferentiatorId,
    BrandEvidenceId,
    BrandReportId,
    BrandReportLineageId,
    BrandValueId,
    ConsistencyRuleId,
    GovernanceRuleId,
    TrustSignalId,
    ValidationRuleId,
)
from brand.domain.shared.value_objects import (
    BrandArchetype,
    BrandCategory,
    BrandDecisionType,
    ColorTemperament,
    ComponentWeight,
    Confidence,
    ConsideredAlternative,
    ConsistencyDimension,
    ContrastLevel,
    CornerLanguage,
    DecisionRelation,
    EmotionKind,
    GovernanceScope,
    IconStyle,
    IllustrationStyle,
    MessagingTone,
    MotionCharacter,
    Percentage,
    PhotoTreatment,
    Priority,
    ProvenanceKind,
    RuleEnforcement,
    Salience,
    SpacingDensity,
    Tag,
    TrustSignalKind,
    TypeVoice,
    UITexture,
    ValidationSeverity,
    VoiceDimension,
)
from brand.domain.verbal.copy_guidelines import BrandCopyGuidelines
from brand.domain.verbal.language_rules import BrandLanguageRules
from brand.domain.verbal.verbal_system import BrandVerbalSystem
from brand.domain.visual.color import ColorPhilosophy
from brand.domain.visual.iconography import IconographyDirection
from brand.domain.visual.imagery import IllustrationDirection, PhotographyDirection
from brand.domain.visual.logo import LogoDirection
from brand.domain.visual.motion import MotionPrinciples
from brand.domain.visual.spacing import SpacingPhilosophy
from brand.domain.visual.typography import TypographyDirection
from brand.domain.visual.ui_personality import ComponentPersonality, UIPersonality
from brand.domain.visual.visual_direction import BrandVisualDirection

__all__ = ["from_document", "to_document"]


def _ids(items) -> list[str]:
    return [str(i) for i in items]


def _eids(raw) -> tuple[BrandEvidenceId, ...]:
    return tuple(BrandEvidenceId.from_string(x) for x in raw)


def _alt_doc(a: ConsideredAlternative) -> dict:
    return {"option": a.option, "reason_rejected": a.reason_rejected}


def _alts(raw) -> tuple[ConsideredAlternative, ...]:
    return tuple(
        ConsideredAlternative(option=a["option"], reason_rejected=a["reason_rejected"])
        for a in raw
    )


# --------------------------- serialize ---------------------------------- #
def to_document(r: BrandStrategyReport) -> dict:
    return {
        "id": str(r.id),
        "lineage_id": str(r.lineage_id),
        "version": r.version,
        "project_id": r.project_id,
        "created_at": r.created_at.isoformat(),
        "quality": {
            "coverage": r.quality.coverage.value,
            "grounding": r.quality.grounding.value,
            "coherence": r.quality.coherence.value,
            "confidence": r.quality.confidence.value,
        },
        "evidence": [
            {"id": str(e.id), "provenance": e.provenance.value, "external_ref": e.external_ref,
             "claim": e.claim, "confidence": e.confidence.value, "statement": e.statement,
             "source_name": e.source_name, "tags": [t.value for t in e.tags]}
            for e in r.evidence_graph
        ],
        "classification": {
            "primary": r.classification.primary.value,
            "secondary": [c.value for c in r.classification.secondary],
            "confidence": r.classification.confidence.value,
            "rationale": r.classification.rationale,
            "considered": [_alt_doc(a) for a in r.classification.considered],
            "evidence_ids": _ids(r.classification.evidence_ids),
        },
        "identity": _identity_doc(r.identity),
        "character": _character_doc(r.character),
        "emotional": _emotional_doc(r.emotional),
        "visual": _visual_doc(r.visual),
        "verbal": _verbal_doc(r.verbal),
        "decision_graph": _decision_graph_doc(r.decision_graph),
        "governance": _governance_doc(r.governance),
    }


def _identity_doc(i: BrandIdentity) -> dict:
    p = i.positioning
    return {
        "positioning": {
            "statement": p.statement, "frame_of_reference": p.frame_of_reference,
            "point_of_difference": p.point_of_difference, "reason_to_believe": p.reason_to_believe,
            "confidence": p.confidence.value, "considered": [_alt_doc(a) for a in p.considered],
            "evidence_ids": _ids(p.evidence_ids),
        },
        "mission": {"statement": i.mission.statement, "evidence_ids": _ids(i.mission.evidence_ids)},
        "vision": {"statement": i.vision.statement, "horizon": i.vision.horizon,
                   "evidence_ids": _ids(i.vision.evidence_ids)},
        "promise": {"statement": i.promise.statement, "proof_points": list(i.promise.proof_points),
                    "evidence_ids": _ids(i.promise.evidence_ids)},
        "values": [
            {"id": str(v.id), "name": v.name, "description": v.description, "behavior": v.behavior,
             "priority": int(v.priority), "evidence_ids": _ids(v.evidence_ids)}
            for v in i.values
        ],
        "story": {"headline": i.story.headline, "situation": i.story.situation,
                  "tension": i.story.tension, "resolution": i.story.resolution,
                  "brand_role": i.story.brand_role, "evidence_ids": _ids(i.story.evidence_ids)},
    }


def _character_doc(c: BrandCharacter) -> dict:
    return {
        "archetype": {
            "primary": c.archetype.primary.value, "primary_weight": c.archetype.primary_weight.value,
            "secondary": c.archetype.secondary.value if c.archetype.secondary else None,
            "rationale": c.archetype.rationale, "considered": [_alt_doc(a) for a in c.archetype.considered],
            "evidence_ids": _ids(c.archetype.evidence_ids),
        },
        "personality": {
            "traits": list(c.personality.traits), "summary": c.personality.summary,
            "evidence_ids": _ids(c.personality.evidence_ids),
            "attributes": [
                {"id": str(a.id), "trait": a.trait, "opposite": a.opposite,
                 "salience": int(a.salience), "evidence_ids": _ids(a.evidence_ids)}
                for a in c.personality.attributes
            ],
        },
        "voice": {
            "dimensions": {d.value: p.value for d, p in c.voice.dimensions.items()},
            "principles": list(c.voice.principles), "avoid": list(c.voice.avoid),
            "signature_words": list(c.voice.signature_words), "evidence_ids": _ids(c.voice.evidence_ids),
        },
        "tone": {
            "dominant": c.tone.dominant.value, "evidence_ids": _ids(c.tone.evidence_ids),
            "modulations": [{"context": m.context, "adjustment": m.adjustment} for m in c.tone.modulations],
        },
    }


def _emotional_doc(e: EmotionalStrategy) -> dict:
    return {
        "positioning": {
            "primary_emotion": e.positioning.primary_emotion.value,
            "emotional_benefit": e.positioning.emotional_benefit,
            "feeling_target": e.positioning.feeling_target,
            "supporting_emotions": [x.value for x in e.positioning.supporting_emotions],
            "evidence_ids": _ids(e.positioning.evidence_ids),
        },
        "differentiators": [
            {"id": str(d.id), "claim": d.claim, "defensibility": d.defensibility, "versus": d.versus,
             "salience": int(d.salience), "evidence_ids": _ids(d.evidence_ids)}
            for d in e.differentiators
        ],
        "trust_signals": [
            {"id": str(t.id), "kind": t.kind.value, "rationale": t.rationale,
             "salience": int(t.salience), "confidence": t.confidence.value,
             "evidence_ids": _ids(t.evidence_ids)}
            for t in e.trust_signals
        ],
    }


def _visual_doc(v: BrandVisualDirection) -> dict:
    return {
        "logo": {"intent": v.logo.intent, "style": v.logo.style, "principles": list(v.logo.principles),
                 "avoid": list(v.logo.avoid), "evidence_ids": _ids(v.logo.evidence_ids)},
        "typography": {"display_voice": v.typography.display_voice.value, "body_voice": v.typography.body_voice.value,
                       "hierarchy_intent": v.typography.hierarchy_intent, "rationale": v.typography.rationale,
                       "principles": list(v.typography.principles), "evidence_ids": _ids(v.typography.evidence_ids)},
        "color": {"temperament": v.color.temperament.value, "contrast": v.color.contrast.value,
                  "accent_role": v.color.accent_role, "neutrals_role": v.color.neutrals_role,
                  "meaning": v.color.meaning, "avoid": list(v.color.avoid), "evidence_ids": _ids(v.color.evidence_ids)},
        "spacing": {"density": v.spacing.density.value, "rhythm_intent": v.spacing.rhythm_intent,
                    "whitespace_role": v.spacing.whitespace_role, "principles": list(v.spacing.principles),
                    "evidence_ids": _ids(v.spacing.evidence_ids)},
        "photography": {"treatment": v.photography.treatment.value, "subject_focus": v.photography.subject_focus,
                        "mood": v.photography.mood, "principles": list(v.photography.principles),
                        "evidence_ids": _ids(v.photography.evidence_ids)},
        "illustration": {"style": v.illustration.style.value, "role": v.illustration.role,
                         "principles": list(v.illustration.principles), "evidence_ids": _ids(v.illustration.evidence_ids)},
        "iconography": {"style": v.iconography.style.value, "weight_intent": v.iconography.weight_intent,
                        "principles": list(v.iconography.principles), "evidence_ids": _ids(v.iconography.evidence_ids)},
        "motion": {"character": v.motion.character.value, "purpose": v.motion.purpose,
                   "restraint": v.motion.restraint, "principles": list(v.motion.principles),
                   "evidence_ids": _ids(v.motion.evidence_ids)},
        "ui": {"corner_language": v.ui.corner_language.value, "weight": v.ui.weight.value,
               "density": v.ui.density.value, "texture": v.ui.texture.value, "feel": v.ui.feel,
               "principles": list(v.ui.principles), "evidence_ids": _ids(v.ui.evidence_ids)},
        "component": {"interaction_feel": v.component.interaction_feel, "emphasis": v.component.emphasis,
                      "restraint": v.component.restraint, "principles": list(v.component.principles),
                      "evidence_ids": _ids(v.component.evidence_ids)},
    }


def _verbal_doc(v: BrandVerbalSystem) -> dict:
    lr = v.language_rules
    cg = v.copy_guidelines
    return {
        "language_rules": {"person": lr.person, "capitalization": lr.capitalization,
                           "terminology": dict(lr.terminology), "preferred_words": list(lr.preferred_words),
                           "forbidden_words": list(lr.forbidden_words), "principles": list(lr.principles),
                           "evidence_ids": _ids(lr.evidence_ids)},
        "copy_guidelines": {"headline_principles": list(cg.headline_principles), "cta_style": cg.cta_style,
                            "microcopy_stance": cg.microcopy_stance, "reading_level": cg.reading_level,
                            "do": list(cg.do), "dont": list(cg.dont), "evidence_ids": _ids(cg.evidence_ids)},
    }


def _decision_graph_doc(g: BrandDecisionGraph) -> dict:
    return {
        "decisions": [
            {"id": str(d.id), "type": d.type.value, "title": d.title, "statement": d.statement,
             "confidence": d.confidence.value, "priority": int(d.priority), "rationale": d.rationale,
             "considered": [_alt_doc(a) for a in d.considered], "evidence_ids": _ids(d.evidence_ids)}
            for d in g
        ],
        "edges": [
            {"id": str(e.id), "source": str(e.source), "target": str(e.target),
             "relation": e.relation.value, "evidence_ids": _ids(e.evidence_ids)}
            for e in g.edges
        ],
    }


def _governance_doc(gov: BrandGovernance) -> dict:
    return {
        "consistency": [
            {"id": str(r.id), "dimension": r.dimension.value, "rule": r.rule,
             "enforcement": r.enforcement.value, "evidence_ids": _ids(r.evidence_ids)}
            for r in gov.consistency
        ],
        "governance": [
            {"id": str(r.id), "scope": r.scope.value, "rule": r.rule, "owner": r.owner,
             "enforcement": r.enforcement.value, "evidence_ids": _ids(r.evidence_ids)}
            for r in gov.governance
        ],
        "validation": [
            {"id": str(r.id), "subject": r.subject, "assertion": r.assertion,
             "enforcement": r.enforcement.value, "severity": r.severity.value,
             "checkable_hint": r.checkable_hint, "evidence_ids": _ids(r.evidence_ids)}
            for r in gov.validation
        ],
    }


# --------------------------- deserialize -------------------------------- #
def from_document(doc: dict) -> BrandStrategyReport:
    evidence_graph = EvidenceGraph.of(
        BrandEvidence(
            id=BrandEvidenceId.from_string(e["id"]), provenance=ProvenanceKind(e["provenance"]),
            external_ref=e["external_ref"], claim=e["claim"], confidence=Confidence.of(e["confidence"]),
            statement=e.get("statement", ""), source_name=e.get("source_name", ""),
            tags=frozenset(Tag.of(t) for t in e.get("tags", ())),
        )
        for e in doc["evidence"]
    )
    cl = doc["classification"]
    classification = BrandClassification(
        primary=BrandCategory(cl["primary"]),
        secondary=tuple(BrandCategory(c) for c in cl.get("secondary", ())),
        confidence=Confidence.of(cl["confidence"]), rationale=cl.get("rationale", ""),
        considered=_alts(cl.get("considered", ())), evidence_ids=_eids(cl["evidence_ids"]),
    )
    quality = BrandQualityMetrics(
        coverage=Percentage.of(doc["quality"]["coverage"]),
        grounding=Percentage.of(doc["quality"]["grounding"]),
        coherence=Percentage.of(doc["quality"]["coherence"]),
        confidence=Confidence.of(doc["quality"]["confidence"]),
    )
    return BrandStrategyReport(
        id=BrandReportId.from_string(doc["id"]),
        lineage_id=BrandReportLineageId.from_string(doc["lineage_id"]),
        version=doc["version"], project_id=doc["project_id"],
        classification=classification,
        identity=_identity(doc["identity"]),
        character=_character(doc["character"]),
        emotional=_emotional(doc["emotional"]),
        visual=_visual(doc["visual"]),
        verbal=_verbal(doc["verbal"]),
        decision_graph=_decision_graph(doc["decision_graph"]),
        governance=_governance(doc["governance"]),
        evidence_graph=evidence_graph, quality=quality,
        created_at=datetime.fromisoformat(doc["created_at"]),
    )


def _identity(doc: dict) -> BrandIdentity:
    p = doc["positioning"]
    return BrandIdentity(
        positioning=BrandPositioning(
            statement=p["statement"], frame_of_reference=p["frame_of_reference"],
            point_of_difference=p["point_of_difference"], reason_to_believe=p.get("reason_to_believe", ""),
            confidence=Confidence.of(p["confidence"]), considered=_alts(p.get("considered", ())),
            evidence_ids=_eids(p["evidence_ids"]),
        ),
        mission=BrandMission(statement=doc["mission"]["statement"], evidence_ids=_eids(doc["mission"]["evidence_ids"])),
        vision=BrandVision(statement=doc["vision"]["statement"], horizon=doc["vision"].get("horizon", ""),
                           evidence_ids=_eids(doc["vision"]["evidence_ids"])),
        promise=BrandPromise(statement=doc["promise"]["statement"], proof_points=tuple(doc["promise"].get("proof_points", ())),
                             evidence_ids=_eids(doc["promise"]["evidence_ids"])),
        values=BrandValues.of(
            BrandValue(id=BrandValueId.from_string(v["id"]), name=v["name"], description=v["description"],
                       behavior=v.get("behavior", ""), priority=Priority(v["priority"]),
                       evidence_ids=_eids(v["evidence_ids"]))
            for v in doc["values"]
        ),
        story=BrandStory(headline=doc["story"]["headline"], situation=doc["story"]["situation"],
                         tension=doc["story"]["tension"], resolution=doc["story"]["resolution"],
                         brand_role=doc["story"].get("brand_role", ""), evidence_ids=_eids(doc["story"]["evidence_ids"])),
    )


def _character(doc: dict) -> BrandCharacter:
    a = doc["archetype"]
    return BrandCharacter(
        archetype=ArchetypeBlend(
            primary=BrandArchetype(a["primary"]), primary_weight=Percentage.of(a["primary_weight"]),
            secondary=BrandArchetype(a["secondary"]) if a.get("secondary") else None,
            rationale=a.get("rationale", ""), considered=_alts(a.get("considered", ())),
            evidence_ids=_eids(a["evidence_ids"]),
        ),
        personality=BrandPersonality(
            traits=tuple(doc["personality"].get("traits", ())), summary=doc["personality"].get("summary", ""),
            evidence_ids=_eids(doc["personality"]["evidence_ids"]),
            attributes=tuple(
                BrandAttribute(id=BrandAttributeId.from_string(x["id"]), trait=x["trait"],
                               opposite=x.get("opposite", ""), salience=Salience(x["salience"]),
                               evidence_ids=_eids(x["evidence_ids"]))
                for x in doc["personality"]["attributes"]
            ),
        ),
        voice=BrandVoice(
            dimensions={VoiceDimension(k): Percentage.of(v) for k, v in doc["voice"]["dimensions"].items()},
            principles=tuple(doc["voice"].get("principles", ())), avoid=tuple(doc["voice"].get("avoid", ())),
            signature_words=tuple(doc["voice"].get("signature_words", ())),
            evidence_ids=_eids(doc["voice"]["evidence_ids"]),
        ),
        tone=BrandTone(
            dominant=MessagingTone(doc["tone"]["dominant"]), evidence_ids=_eids(doc["tone"]["evidence_ids"]),
            modulations=tuple(
                ToneModulation(context=m["context"], adjustment=m["adjustment"])
                for m in doc["tone"]["modulations"]
            ),
        ),
    )


def _emotional(doc: dict) -> EmotionalStrategy:
    p = doc["positioning"]
    return EmotionalStrategy(
        positioning=EmotionalPositioning(
            primary_emotion=EmotionKind(p["primary_emotion"]), emotional_benefit=p["emotional_benefit"],
            feeling_target=p.get("feeling_target", ""),
            supporting_emotions=tuple(EmotionKind(x) for x in p.get("supporting_emotions", ())),
            evidence_ids=_eids(p["evidence_ids"]),
        ),
        differentiators=tuple(
            BrandDifferentiator(id=BrandDifferentiatorId.from_string(d["id"]), claim=d["claim"],
                                defensibility=d.get("defensibility", ""), versus=d.get("versus", ""),
                                salience=Salience(d["salience"]), evidence_ids=_eids(d["evidence_ids"]))
            for d in doc["differentiators"]
        ),
        trust_signals=tuple(
            TrustSignal(id=TrustSignalId.from_string(t["id"]), kind=TrustSignalKind(t["kind"]),
                        rationale=t["rationale"], salience=Salience(t["salience"]),
                        confidence=Confidence.of(t["confidence"]), evidence_ids=_eids(t["evidence_ids"]))
            for t in doc["trust_signals"]
        ),
    )


def _visual(doc: dict) -> BrandVisualDirection:
    return BrandVisualDirection(
        logo=LogoDirection(intent=doc["logo"]["intent"], style=doc["logo"].get("style", ""),
                           principles=tuple(doc["logo"].get("principles", ())), avoid=tuple(doc["logo"].get("avoid", ())),
                           evidence_ids=_eids(doc["logo"]["evidence_ids"])),
        typography=TypographyDirection(display_voice=TypeVoice(doc["typography"]["display_voice"]),
                                       body_voice=TypeVoice(doc["typography"]["body_voice"]),
                                       hierarchy_intent=doc["typography"].get("hierarchy_intent", ""),
                                       rationale=doc["typography"].get("rationale", ""),
                                       principles=tuple(doc["typography"].get("principles", ())),
                                       evidence_ids=_eids(doc["typography"]["evidence_ids"])),
        color=ColorPhilosophy(temperament=ColorTemperament(doc["color"]["temperament"]),
                              contrast=ContrastLevel(doc["color"]["contrast"]),
                              accent_role=doc["color"].get("accent_role", ""), neutrals_role=doc["color"].get("neutrals_role", ""),
                              meaning=doc["color"].get("meaning", ""), avoid=tuple(doc["color"].get("avoid", ())),
                              evidence_ids=_eids(doc["color"]["evidence_ids"])),
        spacing=SpacingPhilosophy(density=SpacingDensity(doc["spacing"]["density"]),
                                  rhythm_intent=doc["spacing"].get("rhythm_intent", ""),
                                  whitespace_role=doc["spacing"].get("whitespace_role", ""),
                                  principles=tuple(doc["spacing"].get("principles", ())),
                                  evidence_ids=_eids(doc["spacing"]["evidence_ids"])),
        photography=PhotographyDirection(treatment=PhotoTreatment(doc["photography"]["treatment"]),
                                         subject_focus=doc["photography"].get("subject_focus", ""),
                                         mood=doc["photography"].get("mood", ""),
                                         principles=tuple(doc["photography"].get("principles", ())),
                                         evidence_ids=_eids(doc["photography"]["evidence_ids"])),
        illustration=IllustrationDirection(style=IllustrationStyle(doc["illustration"]["style"]),
                                           role=doc["illustration"].get("role", ""),
                                           principles=tuple(doc["illustration"].get("principles", ())),
                                           evidence_ids=_eids(doc["illustration"]["evidence_ids"])),
        iconography=IconographyDirection(style=IconStyle(doc["iconography"]["style"]),
                                         weight_intent=doc["iconography"].get("weight_intent", ""),
                                         principles=tuple(doc["iconography"].get("principles", ())),
                                         evidence_ids=_eids(doc["iconography"]["evidence_ids"])),
        motion=MotionPrinciples(character=MotionCharacter(doc["motion"]["character"]),
                                purpose=doc["motion"].get("purpose", ""), restraint=doc["motion"].get("restraint", ""),
                                principles=tuple(doc["motion"].get("principles", ())),
                                evidence_ids=_eids(doc["motion"]["evidence_ids"])),
        ui=UIPersonality(corner_language=CornerLanguage(doc["ui"]["corner_language"]),
                         weight=ComponentWeight(doc["ui"]["weight"]), density=SpacingDensity(doc["ui"]["density"]),
                         texture=UITexture(doc["ui"]["texture"]), feel=doc["ui"].get("feel", ""),
                         principles=tuple(doc["ui"].get("principles", ())), evidence_ids=_eids(doc["ui"]["evidence_ids"])),
        component=ComponentPersonality(interaction_feel=doc["component"].get("interaction_feel", ""),
                                       emphasis=doc["component"].get("emphasis", ""),
                                       restraint=doc["component"].get("restraint", ""),
                                       principles=tuple(doc["component"].get("principles", ())),
                                       evidence_ids=_eids(doc["component"]["evidence_ids"])),
    )


def _verbal(doc: dict) -> BrandVerbalSystem:
    lr = doc["language_rules"]
    cg = doc["copy_guidelines"]
    return BrandVerbalSystem(
        language_rules=BrandLanguageRules(
            person=lr.get("person", ""), capitalization=lr.get("capitalization", ""),
            terminology=dict(lr.get("terminology", {})), preferred_words=tuple(lr.get("preferred_words", ())),
            forbidden_words=tuple(lr.get("forbidden_words", ())), principles=tuple(lr.get("principles", ())),
            evidence_ids=_eids(lr["evidence_ids"]),
        ),
        copy_guidelines=BrandCopyGuidelines(
            headline_principles=tuple(cg.get("headline_principles", ())), cta_style=cg.get("cta_style", ""),
            microcopy_stance=cg.get("microcopy_stance", ""), reading_level=cg.get("reading_level", ""),
            do=tuple(cg.get("do", ())), dont=tuple(cg.get("dont", ())), evidence_ids=_eids(cg["evidence_ids"]),
        ),
    )


def _decision_graph(doc: dict) -> BrandDecisionGraph:
    decisions = tuple(
        BrandDecision(id=BrandDecisionId.from_string(d["id"]), type=BrandDecisionType(d["type"]),
                      title=d["title"], statement=d["statement"], confidence=Confidence.of(d["confidence"]),
                      priority=Priority(d["priority"]), rationale=d.get("rationale", ""),
                      considered=_alts(d.get("considered", ())), evidence_ids=_eids(d["evidence_ids"]))
        for d in doc["decisions"]
    )
    edges = tuple(
        BrandDecisionEdge(id=BrandDecisionEdgeId.from_string(e["id"]),
                          source=BrandDecisionId.from_string(e["source"]),
                          target=BrandDecisionId.from_string(e["target"]),
                          relation=DecisionRelation(e["relation"]), evidence_ids=_eids(e["evidence_ids"]))
        for e in doc["edges"]
    )
    return BrandDecisionGraph.of(decisions, edges)


def _governance(doc: dict) -> BrandGovernance:
    return BrandGovernance(
        consistency=ConsistencyRuleSet.of(
            BrandConsistencyRule(id=ConsistencyRuleId.from_string(r["id"]),
                                 dimension=ConsistencyDimension(r["dimension"]), rule=r["rule"],
                                 enforcement=RuleEnforcement(r["enforcement"]), evidence_ids=_eids(r["evidence_ids"]))
            for r in doc["consistency"]
        ),
        governance=GovernanceRuleSet.of(
            BrandGovernanceRule(id=GovernanceRuleId.from_string(r["id"]), scope=GovernanceScope(r["scope"]),
                                rule=r["rule"], owner=r.get("owner", ""),
                                enforcement=RuleEnforcement(r["enforcement"]), evidence_ids=_eids(r["evidence_ids"]))
            for r in doc["governance"]
        ),
        validation=ValidationRuleSet.of(
            BrandValidationRule(id=ValidationRuleId.from_string(r["id"]), subject=r["subject"],
                                assertion=r["assertion"], enforcement=RuleEnforcement(r["enforcement"]),
                                severity=ValidationSeverity(r["severity"]), checkable_hint=r.get("checkable_hint", ""),
                                evidence_ids=_eids(r["evidence_ids"]))
            for r in doc["validation"]
        ),
    )
