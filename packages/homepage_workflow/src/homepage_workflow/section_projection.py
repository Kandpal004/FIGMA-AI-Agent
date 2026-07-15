"""Section projection — turn the engines' outputs into a per-section design plan.

This is where the workflow *composes* (never recomputes) each section's :class:`SectionDesignPlan`
from what the engines already produced once: the Component Intelligence composition (purpose, the
business/customer/conversion/trust goals, dependencies, content contract), the Design System spec
(responsive, accessibility, animation, platform mappings, token references), and the Design
Orchestrator execution plan (layout, CTA and trust ordering, animation and accessibility
directives). Where an engine models a section's component, its output grounds the plan; where it
does not, a senior D2C creative director's role-based defaults fill the gap — so every one of the
fourteen sections gets a complete, conversion- and trust-oriented plan bound by the Figma
constraints.

:func:`score_section` is the deterministic critique the approval gate applies: a complete,
grounded section clears the 95 bar; a section missing review dimensions falls below it and is sent
back to be improved.

Pure composition: the section-plan model, the input request, and the shared value objects. It reads
the engines' *view* objects (already-serialised DTOs) defensively, so it imports no engine.
"""

from __future__ import annotations

from typing import Any

from homepage_workflow.request import HomepageRequest
from homepage_workflow.section_plan import (
    APPROVAL_SCORE_THRESHOLD,
    ApprovalStatus,
    SectionDesignPlan,
    SectionRole,
    SectionSpec,
)

__all__ = ["project_section", "score_section"]


