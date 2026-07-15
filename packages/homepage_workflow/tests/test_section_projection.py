"""Tests for the section projection and the score-gated critique (section_projection.py)."""

from __future__ import annotations

import dataclasses

from homepage_workflow.request import HomepageRequest, ProductCatalog
from homepage_workflow.section_plan import HOMEPAGE_SECTIONS, ApprovalStatus
from homepage_workflow.section_projection import (
    meets_bar,
    project_section,
    score_section,
)


def _request() -> HomepageRequest:
    return HomepageRequest(
        brand_name="Aesop", business_description="Premium skincare.",
        product_catalog=ProductCatalog(product_category="skincare"),
        design_brief="Convert through trust and clarity.",
    )


class _View:
    """A minimal stand-in for an engine view carrying a components list."""

    def __init__(self, components):
        self.components = components


def test_every_section_projects_a_complete_plan_even_without_engine_data():
    req = _request()
    for order, spec in enumerate(HOMEPAGE_SECTIONS, start=1):
        plan = project_section(spec, req, order=order, evidence_refs=("ds-1",))
        # all thirteen attributes are populated
        assert plan.purpose and plan.business_goal and plan.customer_goal and plan.conversion_goal
        assert plan.required_components and plan.required_assets and plan.content_requirements
        assert plan.cta_strategy and plan.trust_strategy and plan.animation_guidance
        assert "mobile" in plan.responsive_behaviour and "desktop" in plan.responsive_behaviour
        assert len(plan.accessibility_requirements) >= 3 and len(plan.review_checklist) >= 3
        assert plan.approval_status is ApprovalStatus.PENDING
        # a complete section clears the bar even when ungrounded
        score, _ = score_section(plan, grounded=False)
        assert meets_bar(score), (spec.key, score)


def test_engine_data_grounds_the_plan():
    req = _request()
    hero = next(s for s in HOMEPAGE_SECTIONS if s.key == "hero")
    ci_view = _View([{
        "component": "hero",
        "purposes": {"business": "Own the first impression.", "user": "Understand the brand.",
                     "conversion": "Drive the first click.", "trust": "Signal quality."},
        "dependencies": ["header"], "required_inputs": [{"kind": "headline"}, {"kind": "image"}],
        "improves_conversion": True, "builds_trust": True,
    }])
    plan = project_section(hero, req, order=3, component_intelligence_view=ci_view)
    assert plan.business_goal == "Own the first impression."
    assert plan.customer_goal == "Understand the brand."
    assert "header" in plan.dependencies
    assert "headline" in plan.content_requirements
    score, findings = score_section(plan, grounded=True)
    assert score == 100.0 and not findings


def test_incomplete_plan_falls_below_the_bar_and_reports_findings():
    req = _request()
    hero = next(s for s in HOMEPAGE_SECTIONS if s.key == "hero")
    plan = project_section(hero, req, order=3)
    # strip two review dimensions
    broken = dataclasses.replace(
        plan, responsive_behaviour={"mobile": "x"}, accessibility_requirements=("only one",)
    )
    score, findings = score_section(broken, grounded=False)
    assert not meets_bar(score)
    assert any("responsive" in f.lower() for f in findings)
    assert any("accessibility" in f.lower() for f in findings)


def test_improvement_notes_are_carried_into_reasoning():
    req = _request()
    hero = next(s for s in HOMEPAGE_SECTIONS if s.key == "hero")
    improved = project_section(hero, req, order=3, attempt=2, notes=("Increase hero contrast.",))
    assert "Improved on review" in improved.reasoning
    assert "Increase hero contrast." in improved.reasoning
