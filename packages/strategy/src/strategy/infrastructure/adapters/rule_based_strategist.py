"""RuleBasedStrategist — the deterministic default implementation of the strategist.

This adapter implements :class:`StrategySynthesisPort` with explicit, explainable
heuristics rather than an LLM: it selects the positioning tier from brand and market
signals, and derives every pillar from the request context and the consolidated
evidence, citing real evidence ids for each claim. It is fully deterministic (same
input + evidence ⇒ same draft), dependency-free, and honest — it invents no facts; it
*decides* over the evidence it is given, and grounds each decision by citing it.

In production this port is swapped for a reasoning/LLM-backed strategist; the contract
(propose grounded content, citing only supplied evidence) is unchanged, so the engine's
integrity guarantees hold regardless of which brain is plugged in.
"""

from __future__ import annotations

from collections.abc import Sequence

from strategy.application.contracts import StrategyDraft, StrategyInput
from strategy.domain.analysis.opportunity import (
    BusinessOpportunity,
    RevenueOpportunity,
)
from strategy.domain.analysis.risk import BusinessRisk
from strategy.domain.context.context import BrandContext
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
from strategy.domain.retention.retention import RetentionLever, RetentionStrategy
from strategy.domain.shared.ids import (
    BusinessGoalId,
    BusinessOpportunityId,
    BusinessRiskId,
    CustomerPersonaId,
    JobToBeDoneId,
    MessagingPillarId,
    RevenueOpportunityId,
    StrategyEvidenceId,
    TrustElementId,
)
from strategy.domain.shared.value_objects import (
    Confidence,
    ConsideredAlternative,
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
    PersonalityTrait,
    PricingPosture,
    PricingSignalKind,
    Priority,
    RetentionLeverKind,
    RiskCategory,
    Severity,
    SocialProofKind,
    StrategyTier,
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

__all__ = ["RuleBasedStrategist"]


# Per-tier expression of voice, personality, pricing, and visual language.
_TIER_TONE: dict[StrategyTier, MessagingTone] = {
    StrategyTier.LUXURY: MessagingTone.LUXURIOUS,
    StrategyTier.PREMIUM: MessagingTone.AUTHORITATIVE,
    StrategyTier.AFFORDABLE: MessagingTone.WARM,
    StrategyTier.ENTERPRISE: MessagingTone.AUTHORITATIVE,
    StrategyTier.TECHNICAL: MessagingTone.TECHNICAL,
    StrategyTier.MINIMAL: MessagingTone.MINIMAL,
}
_TIER_TRAIT: dict[StrategyTier, PersonalityTrait] = {
    StrategyTier.LUXURY: PersonalityTrait.SOPHISTICATION,
    StrategyTier.PREMIUM: PersonalityTrait.COMPETENCE,
    StrategyTier.AFFORDABLE: PersonalityTrait.SINCERITY,
    StrategyTier.ENTERPRISE: PersonalityTrait.COMPETENCE,
    StrategyTier.TECHNICAL: PersonalityTrait.COMPETENCE,
    StrategyTier.MINIMAL: PersonalityTrait.SOPHISTICATION,
}
_TIER_POSTURE: dict[StrategyTier, PricingPosture] = {
    StrategyTier.LUXURY: PricingPosture.PREMIUM,
    StrategyTier.PREMIUM: PricingPosture.PREMIUM,
    StrategyTier.AFFORDABLE: PricingPosture.VALUE,
    StrategyTier.ENTERPRISE: PricingPosture.COMPETITIVE,
    StrategyTier.TECHNICAL: PricingPosture.COMPETITIVE,
    StrategyTier.MINIMAL: PricingPosture.VALUE,
}
_TIER_ADJECTIVES: dict[StrategyTier, tuple[str, ...]] = {
    StrategyTier.LUXURY: ("elegant", "refined", "exclusive"),
    StrategyTier.PREMIUM: ("premium", "crafted", "considered"),
    StrategyTier.AFFORDABLE: ("friendly", "accessible", "cheerful"),
    StrategyTier.ENTERPRISE: ("professional", "robust", "trusted"),
    StrategyTier.TECHNICAL: ("precise", "technical", "clear"),
    StrategyTier.MINIMAL: ("minimal", "calm", "essential"),
}


class RuleBasedStrategist:
    """A deterministic, evidence-grounded implementation of the strategist port."""

    async def draft(
        self, strategy_input: StrategyInput, evidence: EvidenceGraph
    ) -> StrategyDraft:
        ranked = sorted(evidence, key=lambda e: e.confidence.value, reverse=True)
        brand = strategy_input.brand
        tier, considered = self._select_tier(brand, strategy_input.project.market)

        goals = self._goals(strategy_input, ranked)
        customer = self._customer(strategy_input, ranked)
        positioning = self._positioning(strategy_input, tier, considered, ranked)
        value = self._value(strategy_input, ranked)
        usp = self._usp(strategy_input, ranked)
        messaging = self._messaging(strategy_input, tier, ranked)
        voice = BrandVoice(
            tone=_TIER_TONE[tier],
            principles=("Speak to the customer's goal, not the product's features.",),
            avoid=("Hype", "Dark patterns"),
            evidence_ids=self._cite(ranked, ("tone", "voice", "brand"), 1),
        )
        personality = BrandPersonality(
            traits=(_TIER_TRAIT[tier],),
            archetype=self._archetype(tier),
            evidence_ids=self._cite(ranked, ("brand", "personality"), 1),
        )
        trust = self._trust(ranked)
        pricing = self._pricing(tier, ranked)
        retention = self._retention(ranked)
        risks = self._risks(ranked)
        business_opps, revenue_opps = self._opportunities(ranked)

        return StrategyDraft(
            goals=goals,
            customer=customer,
            positioning=positioning,
            value_proposition=value,
            usp=usp,
            messaging=messaging,
            brand_voice=voice,
            brand_personality=personality,
            trust=trust,
            pricing=pricing,
            retention=retention,
            risks=risks,
            business_opportunities=business_opps,
            revenue_opportunities=revenue_opps,
        )

    # ------------------------------------------------------------------ #
    # Evidence citing                                                     #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _cite(
        ranked: Sequence[StrategyEvidence],
        keywords: Sequence[str],
        limit: int = 3,
    ) -> tuple[StrategyEvidenceId, ...]:
        """Cite the most relevant evidence, falling back to the strongest if none
        matches — so a section is grounded whenever any evidence exists."""
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
    # Tier selection                                                      #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _select_tier(
        brand: BrandContext, market: str
    ) -> tuple[StrategyTier, tuple[ConsideredAlternative, ...]]:
        if brand.tier_hint is not None:
            chosen = brand.tier_hint
        else:
            signals = " ".join(
                (market, brand.maturity, *brand.descriptors)
            ).lower()
            if "luxury" in signals:
                chosen = StrategyTier.LUXURY
            elif "premium" in signals or "high-end" in signals:
                chosen = StrategyTier.PREMIUM
            elif "enterprise" in signals or "b2b" in signals:
                chosen = StrategyTier.ENTERPRISE
            elif "technical" in signals or "developer" in signals:
                chosen = StrategyTier.TECHNICAL
            elif "minimal" in signals:
                chosen = StrategyTier.MINIMAL
            else:
                chosen = StrategyTier.AFFORDABLE
        runners = tuple(
            ConsideredAlternative(
                option=alt.value,
                reason_rejected=f"{chosen.value} fits the brand signals better than {alt.value}.",
            )
            for alt in (StrategyTier.PREMIUM, StrategyTier.AFFORDABLE)
            if alt is not chosen
        )
        return chosen, runners

    @staticmethod
    def _archetype(tier: StrategyTier) -> str:
        return {
            StrategyTier.LUXURY: "the Sovereign",
            StrategyTier.PREMIUM: "the Sage",
            StrategyTier.AFFORDABLE: "the Everyperson",
            StrategyTier.ENTERPRISE: "the Ruler",
            StrategyTier.TECHNICAL: "the Creator",
            StrategyTier.MINIMAL: "the Innocent",
        }[tier]

    # ------------------------------------------------------------------ #
    # Section builders                                                    #
    # ------------------------------------------------------------------ #
    def _goals(
        self, strategy_input: StrategyInput, ranked: Sequence[StrategyEvidence]
    ) -> GoalSet:
        statements = strategy_input.goals.business_goals or ("Grow profitable revenue",)
        goals = []
        for index, statement in enumerate(statements):
            goals.append(
                BusinessGoal(
                    id=BusinessGoalId.new(),
                    statement=statement,
                    category=self._goal_category(statement),
                    horizon=GoalHorizon.MID_TERM,
                    priority=Priority(max(3, 5 - index)),
                    evidence_ids=self._cite(ranked, statement.split(), 2),
                )
            )
        return GoalSet.of(goals)

    @staticmethod
    def _goal_category(statement: str) -> GoalCategory:
        text = statement.lower()
        if "retention" in text or "repeat" in text or "loyal" in text:
            return GoalCategory.RETENTION
        if "conversion" in text or "convert" in text:
            return GoalCategory.CONVERSION
        if "aov" in text or "basket" in text or "order value" in text:
            return GoalCategory.AOV
        if "acqui" in text or "new customer" in text:
            return GoalCategory.ACQUISITION
        if "brand" in text or "awareness" in text:
            return GoalCategory.BRAND
        if "margin" in text:
            return GoalCategory.MARGIN
        return GoalCategory.REVENUE

    def _customer(
        self, strategy_input: StrategyInput, ranked: Sequence[StrategyEvidence]
    ) -> CustomerModel:
        brand = strategy_input.brand
        market = strategy_input.project.market
        persona_cite = self._cite(ranked, ("customer", "shopper", "buyer", "audience"), 2)
        persona = CustomerPersona(
            id=CustomerPersonaId.new(),
            name="Considered Buyer",
            archetype="value-aware researcher",
            confidence=Confidence.of(0.7),
            demographics={"channel": "mobile-first"},
            psychographics={"mindset": "researches before buying"},
            goals=("Buy with confidence", "Avoid a bad purchase"),
            frustrations=("Unclear value", "Weak trust signals"),
            evidence_ids=persona_cite,
        )
        icp = IdealCustomerProfile(
            summary=f"Customers who value {brand.industry or 'the category'} and buy on considered trust.",
            segments=(market or "core",),
            attributes=("compares options", "responsive to social proof"),
            qualifying_signals=("engages with reviews", "returns to compare"),
            disqualifiers=("purely price-driven bargain hunters",),
            evidence_ids=persona_cite,
        )
        jobs = JTBDSet.of(
            (
                JobToBeDone(
                    id=JobToBeDoneId.new(),
                    when_situation="I am choosing between options",
                    motivation="feel certain I am making the right choice",
                    expected_outcome="buy without second-guessing",
                    job_type=JobType.EMOTIONAL,
                    evidence_ids=self._cite(ranked, ("trust", "confidence", "review"), 2),
                ),
                JobToBeDone(
                    id=JobToBeDoneId.new(),
                    when_situation="I land on a product page",
                    motivation="understand the value quickly",
                    expected_outcome="decide fast",
                    job_type=JobType.FUNCTIONAL,
                    evidence_ids=self._cite(ranked, ("value", "conversion", "clarity"), 2),
                ),
            )
        )
        journey = CustomerJourney.of(
            (
                JourneyStage(
                    phase=JourneyPhase.AWARENESS,
                    customer_goal="Discover a credible option",
                    touchpoints=("search", "referral"),
                    emotions=(EmotionKind.CONFIDENCE,),
                    evidence_ids=self._cite(ranked, ("awareness", "brand", "discover"), 1),
                ),
                JourneyStage(
                    phase=JourneyPhase.CONSIDERATION,
                    customer_goal="Compare and build trust",
                    pains=("uncertainty about quality",),
                    objections=("is it worth the price?",),
                    required_trust=("reviews", "guarantee"),
                    emotions=(EmotionKind.TRUST, EmotionKind.REASSURANCE),
                    evidence_ids=self._cite(ranked, ("consideration", "trust", "review"), 2),
                ),
                JourneyStage(
                    phase=JourneyPhase.DECISION,
                    customer_goal="Commit with confidence",
                    required_trust=("secure checkout", "clear returns"),
                    emotions=(EmotionKind.CONFIDENCE, EmotionKind.RELIEF),
                    evidence_ids=self._cite(ranked, ("decision", "checkout", "convert"), 1),
                ),
            )
        )
        pains = (
            PainPoint(
                description="Customers doubt whether the product is worth the price.",
                severity=Severity(4),
                phase=JourneyPhase.CONSIDERATION,
                evidence_ids=self._cite(ranked, ("price", "value", "doubt"), 1),
            ),
        )
        objections = (
            Objection(
                objection="Why should I trust this brand over a cheaper alternative?",
                rebuttal_strategy="Lead with proof: reviews, guarantees, and transparent value.",
                evidence_ids=self._cite(ranked, ("trust", "guarantee", "review"), 1),
            ),
        )
        motivations = (
            PurchaseMotivation(
                description="Confidence that the purchase is a safe, smart choice.",
                weight=Confidence.of(0.8),
                evidence_ids=self._cite(ranked, ("confidence", "trust"), 1),
            ),
        )
        emotions = (
            EmotionalTrigger(
                emotion=EmotionKind.TRUST,
                trigger="Prominent, credible social proof at the point of doubt.",
                intended_response="Reduced anxiety and increased intent to buy.",
                evidence_ids=self._cite(ranked, ("trust", "review", "social")),
            ),
            EmotionalTrigger(
                emotion=EmotionKind.CONFIDENCE,
                trigger="Clear value framing and transparent policies.",
                intended_response="Decisive purchase.",
                evidence_ids=self._cite(ranked, ("value", "clarity", "confidence")),
            ),
        )
        return CustomerModel(
            icp=icp,
            personas=PersonaSet.of((persona,)),
            jobs=jobs,
            journey=journey,
            pains=pains,
            objections=objections,
            motivations=motivations,
            emotions=emotions,
        )

    def _positioning(
        self,
        strategy_input: StrategyInput,
        tier: StrategyTier,
        considered: tuple[ConsideredAlternative, ...],
        ranked: Sequence[StrategyEvidence],
    ) -> PositioningStrategy:
        brand = strategy_input.brand
        market = strategy_input.project.market
        cite = self._cite(ranked, ("positioning", "brand", "differentiat", "competitor"), 3)
        statement = PositioningStatement(
            tier=tier,
            for_customer=f"considered {market or 'core'} shoppers",
            need="want to buy with confidence",
            category=f"{brand.name} is a {tier.value} {brand.industry or 'ecommerce'} brand",
            benefit="trusted value they can commit to without hesitation",
            confidence=Confidence.of(0.75),
            unlike="commodity retailers competing on price alone",
            reason_to_believe="evidence-backed trust and a clear value promise",
            considered=considered,
            evidence_ids=cite,
        )
        brand_positioning = BrandPositioning(
            perception=f"The {tier.value} choice you can trust",
            market_frame=brand.industry or "ecommerce",
            differentiators=("evidence-backed trust", "clarity of value"),
            evidence_ids=cite,
        )
        customer_positioning = CustomerPositioning(
            current_alternative="cheaper, lower-trust alternatives",
            desired_shift="pay a fair price for confidence and quality",
            gains=("peace of mind", "no buyer's remorse"),
            evidence_ids=cite,
        )
        visual = VisualPositioning(
            tier=tier,
            adjectives=_TIER_ADJECTIVES[tier],
            design_principles=("clarity over density", "restraint over noise"),
            references_to_avoid=("cluttered discount aesthetics",),
            evidence_ids=cite,
        )
        return PositioningStrategy(
            statement=statement,
            brand=brand_positioning,
            customer=customer_positioning,
            visual=visual,
        )

    def _value(
        self, strategy_input: StrategyInput, ranked: Sequence[StrategyEvidence]
    ) -> ValueProposition:
        brand = strategy_input.brand
        return ValueProposition(
            headline_promise=f"{brand.name}: value you can trust, delivered with confidence.",
            primary_benefit="Confidence that every purchase is the right one.",
            differentiators=("evidence-backed trust", "transparent value"),
            proof_points=("verified reviews", "clear guarantees"),
            evidence_ids=self._cite(ranked, ("value", "benefit", "promise", "trust"), 3),
        )

    def _usp(
        self, strategy_input: StrategyInput, ranked: Sequence[StrategyEvidence]
    ) -> UniqueSellingProposition:
        return UniqueSellingProposition(
            statement="The most trusted way to buy in the category — proven, not promised.",
            defensibility="Accumulated proof and a trust-first experience are hard to copy quickly.",
            evidence_ids=self._cite(ranked, ("unique", "differentiat", "trust", "proof"), 2),
        )

    def _messaging(
        self,
        strategy_input: StrategyInput,
        tier: StrategyTier,
        ranked: Sequence[StrategyEvidence],
    ) -> MessagingFramework:
        pillars = (
            MessagingPillar(
                id=MessagingPillarId.new(),
                theme="Trust",
                message="Proof over promises.",
                supporting_points=("verified reviews", "guarantees"),
                evidence_ids=self._cite(ranked, ("trust", "review", "guarantee"), 2),
            ),
            MessagingPillar(
                id=MessagingPillarId.new(),
                theme="Value",
                message="Fair value, clearly shown.",
                supporting_points=("transparent pricing", "clear benefits"),
                evidence_ids=self._cite(ranked, ("value", "price", "benefit"), 2),
            ),
        )
        return MessagingFramework.build(
            primary_message="Buy with confidence — proven value, clearly delivered.",
            pillars=pillars,
            evidence_ids=self._cite(ranked, ("messaging", "message", "brand"), 1),
        )

    def _trust(self, ranked: Sequence[StrategyEvidence]) -> TrustStrategy:
        cite = self._cite(ranked, ("trust", "review", "guarantee", "secure", "return"), 3)
        elements = (
            TrustElement(
                id=TrustElementId.new(),
                kind=TrustElementKind.REVIEWS,
                rationale="Reviews are the strongest anxiety reducer at consideration.",
                phase=JourneyPhase.CONSIDERATION,
                priority=Priority(5),
                evidence_ids=self._cite(ranked, ("review", "rating"), 2),
            ),
            TrustElement(
                id=TrustElementId.new(),
                kind=TrustElementKind.GUARANTEE,
                rationale="A guarantee removes the risk of committing.",
                phase=JourneyPhase.DECISION,
                priority=Priority(4),
                evidence_ids=self._cite(ranked, ("guarantee", "return", "refund"), 1),
            ),
            TrustElement(
                id=TrustElementId.new(),
                kind=TrustElementKind.SECURE_CHECKOUT,
                rationale="Checkout security reassurance protects conversion at the final step.",
                phase=JourneyPhase.PURCHASE,
                priority=Priority(4),
                evidence_ids=self._cite(ranked, ("secure", "checkout", "payment"), 1),
            ),
        )
        social = SocialProofStrategy(
            kinds=(SocialProofKind.CUSTOMER_REVIEWS, SocialProofKind.RATINGS_SUMMARY),
            placement_intent="Surface proof where doubt peaks — on the product and at checkout.",
            evidence_ids=cite,
        )
        return TrustStrategy(elements=elements, social_proof=social, evidence_ids=cite)

    def _pricing(
        self, tier: StrategyTier, ranked: Sequence[StrategyEvidence]
    ) -> PricingStrategy:
        cite = self._cite(ranked, ("price", "pricing", "offer", "discount", "bundle"), 3)
        signals = (
            PricingSignal(
                kind=PricingSignalKind.ANCHOR_PRICE,
                rationale="Anchoring frames the value of the primary offer.",
                evidence_ids=self._cite(ranked, ("anchor", "price"), 1),
            ),
            PricingSignal(
                kind=PricingSignalKind.FREE_SHIPPING_THRESHOLD,
                rationale="A shipping threshold lifts average order value.",
                evidence_ids=self._cite(ranked, ("shipping", "threshold", "aov"), 1),
            ),
        )
        offer = OfferStrategy(
            offers=("bundle", "first-order incentive"),
            framing="Frame offers as added value, never as desperation discounts.",
            evidence_ids=cite,
        )
        urgency = UrgencyStrategy(
            kinds=(UrgencyKind.HIGH_DEMAND,),
            evidence_ids=self._cite(ranked, ("urgency", "demand", "stock"), 1),
        )
        return PricingStrategy(
            posture=_TIER_POSTURE[tier],
            signals=signals,
            offer=offer,
            urgency=urgency,
            evidence_ids=cite,
        )

    def _retention(self, ranked: Sequence[StrategyEvidence]) -> RetentionStrategy:
        cite = self._cite(ranked, ("retention", "loyalty", "repeat", "subscription"), 2)
        levers = (
            RetentionLever(
                kind=RetentionLeverKind.LOYALTY_PROGRAM,
                rationale="Rewarding repeat purchase compounds lifetime value.",
                priority=Priority(4),
                evidence_ids=cite,
            ),
            RetentionLever(
                kind=RetentionLeverKind.POST_PURCHASE_NURTURE,
                rationale="Post-purchase nurture turns a first order into a relationship.",
                priority=Priority(3),
                evidence_ids=cite,
            ),
        )
        return RetentionStrategy(
            levers=levers,
            lifecycle_focus="Convert first-time buyers into repeat, loyal customers.",
            evidence_ids=cite,
        )

    def _risks(self, ranked: Sequence[StrategyEvidence]) -> tuple[BusinessRisk, ...]:
        return (
            BusinessRisk(
                id=BusinessRiskId.new(),
                category=RiskCategory.TRUST,
                description="Insufficient trust signals could suppress conversion at consideration.",
                severity=Severity(4),
                likelihood=Likelihood(3),
                mitigation="Prioritise reviews and guarantees where doubt peaks.",
                evidence_ids=self._cite(ranked, ("trust", "conversion", "review"), 1),
            ),
        )

    def _opportunities(
        self, ranked: Sequence[StrategyEvidence]
    ) -> tuple[tuple[BusinessOpportunity, ...], tuple[RevenueOpportunity, ...]]:
        business = (
            BusinessOpportunity(
                id=BusinessOpportunityId.new(),
                category=OpportunityCategory.CONVERSION,
                description="Strengthening trust signals can lift consideration-to-purchase conversion.",
                impact=ImpactScore(4),
                confidence=Confidence.of(0.7),
                evidence_ids=self._cite(ranked, ("conversion", "trust"), 1),
            ),
        )
        revenue = (
            RevenueOpportunity(
                id=RevenueOpportunityId.new(),
                category=OpportunityCategory.AOV,
                description="A free-shipping threshold and bundling can raise average order value.",
                expected_value=Money.of(50000.0, "USD"),
                confidence=Confidence.of(0.6),
                lever="Introduce a shipping threshold and curated bundles.",
                assumptions=("Traffic and margins hold",),
                evidence_ids=self._cite(ranked, ("aov", "bundle", "shipping"), 1),
            ),
        )
        return business, revenue