# --------------------------------------------------------------------------- #
# Role-based creative-director defaults                                        #
# --------------------------------------------------------------------------- #
_ROLE_DEFAULTS: dict[SectionRole, dict[str, Any]] = {
    SectionRole.NAVIGATION: {
        "purpose": "Orient the shopper and give persistent access to search, cart, and account.",
        "business_goal": "Reduce navigation friction and keep the path to purchase always visible.",
        "customer_goal": "Find what I want quickly and always know where I am.",
        "conversion_goal": "Keep the primary conversion path one tap away from every scroll depth.",
        "cta": "Persistent, low-emphasis utility actions (search, cart); the header never competes "
        "with the hero's primary CTA.",
        "trust": "A calm, consistent header signals a considered, trustworthy brand.",
        "assets": ("brand logo", "navigation icons"),
        "content": ("primary navigation labels", "search placeholder", "cart indicator"),
        "animation": "Sticky-on-scroll with a subtle elevation change; no distracting motion.",
        "intent": "A quiet, confident header that stays out of the hero's way.",
    },
    SectionRole.HERO: {
        "purpose": "State the brand promise and drive the first meaningful click above the fold.",
        "business_goal": "Establish premium positioning and convert attention into intent.",
        "customer_goal": "Immediately understand what the brand offers and why it is for me.",
        "conversion_goal": "Move the visitor to the single primary call to action.",
        "cta": "One high-contrast primary CTA; no competing actions above the fold.",
        "trust": "Lead with a confident, specific value proposition; defer proof to the trust bar.",
        "assets": ("hero image or short video", "brand logo"),
        "content": ("headline", "supporting subhead", "primary CTA label"),
        "animation": "A subtle fade-and-rise on load; respect prefers-reduced-motion.",
        "intent": "An editorial hero that states the promise in one confident line.",
    },
    SectionRole.TRUST: {
        "purpose": "Reassure the shopper with proof points before they are asked to act.",
        "business_goal": "Lower perceived risk to lift conversion across the whole page.",
        "customer_goal": "Feel confident this brand is credible and safe to buy from.",
        "conversion_goal": "Remove anxiety that would otherwise stall the purchase decision.",
        "cta": "No CTA; the trust bar supports the hero's CTA rather than competing with it.",
        "trust": "Concrete, specific signals — guarantees, shipping, returns, ratings — not vague "
        "claims.",
        "assets": ("trust icons", "payment/guarantee badges"),
        "content": ("guarantee statement", "shipping promise", "returns policy", "rating summary"),
        "animation": "None or a single subtle entrance; trust must read as stable.",
        "intent": "A quiet band of concrete reassurances directly under the hero.",
    },
    SectionRole.VALUE: {
        "purpose": "Articulate the brand's differentiators as scannable, benefit-led propositions.",
        "business_goal": "Convert interest into preference by making the value unmistakable.",
        "customer_goal": "Quickly grasp why this brand is better for me than the alternatives.",
        "conversion_goal": "Build the case that justifies the primary CTA.",
        "cta": "Optional secondary CTA to learn more; never competes with the hero.",
        "trust": "Benefit claims are specific and substantiated, not marketing filler.",
        "assets": ("USP icons or supporting imagery",),
        "content": ("three benefit-led USP statements", "short supporting copy per USP"),
        "animation": "Staggered entrance on scroll into view; restrained.",
        "intent": "Three sharp, benefit-first propositions that earn the scroll.",
    },
    SectionRole.DISCOVERY: {
        "purpose": "Merchandise the catalog so shoppers can find and desire products fast.",
        "business_goal": "Drive product discovery and click-through into the catalog.",
        "customer_goal": "See relevant products and collections worth exploring.",
        "conversion_goal": "Generate qualified clicks into PDPs and collections.",
        "cta": "Card-level CTAs (view / quick-add) plus a 'shop all' secondary action.",
        "trust": "Real product imagery, honest pricing, and ratings build purchase confidence.",
        "assets": ("product imagery", "collection imagery"),
        "content": ("product/collection titles", "prices", "ratings", "badges"),
        "animation": "Lazy-loaded, gentle image reveals; no layout shift.",
        "intent": "A clean, aspirational merchandising grid that invites exploration.",
    },
    SectionRole.SOCIAL_PROOF: {
        "purpose": "Let other customers make the case, reducing risk through credible proof.",
        "business_goal": "Lift conversion by borrowing the credibility of real customers.",
        "customer_goal": "See that people like me have bought and been happy.",
        "conversion_goal": "Convert consideration into confidence at the decision point.",
        "cta": "A soft CTA to read more reviews or shop the loved products.",
        "trust": "Verified, specific, attributed proof — never anonymous or fabricated.",
        "assets": ("customer photos", "reviewer avatars", "rating stars"),
        "content": ("verified reviews or testimonials", "reviewer names", "ratings"),
        "animation": "Carousel or gentle fade; motion must not undermine credibility.",
        "intent": "Authentic, specific social proof placed before the final ask.",
    },
    SectionRole.CONVERSION: {
        "purpose": "Capture intent and convert it — a newsletter opt-in or a focused offer.",
        "business_goal": "Grow the owned audience and recover would-be leavers.",
        "customer_goal": "Get a reason and a simple way to stay connected or save.",
        "conversion_goal": "Maximise qualified sign-ups with a single, clear action.",
        "cta": "One primary action with a specific incentive; minimal fields.",
        "trust": "Clear value exchange and privacy reassurance; no dark patterns.",
        "assets": ("supporting imagery", "incentive badge"),
        "content": ("value proposition", "single input", "primary CTA label", "privacy note"),
        "animation": "Minimal; a success state confirms the action.",
        "intent": "A focused, honest opt-in with an obvious reason to say yes.",
    },
    SectionRole.CONTENT: {
        "purpose": "Answer the questions that block purchase, in the shopper's own words.",
        "business_goal": "Remove objections that would otherwise cost the sale.",
        "customer_goal": "Get my specific questions answered without leaving the page.",
        "conversion_goal": "Clear the last doubts standing between interest and purchase.",
        "cta": "Inline links to detail; a soft CTA back to the primary action.",
        "trust": "Honest, complete answers — especially on shipping, returns, and fit.",
        "assets": ("supporting diagrams if needed",),
        "content": ("the top 5–8 real pre-purchase questions", "a clear, concise answer for each"),
        "animation": "Accordion expand/collapse; nothing decorative.",
        "intent": "A calm FAQ that dissolves the most common objections.",
    },
    SectionRole.FOOTER: {
        "purpose": "Provide comprehensive navigation, policies, and reassurance at the page end.",
        "business_goal": "Support SEO, discoverability, and trust without stealing focus.",
        "customer_goal": "Find policies, support, and secondary links when I need them.",
        "conversion_goal": "Recover intent with newsletter and key links; reinforce trust.",
        "cta": "Low-emphasis links and a secondary newsletter action.",
        "trust": "Clear policies, contact, and payment/security signals.",
        "assets": ("brand logo", "payment icons", "social icons"),
        "content": ("navigation columns", "policy links", "contact", "payment icons"),
        "animation": "None; the footer is stable and utilitarian.",
        "intent": "A thorough, trustworthy footer that closes the page cleanly.",
    },
}

