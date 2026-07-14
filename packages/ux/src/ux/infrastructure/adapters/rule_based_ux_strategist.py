"""RuleBasedUXStrategist — the deterministic default implementation of the strategist.

This adapter implements :class:`UXSynthesisPort` with explicit, explainable heuristics
rather than an LLM: it derives the goals, mental model, per-page strategies, the seven
journeys, the flows, and the six strategies from a codification of NN/g / Baymard / Shopify
UX practice (the page specs) and the consolidated evidence, citing real evidence ids for
each decision. It is fully deterministic (same input + evidence ⇒ same draft),
dependency-free, and honest — it invents no facts; it *architects* the experience over the
evidence it is given and grounds each decision by citing it.

In production this port is swapped for a reasoning/LLM-backed strategist; the contract
(propose grounded content, citing only supplied evidence) is unchanged, so the engine's
integrity guarantees hold regardless of which brain is plugged in.
"""

from __future__ import annotations

from collections.abc import Sequence

from ux.application.contracts import UXDraft, UXInput
from ux.domain.context.context import UXBrief
from ux.domain.evidence.evidence import EvidenceGraph, UXEvidence
from ux.domain.flow.flow import Flow, FlowSet, FlowStep, FlowTransition
from ux.domain.goals.goal import BusinessGoal, GoalSet, UserGoal
from ux.domain.goals.mental_model import MentalModel
from ux.domain.journey.journey import JourneyStage, UXJourney
from ux.domain.journey.journeys import JourneyMap
from ux.domain.page.cta import CallToAction
from ux.domain.page.objective import PageObjective, SuccessMetric
from ux.domain.page.page_strategy import PageStrategy, PageStrategySet
from ux.domain.page.priority import (
    ContentItem,
    ContentPriority,
    InformationItem,
    InformationPriority,
)
from ux.domain.shared.ids import (
    BusinessGoalId,
    CallToActionId,
    PageStrategyId,
    SuccessMetricId,
    UserGoalId,
    UXEvidenceId,
)
from ux.domain.shared.value_objects import (
    CTAType,
    FlowKind,
    InformationLevel,
    InteractionPattern,
    JourneyKind,
    JourneyPhase,
    NavPattern,
    PageKind,
    Priority,
    Severity,
)
from ux.domain.strategy.strategies import (
    ContentStrategy,
    ErrorRecoveryStrategy,
    InteractionStrategy,
    NavigationStrategy,
    ProgressiveDisclosureStrategy,
    TrustStrategy,
    UXStrategies,
)
from ux.infrastructure.adapters.page_specs import spec_for

__all__ = ["RuleBasedUXStrategist"]


