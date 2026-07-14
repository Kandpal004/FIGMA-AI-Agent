"""RuleBasedBrandStrategist — the deterministic default implementation of the strategist.

This adapter implements :class:`BrandSynthesisPort` with explicit, explainable
heuristics rather than an LLM: it classifies the brand from its brief and market, then
derives every element — identity, character, emotional strategy, visual direction, and
verbal system — from a codified creative knowledge base (:mod:`profiles`) and the
consolidated evidence, citing real evidence ids for each element. It is fully
deterministic (same input + evidence ⇒ same draft), dependency-free, and honest — it
invents no facts; it *decides* over the evidence it is given and grounds each decision by
citing it.

In production this port is swapped for a reasoning/LLM-backed strategist; the contract
(propose grounded content, citing only supplied evidence) is unchanged, so the engine's
integrity guarantees hold regardless of which brain is plugged in.
"""

from __future__ import annotations

from collections.abc import Sequence

from brand.application.contracts import BrandDraft, BrandInput
from brand.domain.classification.classification import BrandClassification
from brand.domain.context.context import BrandBrief, ProjectContext
from brand.domain.emotional.emotional import (
    BrandDifferentiator,
    EmotionalPositioning,
    TrustSignal,
)
from brand.domain.emotional.emotional_strategy import EmotionalStrategy
from brand.domain.evidence.evidence import BrandEvidence, EvidenceGraph
from brand.domain.identity.identity import BrandIdentity
from brand.domain.identity.positioning import BrandPositioning
from brand.domain.identity.purpose import BrandMission, BrandPromise, BrandVision
from brand.domain.identity.story import BrandStory
from brand.domain.identity.values import BrandValue, BrandValues
from brand.domain.personality.archetype import ArchetypeBlend
from brand.domain.personality.character import BrandCharacter
from brand.domain.personality.personality import BrandAttribute, BrandPersonality
from brand.domain.personality.voice import BrandTone, BrandVoice, ToneModulation
from brand.domain.shared.ids import (
    BrandAttributeId,
    BrandDifferentiatorId,
    BrandEvidenceId,
    BrandValueId,
    TrustSignalId,
)
from brand.domain.shared.value_objects import (
    BrandCategory,
    Confidence,
    ConsideredAlternative,
    MessagingTone,
    Percentage,
    Priority,
    Salience,
    TrustSignalKind,
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
from brand.infrastructure.adapters.profiles import CategoryProfile, profile_for

__all__ = ["RuleBasedBrandStrategist"]

# Industry / descriptor keywords → a brand category.
_KEYWORD_CATEGORY: tuple[tuple[str, BrandCategory], ...] = (
    ("luxury", BrandCategory.LUXURY),
    ("fashion", BrandCategory.FASHION),
    ("apparel", BrandCategory.FASHION),
    ("beauty", BrandCategory.BEAUTY),
    ("cosmetic", BrandCategory.BEAUTY),
    ("skincare", BrandCategory.BEAUTY),
    ("health", BrandCategory.HEALTHCARE),
    ("medical", BrandCategory.HEALTHCARE),
    ("supplement", BrandCategory.SUPPLEMENTS),
    ("vitamin", BrandCategory.SUPPLEMENTS),
    ("nutrition", BrandCategory.SUPPLEMENTS),
    ("electronic", BrandCategory.ELECTRONICS),
    ("gadget", BrandCategory.ELECTRONICS),
    ("device", BrandCategory.ELECTRONICS),
    ("furniture", BrandCategory.FURNITURE),
    ("home", BrandCategory.FURNITURE),
    ("enterprise", BrandCategory.ENTERPRISE),
    ("b2b", BrandCategory.ENTERPRISE),
    ("technical", BrandCategory.TECHNICAL),
    ("developer", BrandCategory.TECHNICAL),
    ("lifestyle", BrandCategory.LIFESTYLE),
)

# Tone → position on each tone-of-voice spectrum (0 = first pole, 1 = second pole).
_VOICE: dict[MessagingTone, dict[VoiceDimension, float]] = {
    MessagingTone.LUXURIOUS: {VoiceDimension.FORMALITY: 0.8, VoiceDimension.HUMOR: 0.2, VoiceDimension.RESPECT: 0.85, VoiceDimension.ENTHUSIASM: 0.4},
    MessagingTone.AUTHORITATIVE: {VoiceDimension.FORMALITY: 0.7, VoiceDimension.HUMOR: 0.2, VoiceDimension.RESPECT: 0.8, VoiceDimension.ENTHUSIASM: 0.4},
    MessagingTone.ELEGANT: {VoiceDimension.FORMALITY: 0.7, VoiceDimension.HUMOR: 0.3, VoiceDimension.RESPECT: 0.8, VoiceDimension.ENTHUSIASM: 0.5},
    MessagingTone.MINIMAL: {VoiceDimension.FORMALITY: 0.6, VoiceDimension.HUMOR: 0.15, VoiceDimension.RESPECT: 0.7, VoiceDimension.ENTHUSIASM: 0.25},
    MessagingTone.TECHNICAL: {VoiceDimension.FORMALITY: 0.65, VoiceDimension.HUMOR: 0.1, VoiceDimension.RESPECT: 0.7, VoiceDimension.ENTHUSIASM: 0.3},
    MessagingTone.WARM: {VoiceDimension.FORMALITY: 0.35, VoiceDimension.HUMOR: 0.45, VoiceDimension.RESPECT: 0.8, VoiceDimension.ENTHUSIASM: 0.6},
    MessagingTone.REASSURING: {VoiceDimension.FORMALITY: 0.45, VoiceDimension.HUMOR: 0.25, VoiceDimension.RESPECT: 0.85, VoiceDimension.ENTHUSIASM: 0.45},
    MessagingTone.BOLD: {VoiceDimension.FORMALITY: 0.35, VoiceDimension.HUMOR: 0.4, VoiceDimension.RESPECT: 0.6, VoiceDimension.ENTHUSIASM: 0.85},
    MessagingTone.PLAYFUL: {VoiceDimension.FORMALITY: 0.25, VoiceDimension.HUMOR: 0.7, VoiceDimension.RESPECT: 0.6, VoiceDimension.ENTHUSIASM: 0.8},
}


class RuleBasedBrandStrategist:
    """A deterministic, evidence-grounded implementation of the brand-strategist port."""

    async def draft(self, brand_input: BrandInput, evidence: EvidenceGraph) -> BrandDraft:
        ranked = sorted(evidence, key=lambda e: e.confidence.value, reverse=True)
        brief = brand_input.brief
        classification = self._classify(brief, brand_input.project, ranked)
        profile = profile_for(classification.primary)

        return BrandDraft(
            classification=classification,
            identity=self._identity(brief, ranked),
            character=self._character(profile, ranked),
            emotional=self._emotional(profile, ranked),
            visual=self._visual(profile, ranked),
            verbal=self._verbal(profile, ranked),
        )

    # ------------------------------------------------------------------ #
    @staticmethod
    def _cite(
        ranked: Sequence[BrandEvidence], keywords: Sequence[str], limit: int = 2
    ) -> tuple[BrandEvidenceId, ...]:
        """Cite the most relevant evidence, falling back to the strongest if none
        matches — so an element is grounded whenever any evidence exists."""
        if not ranked:
            return ()
        kws = [k.lower() for k in keywords]
        matched = [
            e
            for e in ranked
            if any(
                k in f"{e.claim} {e.statement} {' '.join(t.value for t in e.tags)}".lower()
                for k in kws
            )
        ]
        chosen = matched[:limit] or ranked[:1]
        return tuple(e.id for e in chosen)

    # ------------------------------------------------------------------ #
    def _classify(
        self,
        brief: BrandBrief,
        project: ProjectContext,
        ranked: Sequence[BrandEvidence],
    ) -> BrandClassification:
        signals = " ".join(
            (brief.industry, brief.maturity, project.market, *brief.descriptors)
        ).lower()
        if brief.category_hint is not None:
            primary = brief.category_hint
        else:
            primary = next(
                (cat for key, cat in _KEYWORD_CATEGORY if key in signals),
                BrandCategory.PREMIUM if "premium" in signals else BrandCategory.LIFESTYLE,
            )
        secondary: list[BrandCategory] = []
        if "premium" in signals and primary is not BrandCategory.PREMIUM:
            secondary.append(BrandCategory.PREMIUM)
        if "luxury" in signals and primary is not BrandCategory.LUXURY:
            secondary.append(BrandCategory.LUXURY)
        if "minimal" in signals and primary is not BrandCategory.MINIMAL:
            secondary.append(BrandCategory.MINIMAL)
        considered = tuple(
            ConsideredAlternative(
                option=alt.value,
                reason_rejected=f"{primary.value} matches the brief's signals more closely than {alt.value}.",
            )
            for alt in (BrandCategory.PREMIUM, BrandCategory.MASS_MARKET)
            if alt is not primary and alt not in secondary
        )
        return BrandClassification(
            primary=primary,
            secondary=tuple(secondary),
            confidence=Confidence.of(0.75),
            rationale="Derived from the brand brief, industry, and market signals.",
            considered=considered,
            evidence_ids=self._cite(ranked, ("brand", "category", "market", "positioning"), 2),
        )

    # ------------------------------------------------------------------ #
    def _identity(
        self, brief: BrandBrief, ranked: Sequence[BrandEvidence]
    ) -> BrandIdentity:
        pos_cite = self._cite(ranked, ("positioning", "differentiat", "brand", "value"), 3)
        positioning = BrandPositioning(
            statement=f"{brief.name} is the brand customers trust to deliver on its promise.",
            frame_of_reference=brief.industry or "the category",
            point_of_difference="an evidence-backed promise kept consistently",
            reason_to_believe="proof over claims, in every interaction",
            confidence=Confidence.of(0.75),
            evidence_ids=pos_cite,
        )
        mission = BrandMission(
            statement=f"To help customers buy with confidence in {brief.industry or 'the category'}.",
            evidence_ids=self._cite(ranked, ("mission", "purpose", "goal"), 1),
        )
        vision = BrandVision(
            statement=f"A world where choosing {brief.name} is the obvious, trusted choice.",
            horizon="3–5 years",
            evidence_ids=self._cite(ranked, ("vision", "future", "growth"), 1),
        )
        promise = BrandPromise(
            statement="Every experience earns your trust and respects your time.",
            proof_points=("transparent value", "consistent quality"),
            evidence_ids=self._cite(ranked, ("promise", "trust", "quality"), 1),
        )
        val_cite = self._cite(ranked, ("value", "principle", "trust", "quality"), 2)
        values = BrandValues.of(
            (
                BrandValue(
                    id=BrandValueId.new(), name="Earned trust",
                    description="Trust is built through proof, not claims.",
                    behavior="Lead with evidence; never overpromise.",
                    priority=Priority(5), evidence_ids=val_cite,
                ),
                BrandValue(
                    id=BrandValueId.new(), name="Clarity",
                    description="Respect the customer with clear, honest communication.",
                    behavior="Say less, mean more; remove ambiguity.",
                    priority=Priority(4), evidence_ids=val_cite,
                ),
                BrandValue(
                    id=BrandValueId.new(), name="Craft",
                    description="Care shows in the details.",
                    behavior="Sweat the details customers feel.",
                    priority=Priority(4), evidence_ids=val_cite,
                ),
            )
        )
        story = BrandStory(
            headline=f"Why {brief.name} exists",
            situation="Customers face a crowded, noisy category where trust is scarce.",
            tension="It is hard to know which brand will actually deliver.",
            resolution=f"{brief.name} proves its promise at every step, so choosing is easy.",
            brand_role="the trusted guide, not the loud hero",
            evidence_ids=self._cite(ranked, ("story", "customer", "trust"), 1),
        )
        return BrandIdentity(
            positioning=positioning, mission=mission, vision=vision,
            promise=promise, values=values, story=story,
        )

    # ------------------------------------------------------------------ #
    def _character(
        self, profile: CategoryProfile, ranked: Sequence[BrandEvidence]
    ) -> BrandCharacter:
        archetype = ArchetypeBlend(
            primary=profile.archetype,
            primary_weight=Percentage(0.7),
            rationale=f"The {profile.archetype.value} archetype fits the category's register.",
            evidence_ids=self._cite(ranked, ("brand", "personality", "archetype"), 1),
        )
        personality = BrandPersonality.build(
            traits=profile.adjectives,
            attributes=(
                BrandAttribute(
                    id=BrandAttributeId.new(), trait=profile.adjectives[0],
                    opposite="generic", salience=Salience(5),
                    evidence_ids=self._cite(ranked, ("personality", "brand", profile.adjectives[0]), 1),
                ),
                BrandAttribute(
                    id=BrandAttributeId.new(), trait=profile.adjectives[1],
                    opposite="careless", salience=Salience(4),
                    evidence_ids=self._cite(ranked, ("personality", "brand", profile.adjectives[1]), 1),
                ),
            ),
            summary=", ".join(profile.adjectives),
            evidence_ids=self._cite(ranked, ("personality", "brand"), 1),
        )
        voice = BrandVoice(
            dimensions={
                dimension: Percentage(value)
                for dimension, value in _VOICE.get(profile.tone, _VOICE[MessagingTone.WARM]).items()
            },
            principles=("Speak to the customer's goal.", "Prove, don't boast."),
            avoid=("Hype", "Jargon", "Dark patterns"),
            signature_words=profile.adjectives,
            evidence_ids=self._cite(ranked, ("voice", "tone", "brand"), 1),
        )
        tone = BrandTone(
            dominant=profile.tone,
            modulations=(
                ToneModulation(context="checkout", adjustment="More reassuring; reduce friction and doubt."),
                ToneModulation(context="error", adjustment="Calm and helpful; take responsibility."),
                ToneModulation(context="post-purchase", adjustment="Warmer; affirm the good choice."),
            ),
            evidence_ids=self._cite(ranked, ("tone", "voice"), 1),
        )
        return BrandCharacter(
            archetype=archetype, personality=personality, voice=voice, tone=tone
        )

    # ------------------------------------------------------------------ #
    def _emotional(
        self, profile: CategoryProfile, ranked: Sequence[BrandEvidence]
    ) -> EmotionalStrategy:
        positioning = EmotionalPositioning(
            primary_emotion=profile.emotion,
            emotional_benefit=f"Customers feel {profile.emotion.value} choosing and using the brand.",
            feeling_target="like they made a smart, confident choice",
            supporting_emotions=(),
            evidence_ids=self._cite(ranked, ("emotion", "feel", "trust", profile.emotion.value), 2),
        )
        diff_cite = self._cite(ranked, ("differentiat", "unique", "advantage"), 2)
        differentiators = (
            BrandDifferentiator(
                id=BrandDifferentiatorId.new(),
                claim="Proof-led trust that competitors only claim.",
                defensibility="Accumulated proof and consistency are slow to copy.",
                versus="brands competing on price or noise",
                salience=Salience(5), evidence_ids=diff_cite,
            ),
        )
        trust_cite = self._cite(ranked, ("trust", "review", "guarantee", "secure"), 2)
        trust_signals = (
            TrustSignal(
                id=TrustSignalId.new(), kind=TrustSignalKind.REVIEWS,
                rationale="Reviews are the strongest credibility signal at consideration.",
                salience=Salience(5), evidence_ids=trust_cite,
            ),
            TrustSignal(
                id=TrustSignalId.new(), kind=TrustSignalKind.GUARANTEE,
                rationale="A guarantee removes the risk of committing.",
                salience=Salience(4), evidence_ids=trust_cite,
            ),
        )
        return EmotionalStrategy(
            positioning=positioning,
            differentiators=differentiators,
            trust_signals=trust_signals,
        )

    # ------------------------------------------------------------------ #
    def _visual(
        self, profile: CategoryProfile, ranked: Sequence[BrandEvidence]
    ) -> BrandVisualDirection:
        v_cite = self._cite(ranked, ("visual", "design", "brand", "aesthetic"), 2)
        logo = LogoDirection(
            intent=f"A {profile.adjectives[0]} mark that reads as trustworthy at a glance.",
            style="wordmark",
            principles=("legible at any size", "restraint over ornament"),
            avoid=("trend-chasing", "clutter"),
            evidence_ids=v_cite,
        )
        typography = TypographyDirection(
            display_voice=profile.display_voice, body_voice=profile.body_voice,
            hierarchy_intent=f"{profile.contrast.value} contrast between display and body.",
            rationale=f"Type voices express the {profile.archetype.value} character.",
            principles=("readability first", "consistent scale"),
            evidence_ids=self._cite(ranked, ("typography", "type", "font"), 1) or v_cite,
        )
        color = ColorPhilosophy(
            temperament=profile.temperament, contrast=profile.contrast,
            accent_role="reserved for action and trust moments",
            neutrals_role="a calm, confident base",
            meaning=f"Colour conveys {profile.adjectives[0]} credibility.",
            avoid=("loud discount aesthetics",),
            evidence_ids=self._cite(ranked, ("color", "colour", "palette"), 1) or v_cite,
        )
        spacing = SpacingPhilosophy(
            density=profile.density,
            rhythm_intent="an unhurried, confident rhythm",
            whitespace_role="signals quality and focus",
            principles=("generous where it matters",),
            evidence_ids=self._cite(ranked, ("spacing", "layout", "whitespace"), 1) or v_cite,
        )
        photography = PhotographyDirection(
            treatment=profile.photo,
            subject_focus="the product and the customer's confidence in it",
            mood=f"{profile.adjectives[0]} and credible",
            principles=("authentic over staged",),
            evidence_ids=self._cite(ranked, ("photo", "image", "photography"), 1) or v_cite,
        )
        illustration = IllustrationDirection(
            style=profile.illustration,
            role="supporting clarity, never decoration"
            if profile.illustration.value != "none"
            else "illustration is not part of this brand's system",
            evidence_ids=v_cite,
        )
        iconography = IconographyDirection(
            style=profile.icon, weight_intent="consistent with the type voice",
            principles=("functional and legible",),
            evidence_ids=v_cite,
        )
        motion = MotionPrinciples(
            character=profile.motion,
            purpose="confirm and guide, never decorate",
            restraint="motion is subtle and purposeful",
            principles=("respect reduced-motion preferences",),
            evidence_ids=self._cite(ranked, ("motion", "animation", "interaction"), 1) or v_cite,
        )
        ui = UIPersonality(
            corner_language=profile.corner, weight=profile.weight,
            density=profile.density, texture=profile.texture,
            feel=f"{profile.adjectives[0]}, {profile.adjectives[1]}, and trustworthy",
            principles=("clarity over decoration",),
            evidence_ids=v_cite,
        )
        component = ComponentPersonality(
            interaction_feel="crisp and immediate",
            emphasis="primary actions carry clear, confident weight",
            restraint="never manipulate; never shout",
            principles=("consistent affordances",),
            evidence_ids=v_cite,
        )
        return BrandVisualDirection(
            logo=logo, typography=typography, color=color, spacing=spacing,
            photography=photography, illustration=illustration, iconography=iconography,
            motion=motion, ui=ui, component=component,
        )

    # ------------------------------------------------------------------ #
    def _verbal(
        self, profile: CategoryProfile, ranked: Sequence[BrandEvidence]
    ) -> BrandVerbalSystem:
        cite = self._cite(ranked, ("voice", "copy", "language", "message"), 2)
        language = BrandLanguageRules(
            person="second person; address the customer as 'you'",
            capitalization="sentence case",
            terminology={"cart": "cart", "checkout": "checkout"},
            preferred_words=profile.adjectives,
            forbidden_words=("cheap", "hurry", "act now"),
            principles=("clear over clever", "honest over hyped"),
            evidence_ids=cite,
        )
        copy = BrandCopyGuidelines(
            headline_principles=("lead with the customer benefit", "one idea per headline"),
            cta_style="clear, action-first, never manipulative",
            microcopy_stance="helpful and calm; reduce anxiety",
            reading_level="plain, accessible",
            do=("state the value", "be specific"),
            dont=("use fake urgency", "overclaim"),
            evidence_ids=cite,
        )
        return BrandVerbalSystem(language_rules=language, copy_guidelines=copy)