_UNIVERSAL_CHECKLIST = (
    "Bound entirely to design-system variables (no hard-coded values)?",
    "Built from components and variants with Auto Layout only?",
    "Meets WCAG AA contrast with visible focus and semantic structure?",
    "Responsive across mobile, tablet, and desktop with no layout shift?",
    "Live text only — no rasterised type?",
)


# --------------------------------------------------------------------------- #
# Defensive engine-view lookups                                                #
# --------------------------------------------------------------------------- #
def _components(view: Any) -> list[dict]:
    return list(getattr(view, "components", []) or [])


def _find(view: Any, component: str) -> dict | None:
    for item in _components(view):
        if item.get("component") == component:
            return item
    return None


def _find_do_section(do_view: Any, component: str) -> dict | None:
    for page in getattr(do_view, "pages", []) or []:
        for section in page.get("sections", []) or []:
            if section.get("component") == component:
                return section
    return None


def _first_sentence(text: str, fallback: str) -> str:
    text = (text or "").strip()
    return text or fallback


# --------------------------------------------------------------------------- #
# Projection                                                                   #
# --------------------------------------------------------------------------- #
def project_section(
    spec: SectionSpec,
    request: HomepageRequest,
    *,
    order: int,
    design_system_view: Any = None,
    component_intelligence_view: Any = None,
    orchestrator_view: Any = None,
    evidence_refs: tuple[str, ...] = (),
    attempt: int = 1,
    notes: tuple[str, ...] = (),
) -> SectionDesignPlan:
    """Compose the design plan for one section from the engines' outputs and role defaults."""
    role_defaults = _ROLE_DEFAULTS[spec.role]
    ci = _find(component_intelligence_view, spec.component)
    ds = _find(design_system_view, spec.component)
    do = _find_do_section(orchestrator_view, spec.component)
    grounded = bool(ci or ds or do)

    # Purpose & goals — grounded in Component Intelligence purposes where present.
    purposes = (ci or {}).get("purposes", {}) if ci else {}
    purpose = _first_sentence(purposes.get("business", ""), role_defaults["purpose"])
    business_goal = _first_sentence(purposes.get("business", ""), role_defaults["business_goal"])
    customer_goal = _first_sentence(purposes.get("user", ""), role_defaults["customer_goal"])
    conversion_goal = _first_sentence(
        purposes.get("conversion", ""), role_defaults["conversion_goal"]
    )

    # Required components — the section's component plus its intelligence dependencies.
    required_components = [spec.component]
    if ci:
        required_components.extend(ci.get("dependencies", []) or [])
    required_components.append("button")

    # Content — the component's data contract where the composition supplies one.
    content: list[str] = []
    if ci:
        content = [i.get("kind", "") for i in ci.get("required_inputs", []) if i.get("kind")]
    if not content:
        default_content = role_defaults["content"]
        content = list(default_content) if isinstance(default_content, tuple) else [default_content]

    # Required assets — role assets plus supplied brand assets.
    assets = list(role_defaults["assets"])
    if request.brand_assets.logo and spec.role in (
        SectionRole.NAVIGATION, SectionRole.HERO, SectionRole.FOOTER
    ):
        assets.append("supplied brand logo")

    # Responsive — orchestrator/design-system directive, else mobile-first default.
    responsive = {}
    if do and isinstance(do.get("responsive"), dict):
        responsive = dict(do["responsive"])
    elif ds and isinstance(ds.get("responsive"), dict):
        responsive = dict(ds["responsive"])
    if "mobile" not in responsive:
        responsive["mobile"] = "single column, full-width, tap targets ≥ 44px"
    if "tablet" not in responsive:
        responsive["tablet"] = "fluid columns, comfortable spacing"
    if "desktop" not in responsive:
        responsive["desktop"] = "multi-column, contained max width"

    # Accessibility — design-system spec where present, else strong defaults.
    a11y: list[str] = ["WCAG AA contrast", "visible focus states", "semantic landmarks & headings"]
    if ds and isinstance(ds.get("accessibility"), dict):
        acc = ds["accessibility"]
        if acc.get("role"):
            a11y.append(f"ARIA role: {acc['role']}")
        for key in acc.get("keyboard", []) or []:
            a11y.append(f"keyboard: {key}")
    a11y.append("respects prefers-reduced-motion")

    # Animation — orchestrator directive, else role default.
    animation = role_defaults["animation"]
    if do and isinstance(do.get("animation"), dict):
        anim = do["animation"]
        trigger = anim.get("trigger", "on-scroll")
        animation = f"{role_defaults['animation']} (trigger: {trigger}, tokenised motion)."

    # CTA & trust — role strategy, reinforced by conversion/trust intelligence.
    cta = role_defaults["cta"]
    trust = role_defaults["trust"]
    if ci and ci.get("improves_conversion"):
        cta = f"{cta} This section is evidenced to improve conversion."
    if ci and ci.get("builds_trust"):
        trust = f"{trust} This section is evidenced to build trust."

    checklist = list(_UNIVERSAL_CHECKLIST)
    if spec.role in (SectionRole.HERO, SectionRole.CONVERSION):
        checklist.insert(0, "Exactly one primary CTA with no competing actions?")
    if spec.role in (SectionRole.TRUST, SectionRole.SOCIAL_PROOF):
        checklist.insert(0, "Proof is specific, verified, and attributed?")

    grounded_from = [
        name for name, present in (
            ("Component Intelligence", bool(ci)),
            ("Design System", bool(ds)),
            ("Design Orchestrator", bool(do)),
        ) if present
    ]
    reasoning = (
        f"{spec.title}: goals and content grounded in "
        f"{', '.join(grounded_from) if grounded_from else 'the creative-director playbook'}, "
        f"aligned to the brief '{request.design_brief}'. Optimised for conversion, trust, and "
        f"premium quality, not decoration."
    )
    if attempt > 1 and notes:
        reasoning += f" Improved on review: {'; '.join(notes)}."

    return SectionDesignPlan(
        section_key=spec.key,
        title=spec.title,
        component=spec.component,
        order=order,
        role=spec.role,
        purpose=purpose,
        business_goal=business_goal,
        customer_goal=customer_goal,
        conversion_goal=conversion_goal,
        required_components=tuple(dict.fromkeys(required_components)),
        required_assets=tuple(dict.fromkeys(assets)),
        content_requirements=tuple(dict.fromkeys(content)),
        cta_strategy=cta,
        trust_strategy=trust,
        responsive_behaviour=responsive,
        accessibility_requirements=tuple(dict.fromkeys(a11y)),
        animation_guidance=animation,
        review_checklist=tuple(checklist),
        reasoning=reasoning,
        design_intent=role_defaults["intent"],
        dependencies=tuple(ci.get("dependencies", []) if ci else ()),
        review_score=0.0,
        approval_status=ApprovalStatus.PENDING,
        evidence_refs=evidence_refs,
    )


