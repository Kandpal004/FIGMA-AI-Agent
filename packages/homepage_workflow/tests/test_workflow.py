"""End-to-end tests: the per-section Homepage Design Workflow over the REAL engines.

These prove the workflow validates inputs, orchestrates every engine once, then designs the
homepage **one section at a time** — generating, critiquing (score-gated at 95), approving, and
never regenerating an approved section — and finally assembles a complete, Figma-ready
:class:`HomepageDesignPlan` with the thirteen creative-director attributes per section.
"""

from __future__ import annotations

import pytest

from director.domain.director.decision import DecisionKind
from director.domain.shared.ids import RunId

from homepage_workflow import definition as wf
from homepage_workflow.request import HomepageRequest, ProductCatalog
from homepage_workflow.section_plan import HOMEPAGE_SECTIONS


@pytest.fixture
def full_brief() -> dict[str, object]:
    return HomepageRequest(
        brand_name="Aesop",
        business_description="Premium botanical skincare for discerning customers.",
        product_catalog=ProductCatalog(product_category="skincare", categories=("serums",)),
        design_brief="A calm, editorial homepage that converts through trust and clarity.",
        descriptors=("premium", "minimal"),
    ).to_brief()


async def test_designs_the_homepage_section_by_section(homepage_env, runner, full_brief):
    result = await runner.start(full_brief)
    run = result.run
    # every engine + section step ran; only the manual final approval remains
    assert run.status == "paused"
    assert run.current_step_key == wf.STEP_FINAL_APPROVAL
    completed = {s.key for s in run.steps if s.state == "completed"}
    assert wf.STEP_VALIDATE_INPUTS in completed
    assert wf.STEP_GENERATE_HOMEPAGE_PLAN in completed
    for spec in HOMEPAGE_SECTIONS:  # every section generated and approved
        assert wf.generate_step_key(spec.key) in completed
        assert wf.approve_step_key(spec.key) in completed

    run_id = RunId.from_string(run.run_id)

    # each section was approved individually with a score at or above the 95 bar
    for spec in HOMEPAGE_SECTIONS:
        plan = runner.section_plan(run_id, spec.key)
        assert plan is not None and plan.is_approved
        assert plan.review_score >= 95.0
        # the thirteen creative-director attributes are all present
        assert plan.purpose and plan.business_goal and plan.customer_goal and plan.conversion_goal
        assert plan.required_components and plan.required_assets and plan.content_requirements
        assert plan.cta_strategy and plan.trust_strategy and plan.animation_guidance
        assert plan.responsive_behaviour and plan.accessibility_requirements and plan.review_checklist
        # bound by the Figma rules
        assert plan.figma_constraints.auto_layout_only and plan.figma_constraints.variables_only

    # sign off the finished plan → the run completes
    approved = await runner.approve_final(run_id)
    assert approved.run.status == "completed"

    # the assembled homepage plan is complete and ready for Figma generation
    homepage = runner.homepage_plan(run_id)
    assert homepage is not None
    assert len(homepage) == 14
    assert [s.section_key for s in homepage] == [s.key for s in HOMEPAGE_SECTIONS]
    assert homepage.all_approved and homepage.ready_for_figma
    assert homepage.overall_score >= 95.0
    doc = homepage.to_json()
    assert doc["ready_for_figma"] is True and doc["section_count"] == 14

    # reasoning and per-section review results were stored
    reasoning = await runner.reasoning(run_id)
    assert len(reasoning) >= len(run.steps)
    reviews = await runner.review_results(run_id)
    assert sum(1 for d in reviews if d.kind is DecisionKind.APPROVE) >= 14  # 14 sections + final


async def test_validate_inputs_blocks_on_missing_required_inputs(runner):
    # a request missing the business description and catalog
    incomplete = HomepageRequest(brand_name="Aesop", design_brief="Convert.").to_brief()
    result = await runner.start(incomplete)
    run = result.run
    # the run blocks at Validate Inputs rather than running the engines
    assert run.current_step_key == wf.STEP_VALIDATE_INPUTS
    validate_step = next(s for s in run.steps if s.key == wf.STEP_VALIDATE_INPUTS)
    assert validate_step.state == "blocked"
    assert all(
        s.state != "completed" for s in run.steps if s.key != wf.STEP_VALIDATE_INPUTS
    )


async def test_never_regenerates_approved_sections(runner, full_brief):
    # each section's approve gate rewinds only to its own generate step, so approving a section
    # can never rewind into an already-approved earlier section.
    d = wf.build_homepage_definition()
    prev_approved: list[str] = []
    for spec in HOMEPAGE_SECTIONS:
        target = d.resolve_rollback(wf.approve_step_key(spec.key)).key
        assert target == wf.generate_step_key(spec.key)
        assert target not in prev_approved  # never rewinds into a prior section
        prev_approved.append(wf.generate_step_key(spec.key))


async def test_pipeline_shape_is_deterministic(runner, full_brief):
    r1 = await runner.start(full_brief)
    completed = [s.key for s in r1.run.steps if s.state == "completed"]
    expected = [k for k in wf.build_homepage_definition().step_keys() if k != wf.STEP_FINAL_APPROVAL]
    assert completed == expected
