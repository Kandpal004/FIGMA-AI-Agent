"""Tests for the Homepage Design Plan output model (section_plan.py)."""

from __future__ import annotations

import json

import pytest

from homepage_workflow.section_plan import (
    APPROVAL_SCORE_THRESHOLD,
    FIGMA_CONSTRAINTS,
    HOMEPAGE_SECTIONS,
    ApprovalStatus,
    HomepageDesignPlan,
    InvalidSectionPlanError,
    SectionDesignPlan,
    SectionRole,
    section_spec,
)


# --------------------------------------------------------------------------- #
# Taxonomy                                                                     #
# --------------------------------------------------------------------------- #
def test_taxonomy_is_the_fourteen_sections_in_order():
    keys = [s.key for s in HOMEPAGE_SECTIONS]
    assert keys == [
        "announcement_bar", "header", "hero", "trust_bar", "usp", "featured_collections",
        "featured_products", "category_grid", "social_proof", "testimonials", "reviews", "faq",
        "newsletter", "footer",
    ]
    assert len(set(keys)) == 14  # unique
    # every section maps to a component and a role
    for spec in HOMEPAGE_SECTIONS:
        assert spec.component and isinstance(spec.role, SectionRole)


def test_section_spec_lookup():
    assert section_spec("hero").component == "hero"
    assert section_spec("trust_bar").component == "trust_badges"
    with pytest.raises(InvalidSectionPlanError):
        section_spec("nope")


# --------------------------------------------------------------------------- #
# Figma constraints                                                            #
# --------------------------------------------------------------------------- #
def test_figma_constraints_are_all_enforced():
    c = FIGMA_CONSTRAINTS
    assert all([
        c.auto_layout_only, c.variables_only, c.components_only, c.variants_only,
        c.no_absolute_positioning, c.no_unnecessary_layers, c.no_raster_text, c.reusable_components,
    ])
    rules = c.rules()
    assert len(rules) == 8
    doc = c.to_json()
    assert doc["auto_layout_only"] is True and len(doc["rules"]) == 8


# --------------------------------------------------------------------------- #
# Section design plan                                                          #
# --------------------------------------------------------------------------- #
def _plan(section_key="hero", order=1, score=0.0, status=ApprovalStatus.PENDING) -> SectionDesignPlan:
    spec = section_spec(section_key)
    return SectionDesignPlan(
        section_key=spec.key, title=spec.title, component=spec.component, order=order,
        role=spec.role,
        purpose="Communicate the brand promise above the fold.",
        business_goal="Establish premium positioning and drive first click.",
        customer_goal="Understand what the brand offers and why it matters.",
        conversion_goal="Move the visitor to the primary CTA.",
        required_components=("hero", "button"),
        required_assets=("hero image", "brand logo"),
        content_requirements=("headline", "subhead", "primary CTA label"),
        cta_strategy="One high-contrast primary CTA; no competing actions.",
        trust_strategy="Lead with a confident value proposition; defer proof to the trust bar.",
        responsive_behaviour={"mobile": "stacked, full-width", "desktop": "two column"},
        accessibility_requirements=("WCAG AA contrast", "visible focus", "semantic heading"),
        animation_guidance="Subtle fade-and-rise on load; respect reduced-motion.",
        review_checklist=("Value proposition clear?", "Single primary CTA?", "Contrast AA?"),
        reasoning="Grounded in the conversion and psychology engines: clarity then trust.",
        design_intent="A confident, editorial hero that states the promise in one line.",
        dependencies=("header",),
        review_score=score,
        approval_status=status,
        evidence_refs=("ds-1", "ci-1"),
    )


def test_section_plan_carries_the_thirteen_attributes_and_serialises():
    plan = _plan()
    doc = plan.to_json()
    for attribute in (
        "purpose", "business_goal", "customer_goal", "conversion_goal", "required_components",
        "required_assets", "content_requirements", "cta_strategy", "trust_strategy",
        "responsive_behaviour", "accessibility_requirements", "animation_guidance",
        "review_checklist",
    ):
        assert attribute in doc, attribute
    # envelope
    for field in ("reasoning", "design_intent", "dependencies", "review_score", "approval_status",
                  "figma_constraints"):
        assert field in doc
    # round-trips through json
    assert json.loads(json.dumps(doc))["section_key"] == "hero"


def test_section_plan_rejects_empty_required_fields():
    with pytest.raises(InvalidSectionPlanError):
        SectionDesignPlan(
            section_key="hero", title="Hero", component="hero", order=1, role=SectionRole.HERO,
            purpose="", business_goal="b", customer_goal="c", conversion_goal="d",
            required_components=(), required_assets=(), content_requirements=(),
            cta_strategy="e", trust_strategy="f", responsive_behaviour={}, animation_guidance="g",
            accessibility_requirements=(), review_checklist=(), reasoning="h", design_intent="i",
        )


def test_section_plan_review_score_bounds():
    with pytest.raises(InvalidSectionPlanError):
        _plan(score=101.0)


def test_with_review_sets_score_and_status():
    approved = _plan().with_review(96.0, ApprovalStatus.APPROVED)
    assert approved.review_score == 96.0 and approved.is_approved
    assert APPROVAL_SCORE_THRESHOLD == 95.0


# --------------------------------------------------------------------------- #
# Homepage design plan                                                         #
# --------------------------------------------------------------------------- #
def test_homepage_plan_aggregates_sections_and_reports_readiness():
    s1 = _plan("hero", order=2, score=96.0, status=ApprovalStatus.APPROVED)
    s2 = _plan("header", order=1, score=98.0, status=ApprovalStatus.APPROVED)
    plan = HomepageDesignPlan(
        brand_name="Aesop", project_id="proj-x", sections=(s1, s2),
        source_refs={"design_system": "ds-1"}, created_at="2026-07-15T12:00:00Z",
    )
    # sorted by order
    assert [s.section_key for s in plan] == ["header", "hero"]
    assert plan.all_approved and plan.ready_for_figma
    assert plan.overall_score == 97.0
    doc = plan.to_json()
    assert doc["ready_for_figma"] is True and doc["section_count"] == 2
    assert doc["sections"][0]["section_key"] == "header"
    # pretty string is valid json
    assert json.loads(plan.to_json_str())["brand_name"] == "Aesop"


def test_homepage_plan_not_ready_until_all_approved():
    approved = _plan("hero", order=1, score=96.0, status=ApprovalStatus.APPROVED)
    improving = _plan("header", order=2, score=80.0, status=ApprovalStatus.IMPROVING)
    plan = HomepageDesignPlan(brand_name="Aesop", project_id="p", sections=(approved, improving))
    assert not plan.ready_for_figma


def test_homepage_plan_rejects_duplicate_orders():
    with pytest.raises(InvalidSectionPlanError):
        HomepageDesignPlan(
            brand_name="Aesop", project_id="p",
            sections=(_plan("hero", order=1), _plan("header", order=1)),
        )