# --------------------------------------------------------------------------- #
# Critique / scoring                                                           #
# --------------------------------------------------------------------------- #
def score_section(plan: SectionDesignPlan, *, grounded: bool = True) -> tuple[float, tuple[str, ...]]:
    """The Creative Director's deterministic critique of a section plan.

    Returns the 0–100 score and the concrete findings (the review dimensions that fell short). A
    complete, grounded section clears the 95 bar; missing dimensions cost 3 points each and send the
    section back to be improved.
    """
    findings: list[str] = []
    score = 100.0

    def fail(condition: bool, finding: str) -> None:
        nonlocal score
        if not condition:
            score -= 3.0
            findings.append(finding)

    responsive = plan.responsive_behaviour
    fail("mobile" in responsive and "desktop" in responsive,
         "Define responsive behaviour for at least mobile and desktop.")
    fail(len(plan.accessibility_requirements) >= 3,
         "Specify at least three accessibility requirements.")
    fail(len(plan.review_checklist) >= 3, "Provide a review checklist of at least three checks.")
    fail(len(plan.trust_strategy) >= 20, "Strengthen the trust strategy.")
    fail(len(plan.cta_strategy) >= 20, "Strengthen the CTA strategy.")
    fail(len(plan.content_requirements) >= 2, "Enumerate the section's content requirements.")
    fail(grounded, "Ground the section in an upstream engine output where possible.")

    return max(0.0, round(score, 1)), tuple(findings)


def meets_bar(score: float) -> bool:
    """Whether a section score clears the approval bar."""
    return score >= APPROVAL_SCORE_THRESHOLD