class RuleBasedUXStrategist:
    """A deterministic, evidence-grounded implementation of the UX-strategist port."""

    async def draft(self, ux_input: UXInput, evidence: EvidenceGraph) -> UXDraft:
        ranked = sorted(evidence, key=lambda e: e.confidence.value, reverse=True)
        brief = ux_input.brief
        return UXDraft(
            goals=self._goals(brief, ranked),
            mental_model=self._mental_model(ranked),
            pages=self._pages(brief, ranked),
            journeys=self._journeys(brief, ranked),
            flows=self._flows(ranked),
            strategies=self._strategies(brief, ranked),
        )

    # ------------------------------------------------------------------ #
    @staticmethod
    def _cite(
        ranked: Sequence[UXEvidence], keywords: Sequence[str], limit: int = 2
    ) -> tuple[UXEvidenceId, ...]:
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
    def _goals(self, brief: UXBrief, ranked: Sequence[UXEvidence]) -> GoalSet:
        return GoalSet.of(
            user_goals=(
                UserGoal(
                    id=UserGoalId.new(),
                    statement=f"Buy the right {brief.product_category} with confidence and minimal effort.",
                    is_primary=True, priority=Priority(5),
                    evidence_ids=self._cite(ranked, ("goal", "buy", "confidence", "customer"), 2),
                ),
                UserGoal(
                    id=UserGoalId.new(),
                    statement="Understand the value and trust the brand quickly.",
                    is_primary=False, priority=Priority(4),
                    evidence_ids=self._cite(ranked, ("value", "trust", "understand"), 1),
                ),
            ),
            business_goals=(
                BusinessGoal(
                    id=BusinessGoalId.new(), statement="Increase conversion and average order value.",
                    priority=Priority(5),
                    evidence_ids=self._cite(ranked, ("conversion", "revenue", "business", "aov"), 2),
                ),
            ),
        )

    def _mental_model(self, ranked: Sequence[UXEvidence]) -> MentalModel:
        return MentalModel(
            summary="Shoppers expect a familiar ecommerce flow: browse, evaluate on trust, and check out simply.",
            expectations=("navigation matches other stores", "reviews near the buy button",
                          "checkout is short and secure"),
            familiar_patterns=("faceted category filtering", "sticky add-to-cart", "progress-stepped checkout"),
            anti_patterns=("hidden costs at checkout", "forced account creation"),
            evidence_ids=self._cite(ranked, ("convention", "pattern", "expect", "navigation"), 2),
        )

    # ------------------------------------------------------------------ #
    def _pages(self, brief: UXBrief, ranked: Sequence[UXEvidence]) -> PageStrategySet:
        pages = []
        for page in brief.pages:
            spec = spec_for(page)
            cite = self._cite(ranked, (page.value, "page", "conversion", "trust"), 2)
            primary = CallToAction(
                id=CallToActionId.new(), type=CTAType.PRIMARY, action=spec.primary_action,
                label_intent=spec.primary_action, target=spec.primary_target, priority=Priority(5),
                evidence_ids=cite,
            )
            secondary = CallToAction(
                id=CallToActionId.new(), type=CTAType.SECONDARY, action=spec.secondary_action,
                label_intent=spec.secondary_action, priority=Priority(3), evidence_ids=cite,
            )
            metrics = tuple(
                SuccessMetric(id=SuccessMetricId.new(), kind=k, target="improve",
                              priority=Priority(5 - i if 5 - i >= 1 else 1), evidence_ids=cite)
                for i, k in enumerate(spec.metrics)
            )
            info = InformationPriority(
                items=tuple(
                    InformationItem(
                        label=c.value.replace("_", " "),
                        level=(InformationLevel.PRIMARY if i == 0
                               else InformationLevel.SECONDARY if i < 3
                               else InformationLevel.TERTIARY),
                    )
                    for i, c in enumerate(spec.content)
                ),
                evidence_ids=cite,
            )
            content = ContentPriority(
                items=tuple(ContentItem(content_type=c, rank=i + 1) for i, c in enumerate(spec.content)),
                evidence_ids=cite,
            )
            pages.append(
                PageStrategy(
                    id=PageStrategyId.new(), page=page,
                    objective=PageObjective(
                        statement=spec.objective, why_it_exists=spec.why_it_exists,
                        serves_user_goal="Buy with confidence and minimal effort.",
                        serves_business_goal="Increase conversion and AOV.", evidence_ids=cite,
                    ),
                    ctas=(primary, secondary), success_metrics=metrics,
                    information_priority=info, content_priority=content,
                    applicable_laws=spec.laws, evidence_ids=cite,
                )
            )
        return PageStrategySet.of(pages)

    # ------------------------------------------------------------------ #
    def _stage(
        self, phase: JourneyPhase, goal: str, ranked: Sequence[UXEvidence], *,
        task: str = "", emotion: str = "", friction: tuple[str, ...] = (),
        trust: tuple[str, ...] = (), exit_risk: int = 2, note: str = "", keywords=("journey",),
    ) -> JourneyStage:
        return JourneyStage(
            phase=phase, user_goal=goal, task=task, emotion=emotion, friction=friction,
            trust_needed=trust, exit_risk=Severity(exit_risk), note=note,
            evidence_ids=self._cite(ranked, keywords, 1),
        )

    def _journeys(self, brief: UXBrief, ranked: Sequence[UXEvidence]) -> JourneyMap:
        user = UXJourney.of(JourneyKind.USER, (
            self._stage(JourneyPhase.AWARENESS, "Discover a credible option", ranked,
                        emotion="curiosity", keywords=("awareness", "discover")),
            self._stage(JourneyPhase.CONSIDERATION, "Compare and build trust", ranked,
                        emotion="anxiety", friction=("hard to compare options",),
                        trust=("reviews",), exit_risk=3, keywords=("consideration", "trust")),
            self._stage(JourneyPhase.DECISION, "Commit with confidence", ranked,
                        emotion="confidence", trust=("guarantee",), exit_risk=3, keywords=("decision",)),
            self._stage(JourneyPhase.PURCHASE, "Complete the purchase", ranked,
                        emotion="relief", friction=("checkout effort",), exit_risk=4, keywords=("checkout", "purchase")),
            self._stage(JourneyPhase.POST_PURCHASE, "Feel good about the choice", ranked,
                        emotion="satisfaction", keywords=("post-purchase", "retention")),
        ))
        task = UXJourney.of(JourneyKind.TASK, (
            self._stage(JourneyPhase.CONSIDERATION, "Find the right product", ranked,
                        task="filter and scan", friction=("too many options",), exit_risk=2, keywords=("find", "filter")),
            self._stage(JourneyPhase.EVALUATION, "Evaluate the product", ranked,
                        task="read details and reviews", exit_risk=2, keywords=("evaluate", "review")),
            self._stage(JourneyPhase.PURCHASE, "Buy the product", ranked,
                        task="add to cart and checkout", friction=("form effort",), exit_risk=4, keywords=("cart", "checkout")),
        ))
        decision = UXJourney.of(JourneyKind.DECISION, (
            self._stage(JourneyPhase.CONSIDERATION, "Decide it is worth considering", ranked,
                        emotion="interest", exit_risk=2, keywords=("consideration",)),
            self._stage(JourneyPhase.EVALUATION, "Decide it fits and is trustworthy", ranked,
                        emotion="doubt", friction=("trust gap",), exit_risk=3, keywords=("trust", "evaluate")),
            self._stage(JourneyPhase.DECISION, "Decide to buy now", ranked,
                        emotion="confidence", exit_risk=3, keywords=("decision", "commit")),
        ))
        trust = UXJourney.of(JourneyKind.TRUST, (
            self._stage(JourneyPhase.CONSIDERATION, "Trust the brand is credible", ranked,
                        trust=("social proof", "ratings"), exit_risk=3, keywords=("trust", "proof")),
            self._stage(JourneyPhase.DECISION, "Trust the purchase is safe", ranked,
                        trust=("guarantee", "returns"), exit_risk=3, keywords=("guarantee", "return")),
            self._stage(JourneyPhase.PURCHASE, "Trust the checkout is secure", ranked,
                        trust=("secure checkout",), exit_risk=4, keywords=("secure", "checkout")),
        ))
        conversion = UXJourney.of(JourneyKind.CONVERSION, (
            self._stage(JourneyPhase.CONSIDERATION, "Move from browsing to intent", ranked,
                        friction=("weak value clarity",), exit_risk=3, keywords=("conversion", "value")),
            self._stage(JourneyPhase.DECISION, "Move from intent to add-to-cart", ranked,
                        friction=("decision friction",), exit_risk=3, keywords=("cta", "cart")),
            self._stage(JourneyPhase.PURCHASE, "Move from cart to completed order", ranked,
                        friction=("checkout friction", "cost shock"), exit_risk=4, keywords=("checkout", "cost")),
        ))
        mobile = UXJourney.of(JourneyKind.MOBILE, (
            self._stage(JourneyPhase.CONSIDERATION, "Browse comfortably on a small screen", ranked,
                        note="thumb reach; reduced attention", friction=("small tap targets",), exit_risk=3,
                        keywords=("mobile", "thumb")),
            self._stage(JourneyPhase.PURCHASE, "Check out quickly on mobile", ranked,
                        note="minimise typing; support wallets", friction=("mobile form effort",), exit_risk=4,
                        keywords=("mobile", "checkout")),
        ))
        accessibility = UXJourney.of(JourneyKind.ACCESSIBILITY, (
            self._stage(JourneyPhase.CONSIDERATION, "Perceive and operate content with assistive tech", ranked,
                        note="WCAG AA: contrast, semantics, focus order", exit_risk=2, keywords=("accessibility", "wcag")),
            self._stage(JourneyPhase.PURCHASE, "Complete checkout with keyboard and screen reader", ranked,
                        note="WCAG AA: labels, errors, focus management", exit_risk=3, keywords=("accessibility", "checkout")),
        ))
        return JourneyMap(
            user=user, task=task, decision=decision, trust=trust,
            conversion=conversion, mobile=mobile, accessibility=accessibility,
        )

    # ------------------------------------------------------------------ #
    def _flows(self, ranked: Sequence[UXEvidence]) -> FlowSet:
        cite = self._cite(ranked, ("flow", "checkout", "cart"), 1)
        user_flow = Flow.of(
            FlowKind.USER,
            (
                FlowStep(order=1, action="land and orient", page=PageKind.HOME, evidence_ids=cite),
                FlowStep(order=2, action="browse a category", page=PageKind.CATEGORY, evidence_ids=cite),
                FlowStep(order=3, action="evaluate a product", page=PageKind.PRODUCT, is_decision_point=True, evidence_ids=cite),
                FlowStep(order=4, action="review the cart", page=PageKind.CART, evidence_ids=cite),
                FlowStep(order=5, action="complete checkout", page=PageKind.CHECKOUT, evidence_ids=cite),
                FlowStep(order=6, action="confirm the order", page=PageKind.POST_PURCHASE, evidence_ids=cite),
            ),
            (
                FlowTransition(1, 2), FlowTransition(2, 3), FlowTransition(3, 4, "adds to cart"),
                FlowTransition(4, 5), FlowTransition(5, 6),
            ),
        )
        task_flow = Flow.of(
            FlowKind.TASK,
            (
                FlowStep(order=1, action="find the right product", page=PageKind.CATEGORY, is_decision_point=True, evidence_ids=cite),
                FlowStep(order=2, action="evaluate fit and trust", page=PageKind.PRODUCT, evidence_ids=cite),
                FlowStep(order=3, action="purchase", page=PageKind.CHECKOUT, evidence_ids=cite),
            ),
            (FlowTransition(1, 2), FlowTransition(2, 3, "confident to buy")),
        )
        return FlowSet.of((user_flow, task_flow))

    # ------------------------------------------------------------------ #
    def _strategies(self, brief: UXBrief, ranked: Sequence[UXEvidence]) -> UXStrategies:
        return UXStrategies(
            navigation=NavigationStrategy(
                pattern=NavPattern.FACETED,
                primary_nav=("shop", "categories", "search", "account", "cart"),
                wayfinding="Persistent header, breadcrumbs, and clear active states.",
                principles=("match ecommerce conventions (Jakob)", "keep primary paths one tap away"),
                evidence_ids=self._cite(ranked, ("navigation", "convention", "pattern"), 2),
            ),
            content=ContentStrategy(
                hierarchy_intent="Lead with value and trust; reveal detail progressively.",
                leads_with=("value proposition", "social proof", "clear pricing"),
                principles=("chunk information (Miller)", "clarity over completeness (Occam)"),
                evidence_ids=self._cite(ranked, ("content", "value", "clarity"), 2),
            ),
            interaction=InteractionStrategy(
                patterns=(
                    InteractionPattern.INLINE_VALIDATION, InteractionPattern.STICKY_ACTION,
                    InteractionPattern.PROGRESSIVE_DISCLOSURE, InteractionPattern.OPTIMISTIC_FEEDBACK,
                ),
                feedback_intent="Acknowledge every action immediately and honestly.",
                principles=("visibility of system status (Nielsen)", "large, reachable targets (Fitts)"),
                evidence_ids=self._cite(ranked, ("interaction", "feedback", "status"), 2),
            ),
            error_recovery=ErrorRecoveryStrategy(
                prevention=("inline validation before submit", "clear input constraints"),
                recovery=("plain-language error messages", "preserve entered data", "offer a clear next step"),
                principles=("prevent errors, then help recovery (Nielsen)",),
                evidence_ids=self._cite(ranked, ("error", "validation", "recovery"), 2),
            ),
            disclosure=ProgressiveDisclosureStrategy(
                reveal_first=("price", "primary CTA", "key value and trust"),
                reveal_on_demand=("full specifications", "shipping details", "policy detail"),
                principles=("keep the primary path clear (Tesler)", "don't hide decision-critical info"),
                evidence_ids=self._cite(ranked, ("disclosure", "detail", "reveal"), 2),
            ),
            trust=TrustStrategy(
                trust_moments=("consideration on the product page", "commitment at checkout"),
                signals=("verified reviews", "ratings summary", "guarantee", "secure-checkout reassurance"),
                principles=("place proof where doubt peaks", "reversibility reduces risk"),
                evidence_ids=self._cite(ranked, ("trust", "review", "guarantee", "secure"), 2),
            ),
        )
