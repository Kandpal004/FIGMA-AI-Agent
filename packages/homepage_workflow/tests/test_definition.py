"""Tests for the Homepage workflow definition and catalog (pure config)."""

from __future__ import annotations

from core.contracts.agent import AgentRole

from director.domain.shared.value_objects import PageType, WorkflowType
from homepage_workflow import definition as wf


def test_definition_is_the_v1_pipeline_in_order():
    d = wf.build_homepage_definition()
    assert d.workflow_type is WorkflowType.PAGE
    assert d.page_type is PageType.HOMEPAGE
    assert d.step_keys() == (
        wf.STEP_RESEARCH,
        wf.STEP_COMPETITOR_ANALYSIS,
        wf.STEP_BUSINESS_STRATEGY,
        wf.STEP_BRAND_STRATEGY,
        wf.STEP_CUSTOMER_PSYCHOLOGY,
        wf.STEP_UX_STRATEGY,
        wf.STEP_INFORMATION_ARCHITECTURE,
        wf.STEP_WIREFRAME_PLANNING,
        wf.STEP_CD_REVIEW,
        wf.STEP_DESIGN_LANGUAGE,
        wf.STEP_COMPONENT_INTELLIGENCE,
        wf.STEP_DESIGN_SYSTEM_MAPPING,
        wf.STEP_FIGMA_GENERATION,
        wf.STEP_DESIGN_CRITIQUE,
        wf.STEP_SELF_IMPROVEMENT,
        wf.STEP_FINAL_APPROVAL,
    )


def test_the_two_gates_rewind_correctly():
    d = wf.build_homepage_definition()
    gate_keys = {g.key for g in d.gates()}
    assert gate_keys == {wf.STEP_CD_REVIEW, wf.STEP_FINAL_APPROVAL}
    # the wireframe review rewinds to UX; the final approval rewinds to self-improvement
    assert d.resolve_rollback(wf.STEP_CD_REVIEW).key == wf.STEP_UX_STRATEGY
    assert d.resolve_rollback(wf.STEP_FINAL_APPROVAL).key == wf.STEP_SELF_IMPROVEMENT


def test_final_approval_is_a_manual_gate():
    d = wf.build_homepage_definition()
    final = d.get_step(wf.STEP_FINAL_APPROVAL)
    assert final.is_gate and final.approval.requires_human
    cd = d.get_step(wf.STEP_CD_REVIEW)
    assert cd.is_gate and not cd.approval.requires_human  # automatic


def test_review_steps_use_the_creative_director_role():
    d = wf.build_homepage_definition()
    assert d.get_step(wf.STEP_CD_REVIEW).agent_role is AgentRole.CREATIVE_DIRECTOR
    assert d.get_step(wf.STEP_DESIGN_CRITIQUE).agent_role is AgentRole.CREATIVE_DIRECTOR
    assert d.get_step(wf.STEP_FINAL_APPROVAL).agent_role is AgentRole.CREATIVE_DIRECTOR


def test_catalog_resolves_the_homepage_page_workflow():
    catalog = wf.build_homepage_catalog()
    resolved = catalog.for_page(PageType.HOMEPAGE)
    assert resolved.key == wf.HOMEPAGE_WORKFLOW_KEY
    assert len(resolved) == 16
