"""Tests for the per-section Homepage workflow definition and catalog (pure config)."""

from __future__ import annotations

from core.contracts.agent import AgentRole

from director.domain.shared.value_objects import PageType, WorkflowType
from homepage_workflow import definition as wf
from homepage_workflow.section_plan import HOMEPAGE_SECTIONS


def test_definition_starts_with_validate_and_runs_strategy_once():
    d = wf.build_homepage_definition()
    assert d.workflow_type is WorkflowType.PAGE
    assert d.page_type is PageType.HOMEPAGE
    assert d.first_step.key == wf.STEP_VALIDATE_INPUTS
    # the strategy pipeline appears exactly once (page-level), before section work
    keys = d.step_keys()
    assert keys.index(wf.STEP_RESEARCH) < keys.index(wf.STEP_GENERATE_HOMEPAGE_PLAN)
    assert keys.count(wf.STEP_RESEARCH) == 1
    assert keys.count(wf.STEP_DESIGN_SYSTEM_MAPPING) == 1


def test_one_generate_and_approve_gate_per_section():
    d = wf.build_homepage_definition()
    gen = [s.key for s in d.steps if wf.is_generate_step(s.key)]
    app = [s.key for s in d.steps if wf.is_approve_step(s.key)]
    assert len(gen) == 14 and len(app) == 14
    # in taxonomy order, generate immediately precedes its approve gate
    for spec in HOMEPAGE_SECTIONS:
        g, a = wf.generate_step_key(spec.key), wf.approve_step_key(spec.key)
        assert d.next_step(g).key == a
        # the approve gate rewinds ONLY to its own generate — approved sections are never touched
        assert d.resolve_rollback(a).key == g


def test_section_approve_gates_are_automatic_and_final_is_manual():
    d = wf.build_homepage_definition()
    hero_gate = d.get_step(wf.approve_step_key("hero"))
    assert hero_gate.is_gate and not hero_gate.approval.requires_human  # score-gated, automatic
    final = d.get_step(wf.STEP_FINAL_APPROVAL)
    assert final.is_gate and final.approval.requires_human  # human sign-off
    assert d.resolve_rollback(final.key).key == wf.STEP_FINALIZE


def test_creative_director_review_gate_rewinds_to_ux():
    d = wf.build_homepage_definition()
    assert d.get_step(wf.STEP_CD_REVIEW).agent_role is AgentRole.CREATIVE_DIRECTOR
    assert d.resolve_rollback(wf.STEP_CD_REVIEW).key == wf.STEP_UX_STRATEGY


def test_catalog_resolves_the_homepage_page_workflow():
    catalog = wf.build_homepage_catalog()
    resolved = catalog.for_page(PageType.HOMEPAGE)
    assert resolved.key == wf.HOMEPAGE_WORKFLOW_KEY
    # validate + 12 strategy + generate_plan + 14x2 sections + finalize + final_approval
    assert len(resolved) == 1 + 12 + 1 + 28 + 1 + 1 == 44
