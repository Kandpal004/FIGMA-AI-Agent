"""Serializable view DTOs — the read models the inbound layer returns.

Callers receive these flat, primitive-typed projections of a
:class:`BrandStrategyReport` (or a :class:`BrandGuidelinesBundle`) — never the domain
aggregate. Pure data with ``from_*`` builders; no I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from brand.domain.decision.decision import BrandDecision
from brand.domain.report.bundle import BrandGuidelinesBundle
from brand.domain.report.report import BrandStrategyReport
from brand.domain.visual.visual_direction import BrandVisualDirection

__all__ = [
    "BrandDecisionTraceView",
    "BrandDecisionView",
    "GovernanceRuleView",
    "GuidelinesBundleView",
    "IdentityView",
    "PersonalityView",
    "QualityView",
    "ReportView",
    "ValidationRuleView",
    "VisualDirectionView",
]


def _ids(items) -> list[str]:
    return [str(i) for i in items]


def _iso(value) -> str:
    return value.isoformat() if isinstance(value, datetime) else str(value)


def _visual_view(v: BrandVisualDirection) -> dict:
    return {
        "logo": {"intent": v.logo.intent, "style": v.logo.style},
        "typography": {"display_voice": v.typography.display_voice.value,
                       "body_voice": v.typography.body_voice.value,
                       "hierarchy_intent": v.typography.hierarchy_intent},
        "color": {"temperament": v.color.temperament.value, "contrast": v.color.contrast.value,
                  "accent_role": v.color.accent_role, "meaning": v.color.meaning},
        "spacing": {"density": v.spacing.density.value, "rhythm_intent": v.spacing.rhythm_intent},
        "photography": {"treatment": v.photography.treatment.value, "mood": v.photography.mood},
        "illustration": {"style": v.illustration.style.value, "role": v.illustration.role},
        "iconography": {"style": v.iconography.style.value},
        "motion": {"character": v.motion.character.value, "purpose": v.motion.purpose},
        "ui": {"corner_language": v.ui.corner_language.value, "weight": v.ui.weight.value,
               "density": v.ui.density.value, "texture": v.ui.texture.value, "feel": v.ui.feel},
        "component": {"interaction_feel": v.component.interaction_feel, "emphasis": v.component.emphasis},
    }


@dataclass(frozen=True, slots=True)
class QualityView:
    overall_score: float
    band: str
    coverage: float
    grounding: float
    coherence: float
    confidence: float
    is_fully_grounded: bool


@dataclass(frozen=True, slots=True)
class IdentityView:
    positioning: str
    frame_of_reference: str
    point_of_difference: str
    mission: str
    vision: str
    promise: str
    values: list[str]
    story_headline: str


@dataclass(frozen=True, slots=True)
class PersonalityView:
    archetype: str
    archetype_secondary: str | None
    traits: list[str]
    attributes: list[str]
    tone: str
    voice_dimensions: dict[str, float]


@dataclass(frozen=True, slots=True)
class VisualDirectionView:
    direction: dict


@dataclass(frozen=True, slots=True)
class BrandDecisionView:
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
    def from_decision(cls, d: BrandDecision) -> BrandDecisionView:
        return cls(
            id=str(d.id), type=d.type.value, title=d.title, statement=d.statement,
            rationale=d.rationale, confidence=d.confidence.value, priority=int(d.priority),
            considered=[{"option": a.option, "reason_rejected": a.reason_rejected} for a in d.considered],
            evidence_ids=_ids(d.evidence_ids),
        )


@dataclass(frozen=True, slots=True)
class GovernanceRuleView:
    id: str
    kind: str
    scope_or_dimension: str
    rule: str
    enforcement: str
    evidence_ids: list[str]


@dataclass(frozen=True, slots=True)
class ValidationRuleView:
    id: str
    subject: str
    assertion: str
    enforcement: str
    severity: str
    checkable_hint: str
    evidence_ids: list[str]


@dataclass(frozen=True, slots=True)
class ReportView:
    """The full, flat projection of a brand strategy report."""

    report_id: str
    lineage_id: str
    version: int
    project_id: str
    primary_category: str
    secondary_categories: list[str]
    archetype: str
    is_usable: bool
    created_at: str
    quality: QualityView
    identity: IdentityView
    personality: PersonalityView
    emotional_primary: str
    differentiators: list[str]
    trust_signals: list[str]
    visual: VisualDirectionView
    verbal_forbidden_words: list[str]
    decisions: list[BrandDecisionView]
    consistency_rules: list[GovernanceRuleView]
    governance_rules: list[GovernanceRuleView]
    validation_rules: list[ValidationRuleView]
    evidence_count: int

    @classmethod
    def from_report(cls, r: BrandStrategyReport) -> ReportView:
        quality = QualityView(
            overall_score=r.quality.overall_score.value, band=r.quality.band.value,
            coverage=r.quality.coverage.value, grounding=r.quality.grounding.value,
            coherence=r.quality.coherence.value, confidence=r.quality.confidence.value,
            is_fully_grounded=r.quality.is_fully_grounded,
        )
        identity = IdentityView(
            positioning=r.identity.positioning.statement,
            frame_of_reference=r.identity.positioning.frame_of_reference,
            point_of_difference=r.identity.positioning.point_of_difference,
            mission=r.identity.mission.statement, vision=r.identity.vision.statement,
            promise=r.identity.promise.statement,
            values=[v.name for v in r.identity.values.by_priority()],
            story_headline=r.identity.story.headline,
        )
        personality = PersonalityView(
            archetype=r.character.archetype.primary.value,
            archetype_secondary=r.character.archetype.secondary.value if r.character.archetype.secondary else None,
            traits=list(r.character.personality.traits),
            attributes=[a.trait for a in r.character.personality.attributes],
            tone=r.character.tone.dominant.value,
            voice_dimensions={d.value: p.value for d, p in r.character.voice.dimensions.items()},
        )
        return cls(
            report_id=str(r.id), lineage_id=str(r.lineage_id), version=r.version,
            project_id=r.project_id, primary_category=r.primary_category.value,
            secondary_categories=[c.value for c in r.classification.secondary],
            archetype=r.archetype.value, is_usable=r.is_usable, created_at=_iso(r.created_at),
            quality=quality, identity=identity, personality=personality,
            emotional_primary=r.emotional.positioning.primary_emotion.value,
            differentiators=[d.claim for d in r.emotional.differentiators_by_salience()],
            trust_signals=[t.kind.value for t in r.emotional.trust_by_salience()],
            visual=VisualDirectionView(direction=_visual_view(r.visual)),
            verbal_forbidden_words=list(r.verbal.language_rules.forbidden_words),
            decisions=[BrandDecisionView.from_decision(d) for d in r.decision_graph],
            consistency_rules=[
                GovernanceRuleView(id=str(x.id), kind="consistency", scope_or_dimension=x.dimension.value,
                                   rule=x.rule, enforcement=x.enforcement.value, evidence_ids=_ids(x.evidence_ids))
                for x in r.governance.consistency
            ],
            governance_rules=[
                GovernanceRuleView(id=str(x.id), kind="governance", scope_or_dimension=x.scope.value,
                                   rule=x.rule, enforcement=x.enforcement.value, evidence_ids=_ids(x.evidence_ids))
                for x in r.governance.governance
            ],
            validation_rules=[
                ValidationRuleView(id=str(x.id), subject=x.subject, assertion=x.assertion,
                                   enforcement=x.enforcement.value, severity=x.severity.value,
                                   checkable_hint=x.checkable_hint, evidence_ids=_ids(x.evidence_ids))
                for x in r.governance.validation
            ],
            evidence_count=r.evidence_count(),
        )


@dataclass(frozen=True, slots=True)
class GuidelinesBundleView:
    """The neutral brand brief downstream design phases consume, flattened for transport."""

    report_id: str
    project_id: str
    primary_category: str
    secondary_categories: list[str]
    archetype: str
    tone: str
    positioning_statement: str
    visual: VisualDirectionView
    validation_rules: list[ValidationRuleView]
    is_usable: bool
    created_at: str

    @classmethod
    def from_bundle(cls, b: BrandGuidelinesBundle) -> GuidelinesBundleView:
        return cls(
            report_id=str(b.report_id), project_id=b.project_id,
            primary_category=b.primary_category.value,
            secondary_categories=[c.value for c in b.secondary_categories],
            archetype=b.archetype.value, tone=b.tone.value,
            positioning_statement=b.positioning_statement,
            visual=VisualDirectionView(direction=_visual_view(b.visual)),
            validation_rules=[
                ValidationRuleView(id=str(x.id), subject=x.subject, assertion=x.assertion,
                                   enforcement=x.enforcement.value, severity=x.severity.value,
                                   checkable_hint=x.checkable_hint, evidence_ids=_ids(x.evidence_ids))
                for x in b.validation_rules
            ],
            is_usable=b.is_usable, created_at=_iso(b.created_at),
        )


@dataclass(frozen=True, slots=True)
class BrandDecisionTraceView:
    """An explanation of one decision: the decision, what it derives from/expresses, its evidence."""

    decision: BrandDecisionView
    derives_from: list[BrandDecisionView]
    expresses: list[BrandDecisionView]
    evidence: list[dict]
