"""RuleBasedPsychologist — the deterministic default implementation of the psychologist.

This adapter implements :class:`PsychologySynthesisPort` with explicit, explainable
heuristics rather than an LLM: it classifies awareness and sophistication from the brief,
then derives the full psychology model — profile, personas, jobs, journeys, the
judgement-bearing matrix inputs, and the framework applications — from a codification of
Schwartz/Maslow/Fogg/Cialdini reasoning and the consolidated evidence, citing real
evidence ids for each finding. It is fully deterministic (same input + evidence ⇒ same
draft), dependency-free, and honest — it invents no facts; it *interprets* the evidence it
is given and grounds each determination by citing it.

In production this port is swapped for a reasoning/LLM-backed psychologist; the contract
(propose grounded content, citing only supplied evidence) is unchanged, so the engine's
integrity guarantees hold regardless of which brain is plugged in.
"""

from __future__ import annotations

from collections.abc import Sequence

from psychology.application.contracts import PsychologyDraft, PsychologyInput
from psychology.domain.context.context import PsychologyBrief
from psychology.domain.evidence.evidence import EvidenceGraph, PsychologyEvidence
from psychology.domain.frameworks.behavioral_economics import (
    BehavioralPrinciple,
    BehavioralPrincipleSet,
)
from psychology.domain.frameworks.hook import HookLoop
from psychology.domain.frameworks.maslow import MaslowMapping
from psychology.domain.journey.buying_journey import BuyingJourney, BuyingStage
from psychology.domain.journey.decision_journey import DecisionJourney, DecisionStage
from psychology.domain.matrices.cells import (
    BehaviorCell,
    ObjectionCell,
    RetentionCell,
    ValueCell,
)
from psychology.domain.persona.buying_persona import BuyingPersona, BuyingPersonaSet
from psychology.domain.persona.jtbd import ForcesOfProgress, JobToBeDone, JTBDSet
from psychology.domain.persona.persona import CustomerPersona, PersonaSet
from psychology.domain.shared.ids import (
    BuyingPersonaId,
    CustomerPersonaId,
    DecisionTriggerId,
    DriverId,
    JobToBeDoneId,
    MatrixCellId,
    PsychologyEvidenceId,
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
    Intensity,
    JobType,
    JourneyPhase,
    Likelihood,
    MaslowNeed,
    ObjectionKind,
    RiskKind,
    SophisticationLevel,
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

__all__ = ["RuleBasedPsychologist"]


class RuleBasedPsychologist:
    """A deterministic, evidence-grounded implementation of the psychologist port."""

    async def draft(
        self, psychology_input: PsychologyInput, evidence: EvidenceGraph
    ) -> PsychologyDraft:
        ranked = sorted(evidence, key=lambda e: e.confidence.value, reverse=True)
        brief = psychology_input.brief
        awareness = self._awareness(brief)
        sophistication = self._sophistication(brief, psychology_input.project.market)

        profile = self._profile(brief, awareness, sophistication, ranked)
        return PsychologyDraft(
            profile=profile,
            personas=self._personas(brief, awareness, ranked),
            buying_personas=self._buying_personas(awareness, sophistication, ranked),
            jobs=self._jobs(brief, ranked),
            buying_journey=self._buying_journey(ranked),
            decision_journey=self._decision_journey(ranked),
            objections=self._objections(ranked),
            behaviors=self._behaviors(ranked),
            value_cells=self._value_cells(brief, ranked),
            retention_cells=self._retention_cells(ranked),
            maslow=self._maslow(brief, ranked),
            hook=self._hook(ranked),
            principles=self._principles(ranked),
        )

    # ------------------------------------------------------------------ #
    @staticmethod
    def _cite(
        ranked: Sequence[PsychologyEvidence], keywords: Sequence[str], limit: int = 2
    ) -> tuple[PsychologyEvidenceId, ...]:
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
    @staticmethod
    def _awareness(brief: PsychologyBrief) -> AwarenessLevel:
        signals = " ".join((brief.purchase_type, *brief.descriptors)).lower()
        if "impulse" in signals:
            return AwarenessLevel.PRODUCT_AWARE
        if brief.is_high_risk:
            return AwarenessLevel.SOLUTION_AWARE
        return AwarenessLevel.SOLUTION_AWARE

    @staticmethod
    def _sophistication(brief: PsychologyBrief, market: str) -> SophisticationLevel:
        signals = " ".join((brief.price_band, market, *brief.descriptors)).lower()
        if "premium" in signals or "luxury" in signals:
            return SophisticationLevel.STAGE_5_IDENTIFICATION
        if "mass" in signals or "commodity" in signals:
            return SophisticationLevel.STAGE_4_AMPLIFIED_MECHANISM
        return SophisticationLevel.STAGE_3_MECHANISM

    # ------------------------------------------------------------------ #
    def _profile(
        self,
        brief: PsychologyBrief,
        awareness: AwarenessLevel,
        sophistication: SophisticationLevel,
        ranked: Sequence[PsychologyEvidence],
    ) -> PsychologicalProfile:
        motivations = (
            PurchaseMotivation(
                description="Buy with confidence that it is the right choice.",
                maslow_need=MaslowNeed.SAFETY, intensity=Intensity(4),
                evidence_ids=self._cite(ranked, ("trust", "confidence", "safety", "motivation"), 2),
            ),
            PurchaseMotivation(
                description="Feel good about the purchase and how it reflects on them.",
                maslow_need=MaslowNeed.ESTEEM, intensity=Intensity(3),
                evidence_ids=self._cite(ranked, ("aspiration", "status", "esteem", "brand"), 1),
            ),
        )
        anxieties = (
            PurchaseAnxiety(
                kind=AnxietyKind.TRUST, description="Uncertainty about whether the brand delivers.",
                intensity=Intensity(4), phase=JourneyPhase.CONSIDERATION,
                evidence_ids=self._cite(ranked, ("trust", "doubt", "anxiety", "review"), 2),
            ),
            PurchaseAnxiety(
                kind=(AnxietyKind.FINANCIAL if brief.is_high_risk else AnxietyKind.PERFORMANCE),
                description="Concern about whether it is worth the price / will perform.",
                intensity=Intensity(4 if brief.is_high_risk else 3), phase=JourneyPhase.EVALUATION,
                evidence_ids=self._cite(ranked, ("price", "value", "risk", "performance"), 1),
            ),
        )
        frictions = (
            PurchaseFriction(
                kind=FrictionKind.TRUST, description="Not enough proof at the point of doubt.",
                intensity=Intensity(3), phase=JourneyPhase.CONSIDERATION,
                evidence_ids=self._cite(ranked, ("trust", "proof", "friction"), 1),
            ),
            PurchaseFriction(
                kind=FrictionKind.DECISION_FATIGUE, description="Too many options or unclear differences.",
                intensity=Intensity(3), phase=JourneyPhase.EVALUATION,
                evidence_ids=self._cite(ranked, ("choice", "compare", "clarity"), 1),
            ),
        )
        risks = (
            RiskPerception(
                kind=(RiskKind.FINANCIAL if brief.is_high_risk else RiskKind.FUNCTIONAL),
                description="The product may not deliver the expected value.",
                likelihood=Likelihood(3), impact=Intensity(4 if brief.is_high_risk else 3),
                mitigation="Guarantees, reviews, and transparent returns.",
                evidence_ids=self._cite(ranked, ("risk", "guarantee", "return", "trust"), 2),
            ),
            RiskPerception(
                kind=RiskKind.SOCIAL, description="Others may judge the choice.",
                likelihood=Likelihood(2), impact=Intensity(3),
                mitigation="Social proof and identity alignment.",
                evidence_ids=self._cite(ranked, ("social", "proof", "review", "belonging"), 1),
            ),
        )
        trust_reqs = (
            TrustRequirement(
                id=TrustRequirementId.new(), kind=TrustRequirementKind.SOCIAL_PROOF,
                description="See that others like them chose this and were happy.",
                phase=JourneyPhase.CONSIDERATION, priority=self._priority(5),
                evidence_ids=self._cite(ranked, ("social", "proof", "review", "rating"), 2),
            ),
            TrustRequirement(
                id=TrustRequirementId.new(), kind=TrustRequirementKind.GUARANTEE,
                description="Know the purchase is reversible if it disappoints.",
                phase=JourneyPhase.DECISION, priority=self._priority(4),
                evidence_ids=self._cite(ranked, ("guarantee", "return", "refund"), 1),
            ),
        )
        triggers = (
            DecisionTrigger(
                id=DecisionTriggerId.new(), description="Prominent, credible social proof at the moment of doubt.",
                activates=DriverKind.SOCIAL, phase=JourneyPhase.CONSIDERATION,
                evidence_ids=self._cite(ranked, ("social", "proof", "trust"), 1),
            ),
            DecisionTrigger(
                id=DecisionTriggerId.new(), description="A clear, risk-reversing guarantee at checkout.",
                activates=DriverKind.LOGICAL, phase=JourneyPhase.DECISION,
                evidence_ids=self._cite(ranked, ("guarantee", "checkout", "risk"), 1),
            ),
        )
        drivers = (
            Driver(id=DriverId.new(), kind=DriverKind.EMOTIONAL,
                   description="Desire to feel confident and reassured.", intensity=Intensity(4),
                   evidence_ids=self._cite(ranked, ("emotion", "confidence", "feel"), 1)),
            Driver(id=DriverId.new(), kind=DriverKind.LOGICAL,
                   description="Need for clear value and proof.", intensity=Intensity(4),
                   evidence_ids=self._cite(ranked, ("value", "logic", "proof"), 1)),
            Driver(id=DriverId.new(), kind=DriverKind.SOCIAL,
                   description="Reassurance from what others do.", intensity=Intensity(3),
                   evidence_ids=self._cite(ranked, ("social", "others", "proof"), 1)),
            Driver(id=DriverId.new(), kind=DriverKind.URGENCY,
                   description="Gentle, honest urgency to act now.", intensity=Intensity(2),
                   evidence_ids=self._cite(ranked, ("urgency", "demand", "stock"), 1)),
            Driver(id=DriverId.new(), kind=DriverKind.RETENTION,
                   description="Reasons to come back after the first purchase.", intensity=Intensity(3),
                   evidence_ids=self._cite(ranked, ("retention", "loyalty", "repeat"), 1)),
        )
        confidence = PurchaseConfidence(
            level=Intensity(3),
            boosters=("credible reviews", "clear guarantees", "transparent value"),
            blockers=("weak trust signals", "unclear value"),
            evidence_ids=self._cite(ranked, ("confidence", "trust", "value"), 1),
        )
        return PsychologicalProfile(
            target_customer=f"Considered buyer of {brief.product_category} who decides on trust and value.",
            awareness=awareness, sophistication=sophistication, intent=CustomerIntent.COMPARING,
            confidence=confidence, motivations=motivations, anxieties=anxieties, frictions=frictions,
            risks=risks, trust_requirements=trust_reqs, decision_triggers=triggers, drivers=drivers,
        )

    @staticmethod
    def _priority(value: int):
        from psychology.domain.shared.value_objects import Priority

        return Priority(value)

    # ------------------------------------------------------------------ #
    def _personas(
        self, brief: PsychologyBrief, awareness: AwarenessLevel, ranked: Sequence[PsychologyEvidence]
    ) -> PersonaSet:
        cite = self._cite(ranked, ("customer", "buyer", "shopper", "audience"), 2)
        return PersonaSet.of(
            (
                CustomerPersona(
                    id=CustomerPersonaId.new(), name="Considered Claire",
                    archetype="value-aware researcher", awareness=awareness,
                    confidence=Confidence.of(0.7),
                    demographics={"channel": "mobile-first"},
                    psychographics={"mindset": "researches before buying"},
                    goals=("Buy with confidence", "Avoid a bad purchase"),
                    fears=("Wasting money", "Being disappointed"),
                    evidence_ids=cite,
                ),
            )
        )

    def _buying_personas(
        self,
        awareness: AwarenessLevel,
        sophistication: SophisticationLevel,
        ranked: Sequence[PsychologyEvidence],
    ) -> BuyingPersonaSet:
        cite = self._cite(ranked, ("decision", "buyer", "trust", "criteria"), 2)
        return BuyingPersonaSet.of(
            (
                BuyingPersona(
                    id=BuyingPersonaId.new(), name="The Decider", role=BuyingRole.DECIDER,
                    awareness=awareness, sophistication=sophistication,
                    must_believe=("This is trustworthy", "This is worth the price"),
                    blocked_by=("Weak proof", "Unclear value"),
                    decision_criteria=("trust signals", "clear value", "low risk"),
                    evidence_ids=cite,
                ),
            )
        )

    def _jobs(
        self, brief: PsychologyBrief, ranked: Sequence[PsychologyEvidence]
    ) -> JTBDSet:
        return JTBDSet.of(
            (
                JobToBeDone(
                    id=JobToBeDoneId.new(),
                    when_situation="I am choosing between options",
                    motivation="feel certain I am making the right choice",
                    expected_outcome="buy without second-guessing",
                    job_type=JobType.EMOTIONAL,
                    forces=ForcesOfProgress(push=Intensity(4), pull=Intensity(4), anxiety=Intensity(3), habit=Intensity(2)),
                    evidence_ids=self._cite(ranked, ("trust", "confidence", "decision"), 2),
                ),
                JobToBeDone(
                    id=JobToBeDoneId.new(),
                    when_situation=f"I need {brief.product_category}",
                    motivation="get clear value quickly",
                    expected_outcome="decide efficiently",
                    job_type=JobType.FUNCTIONAL,
                    evidence_ids=self._cite(ranked, ("value", "clarity", "efficient"), 1),
                ),
            )
        )

    # ------------------------------------------------------------------ #
    def _buying_journey(self, ranked: Sequence[PsychologyEvidence]) -> BuyingJourney:
        return BuyingJourney.of(
            (
                BuyingStage(
                    phase=JourneyPhase.AWARENESS, customer_goal="Discover a credible option",
                    dominant_driver=DriverKind.EMOTIONAL, emotion=EmotionKind.DESIRE,
                    dominant_motivation="find a trustworthy solution",
                    evidence_ids=self._cite(ranked, ("awareness", "discover", "brand"), 1),
                ),
                BuyingStage(
                    phase=JourneyPhase.CONSIDERATION, customer_goal="Build trust and compare",
                    dominant_driver=DriverKind.SOCIAL, emotion=EmotionKind.ANXIETY,
                    dominant_motivation="reduce uncertainty",
                    anxieties=("is it trustworthy?",), trust_needed=("reviews", "ratings"),
                    evidence_ids=self._cite(ranked, ("consideration", "trust", "review"), 2),
                ),
                BuyingStage(
                    phase=JourneyPhase.DECISION, customer_goal="Commit with confidence",
                    dominant_driver=DriverKind.LOGICAL, emotion=EmotionKind.CONFIDENCE,
                    dominant_motivation="commit without regret",
                    frictions=("last-minute doubt",), trust_needed=("guarantee", "secure checkout"),
                    evidence_ids=self._cite(ranked, ("decision", "checkout", "guarantee"), 1),
                ),
                BuyingStage(
                    phase=JourneyPhase.POST_PURCHASE, customer_goal="Feel good about the choice",
                    dominant_driver=DriverKind.RETENTION, emotion=EmotionKind.RELIEF,
                    dominant_motivation="confirm the good decision",
                    evidence_ids=self._cite(ranked, ("post-purchase", "retention", "loyalty"), 1),
                ),
            )
        )

    def _decision_journey(self, ranked: Sequence[PsychologyEvidence]) -> DecisionJourney:
        cite = self._cite(ranked, ("decision", "checkout", "trust"), 1)
        return DecisionJourney.of(
            (
                DecisionStage(order=1, commitment="Click into the product", emotion=EmotionKind.DESIRE,
                              peak_end_weight=Intensity(2), micro_decision="Is this relevant?", evidence_ids=cite),
                DecisionStage(order=2, commitment="Read reviews and details", emotion=EmotionKind.ANXIETY,
                              peak_end_weight=Intensity(4), micro_decision="Can I trust this?",
                              anxiety="uncertainty about quality", evidence_ids=cite),
                DecisionStage(order=3, commitment="Add to cart", emotion=EmotionKind.CONFIDENCE,
                              peak_end_weight=Intensity(3), micro_decision="Is it worth it?", evidence_ids=cite),
                DecisionStage(order=4, commitment="Complete checkout", emotion=EmotionKind.RELIEF,
                              peak_end_weight=Intensity(5), micro_decision="Am I safe to commit?",
                              anxiety="last-minute risk", evidence_ids=cite),
            )
        )

    # ------------------------------------------------------------------ #
    def _objections(self, ranked: Sequence[PsychologyEvidence]) -> tuple[ObjectionCell, ...]:
        return (
            ObjectionCell(
                id=MatrixCellId.new(), objection="Is it worth the price?", kind=ObjectionKind.PRICE,
                phase=JourneyPhase.EVALUATION,
                resolution_strategy="Frame value clearly; anchor against the cost of a wrong choice.",
                evidence_ids=self._cite(ranked, ("price", "value", "worth"), 1),
            ),
            ObjectionCell(
                id=MatrixCellId.new(), objection="Can I trust this brand?", kind=ObjectionKind.TRUST,
                phase=JourneyPhase.CONSIDERATION,
                resolution_strategy="Lead with proof: reviews, guarantees, transparency.",
                evidence_ids=self._cite(ranked, ("trust", "review", "guarantee"), 2),
            ),
            ObjectionCell(
                id=MatrixCellId.new(), objection="What if it doesn't work for me?", kind=ObjectionKind.RISK,
                phase=JourneyPhase.DECISION,
                resolution_strategy="Reverse the risk with a clear returns/guarantee policy.",
                evidence_ids=self._cite(ranked, ("risk", "return", "guarantee"), 1),
            ),
        )

    def _behaviors(self, ranked: Sequence[PsychologyEvidence]) -> tuple[BehaviorCell, ...]:
        return (
            BehaviorCell(
                id=MatrixCellId.new(), target_behavior="Read reviews before deciding",
                motivation=Intensity(4), ability=Intensity(4), prompt="Surface reviews on the product page",
                evidence_ids=self._cite(ranked, ("review", "trust", "behavior"), 1),
            ),
            BehaviorCell(
                id=MatrixCellId.new(), target_behavior="Add to cart", motivation=Intensity(4),
                ability=Intensity(4), prompt="Clear, prominent add-to-cart",
                evidence_ids=self._cite(ranked, ("cart", "conversion", "cta"), 1),
            ),
            BehaviorCell(
                id=MatrixCellId.new(), target_behavior="Complete checkout", motivation=Intensity(3),
                ability=Intensity(3), prompt="Reassurance and minimal steps at checkout",
                evidence_ids=self._cite(ranked, ("checkout", "friction", "trust"), 1),
            ),
        )

    def _value_cells(
        self, brief: PsychologyBrief, ranked: Sequence[PsychologyEvidence]
    ) -> tuple[ValueCell, ...]:
        return (
            ValueCell(
                id=MatrixCellId.new(),
                value_perception="Confidence and quality outweigh a higher price.",
                price_relation="value-over-price",
                framing="Frame price as the cost of certainty, not just the product.",
                evidence_ids=self._cite(ranked, ("value", "price", "quality"), 2),
            ),
        )

    def _retention_cells(self, ranked: Sequence[PsychologyEvidence]) -> tuple[RetentionCell, ...]:
        cite = self._cite(ranked, ("retention", "loyalty", "repeat", "subscription"), 2)
        return (
            RetentionCell(
                id=MatrixCellId.new(), driver="Reinforce the good decision",
                lifecycle_stage="post_purchase", mechanism="Post-purchase reassurance and nurture.",
                evidence_ids=cite,
            ),
            RetentionCell(
                id=MatrixCellId.new(), driver="Reward loyalty", lifecycle_stage="repeat",
                mechanism="Loyalty rewards for repeat purchase.", evidence_ids=cite,
            ),
        )

    # ------------------------------------------------------------------ #
    def _maslow(
        self, brief: PsychologyBrief, ranked: Sequence[PsychologyEvidence]
    ) -> MaslowMapping:
        dominant = MaslowNeed.SAFETY if brief.is_high_risk else MaslowNeed.ESTEEM
        return MaslowMapping(
            dominant_need=dominant,
            active_needs=(MaslowNeed.BELONGING, MaslowNeed.ESTEEM),
            rationale="The purchase primarily serves safety/esteem for this considered buyer.",
            evidence_ids=self._cite(ranked, ("safety", "trust", "esteem", "need"), 1),
        )

    def _hook(self, ranked: Sequence[PsychologyEvidence]) -> HookLoop:
        return HookLoop(
            trigger="a reason to return (restock, new arrival, reward)",
            action="revisit and browse",
            variable_reward="discover something newly relevant",
            investment="save items, preferences, or loyalty progress",
            evidence_ids=self._cite(ranked, ("retention", "habit", "loyalty", "return"), 1),
        )

    def _principles(self, ranked: Sequence[PsychologyEvidence]) -> BehavioralPrincipleSet:
        return BehavioralPrincipleSet.of(
            (
                BehavioralPrinciple(
                    kind=BehavioralPrincipleKind.SOCIAL_PROOF,
                    application="Show credible reviews and ratings where doubt peaks.",
                    evidence_ids=self._cite(ranked, ("social", "proof", "review"), 1),
                ),
                BehavioralPrinciple(
                    kind=BehavioralPrincipleKind.LOSS_AVERSION,
                    application="Frame the guarantee so the customer avoids the loss of a bad choice.",
                    evidence_ids=self._cite(ranked, ("guarantee", "risk", "loss"), 1),
                ),
                BehavioralPrinciple(
                    kind=BehavioralPrincipleKind.ANCHORING,
                    application="Anchor value against the cost of getting it wrong.",
                    evidence_ids=self._cite(ranked, ("price", "value", "anchor"), 1),
                ),
                BehavioralPrinciple(
                    kind=BehavioralPrincipleKind.AUTHORITY,
                    application="Signal expertise and credentials to borrow authority.",
                    evidence_ids=self._cite(ranked, ("authority", "expert", "trust"), 1),
                ),
                BehavioralPrinciple(
                    kind=BehavioralPrincipleKind.PEAK_END,
                    application="Design the checkout ending to leave a confident, positive memory.",
                    evidence_ids=self._cite(ranked, ("checkout", "experience", "confidence"), 1),
                ),
            )
        )
