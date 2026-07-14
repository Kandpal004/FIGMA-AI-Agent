"""Domain tests — the invariants that make a brand trustworthy by construction."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from brand.domain.classification.classification import BrandClassification
from brand.domain.decision.decision import BrandDecision
from brand.domain.decision.decision_graph import (
    BrandDecisionEdge,
    BrandDecisionGraph,
    InvalidDecisionGraphError,
)
from brand.domain.evidence.evidence import (
    BrandEvidence,
    EvidenceGraph,
    InvalidEvidenceError,
)
from brand.domain.personality.archetype import ArchetypeBlend, InvalidArchetypeError
from brand.domain.shared.ids import (
    BrandDecisionEdgeId,
    BrandDecisionId,
    BrandEvidenceId,
)
from brand.domain.shared.value_objects import (
    BrandArchetype,
    BrandCategory,
    BrandDecisionType,
    Confidence,
    DecisionRelation,
    Percentage,
    Priority,
    ProvenanceKind,
)

NOW = datetime(2026, 7, 14, tzinfo=UTC)


# --------------------------- value objects ------------------------------ #
def test_brand_category_has_thirteen_members():
    assert len(BrandCategory) == 13


def test_brand_archetype_has_twelve_members():
    assert len(BrandArchetype) == 12


def test_archetype_blend_rejects_dominant_below_half():
    with pytest.raises(InvalidArchetypeError):
        ArchetypeBlend(primary=BrandArchetype.SAGE, primary_weight=Percentage(0.4))


def test_archetype_blend_rejects_secondary_equal_primary():
    with pytest.raises(InvalidArchetypeError):
        ArchetypeBlend(primary=BrandArchetype.SAGE, secondary=BrandArchetype.SAGE)


def test_classification_dedupes_secondary_and_drops_primary():
    c = BrandClassification(
        primary=BrandCategory.BEAUTY,
        secondary=(BrandCategory.PREMIUM, BrandCategory.BEAUTY, BrandCategory.PREMIUM),
    )
    assert c.secondary == (BrandCategory.PREMIUM,)
    assert c.expresses(BrandCategory.PREMIUM)
    assert c.expresses(BrandCategory.BEAUTY)


# --------------------------- evidence graph ----------------------------- #
def _evidence(claim: str = "A cited fact") -> BrandEvidence:
    return BrandEvidence(
        id=BrandEvidenceId.new(), provenance=ProvenanceKind.BUSINESS_STRATEGY,
        external_ref="s1", claim=claim, confidence=Confidence.of(0.8),
    )


def test_evidence_requires_claim_and_external_ref():
    with pytest.raises(InvalidEvidenceError):
        BrandEvidence(
            id=BrandEvidenceId.new(), provenance=ProvenanceKind.KNOWLEDGE,
            external_ref="", claim="x", confidence=Confidence.of(0.5),
        )


def test_evidence_graph_rejects_duplicate_ids():
    e = _evidence()
    with pytest.raises(InvalidEvidenceError):
        EvidenceGraph.of([e, e])


# --------------------------- decision graph ----------------------------- #
def _decision(evidence_ids=(), decision_type=BrandDecisionType.POSITIONING) -> BrandDecision:
    return BrandDecision(
        id=BrandDecisionId.new(), type=decision_type, title="Own the position",
        statement="Commit to the brand position.", confidence=Confidence.of(0.8),
        priority=Priority(5), evidence_ids=tuple(evidence_ids),
    )


def test_decision_graph_rejects_dangling_edge():
    a = _decision()
    edge = BrandDecisionEdge(
        id=BrandDecisionEdgeId.new(), source=a.id, target=BrandDecisionId.new(),
        relation=DecisionRelation.EXPRESSES,
    )
    with pytest.raises(InvalidDecisionGraphError):
        BrandDecisionGraph.of([a], [edge])


def test_decision_graph_rejects_derives_from_cycle():
    a, b = _decision(), _decision()
    edges = [
        BrandDecisionEdge(id=BrandDecisionEdgeId.new(), source=a.id, target=b.id, relation=DecisionRelation.DERIVES_FROM),
        BrandDecisionEdge(id=BrandDecisionEdgeId.new(), source=b.id, target=a.id, relation=DecisionRelation.DERIVES_FROM),
    ]
    with pytest.raises(InvalidDecisionGraphError):
        BrandDecisionGraph.of([a, b], edges)


def test_decision_graph_expresses_query():
    creative = _decision(decision_type=BrandDecisionType.COLOR)
    identity = _decision(decision_type=BrandDecisionType.PERSONALITY)
    edge = BrandDecisionEdge(
        id=BrandDecisionEdgeId.new(), source=creative.id, target=identity.id,
        relation=DecisionRelation.EXPRESSES,
    )
    graph = BrandDecisionGraph.of([creative, identity], [edge])
    assert graph.expressed_by(creative.id) == (identity,)


# --------------------------- report provenance -------------------------- #
def _report(*, decisions, evidence):
    from brand.domain.emotional.emotional import EmotionalPositioning
    from brand.domain.emotional.emotional_strategy import EmotionalStrategy
    from brand.domain.governance.governance_model import BrandGovernance
    from brand.domain.identity.identity import BrandIdentity
    from brand.domain.identity.positioning import BrandPositioning
    from brand.domain.identity.purpose import BrandMission, BrandPromise, BrandVision
    from brand.domain.identity.story import BrandStory
    from brand.domain.identity.values import BrandValues
    from brand.domain.personality.character import BrandCharacter
    from brand.domain.personality.personality import BrandPersonality
    from brand.domain.personality.voice import BrandTone, BrandVoice
    from brand.domain.quality.quality import BrandQualityMetrics
    from brand.domain.report.report import BrandStrategyReport
    from brand.domain.shared.ids import BrandReportId, BrandReportLineageId
    from brand.domain.shared.value_objects import EmotionKind, MessagingTone
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
    from brand.domain.shared.value_objects import (
        ColorTemperament, ComponentWeight, ContrastLevel, CornerLanguage, IconStyle,
        IllustrationStyle, MotionCharacter, PhotoTreatment, SpacingDensity, TypeVoice, UITexture,
    )

    ev = tuple(e.id for e in evidence)
    identity = BrandIdentity(
        positioning=BrandPositioning(statement="Trusted premium", frame_of_reference="beauty",
                                     point_of_difference="proof-led trust", evidence_ids=ev),
        mission=BrandMission(statement="Buy with confidence"),
        vision=BrandVision(statement="The trusted choice"),
        promise=BrandPromise(statement="Earn trust every time"),
        values=BrandValues(), story=BrandStory(headline="Why", situation="s", tension="t", resolution="r"),
    )
    character = BrandCharacter(
        archetype=ArchetypeBlend(primary=BrandArchetype.LOVER, evidence_ids=ev),
        personality=BrandPersonality(traits=("elegant",)),
        voice=BrandVoice(), tone=BrandTone(dominant=MessagingTone.ELEGANT),
    )
    emotional = EmotionalStrategy(
        positioning=EmotionalPositioning(primary_emotion=EmotionKind.ASPIRATION, emotional_benefit="feel radiant")
    )
    visual = BrandVisualDirection(
        logo=LogoDirection(intent="refined mark"),
        typography=TypographyDirection(display_voice=TypeVoice.EDITORIAL_SERIF, body_voice=TypeVoice.HUMANIST_SANS),
        color=ColorPhilosophy(temperament=ColorTemperament.WARM, contrast=ContrastLevel.MEDIUM),
        spacing=SpacingPhilosophy(density=SpacingDensity.AIRY),
        photography=PhotographyDirection(treatment=PhotoTreatment.EDITORIAL),
        illustration=IllustrationDirection(style=IllustrationStyle.NONE),
        iconography=IconographyDirection(style=IconStyle.LINE),
        motion=MotionPrinciples(character=MotionCharacter.FLUID),
        ui=UIPersonality(corner_language=CornerLanguage.ROUNDED, weight=ComponentWeight.LIGHT,
                         density=SpacingDensity.AIRY, texture=UITexture.SUBTLE_DEPTH),
        component=ComponentPersonality(interaction_feel="crisp"),
    )
    verbal = BrandVerbalSystem(
        language_rules=BrandLanguageRules(person="you"), copy_guidelines=BrandCopyGuidelines(cta_style="clear"),
    )
    return BrandStrategyReport(
        id=BrandReportId.new(), lineage_id=BrandReportLineageId.new(), version=1, project_id="proj",
        classification=BrandClassification(primary=BrandCategory.BEAUTY, evidence_ids=ev),
        identity=identity, character=character, emotional=emotional, visual=visual, verbal=verbal,
        decision_graph=BrandDecisionGraph.of(decisions),
        governance=BrandGovernance(),
        evidence_graph=EvidenceGraph.of(evidence),
        quality=BrandQualityMetrics(coverage=Percentage.of(1.0), grounding=Percentage.of(1.0),
                                    coherence=Percentage.of(1.0), confidence=Confidence.of(0.8)),
        created_at=NOW,
    )


def test_report_accepts_fully_grounded_brand():
    e = _evidence()
    report = _report(decisions=[_decision(evidence_ids=[e.id])], evidence=[e])
    assert report.is_usable
    assert report.primary_category is BrandCategory.BEAUTY
    assert report.archetype is BrandArchetype.LOVER


def test_report_rejects_ungrounded_decision():
    from brand.domain.report.report import InvalidBrandReportError

    e = _evidence()
    rogue = _decision(evidence_ids=[BrandEvidenceId.new()])  # cites missing evidence
    with pytest.raises(InvalidBrandReportError):
        _report(decisions=[rogue], evidence=[e])


def test_report_bundle_projection_is_neutral():
    from brand.domain.report.bundle import BrandGuidelinesBundle

    e = _evidence()
    report = _report(decisions=[_decision(evidence_ids=[e.id])], evidence=[e])
    bundle = BrandGuidelinesBundle.from_report(report)
    assert bundle.primary_category is BrandCategory.BEAUTY
    assert bundle.archetype is BrandArchetype.LOVER
    assert bundle.report_id == report.id
