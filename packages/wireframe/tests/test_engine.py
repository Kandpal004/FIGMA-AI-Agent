"""Behavioural tests for the wireframe engine — end-to-end through the in-memory facade."""

from __future__ import annotations

import pytest

from wireframe.application.commands import BuildWireframePlan
from wireframe.domain.shared.ids import WireframePlanId, WireframePlanLineageId
from wireframe.domain.shared.value_objects import ApprovalGate, GraphKind, PageType

pytestmark = pytest.mark.asyncio


async def _build(env_factory, request_factory, signals, **brief):
    env = env_factory(signals)
    view = await env.facade.plan(BuildWireframePlan(request=request_factory(**brief)))
    return env, view


async def test_plan_is_grounded_usable_and_scored(env_factory, request_factory, signals) -> None:
    _, view = await _build(env_factory, request_factory, signals)
    assert view.is_usable
    assert view.quality.grounding == 1.0
    assert view.quality.overall_score >= 90.0
    assert view.evidence_count > 0
    assert view.version == 1
    assert view.section_count > 0


async def test_default_pages_cover_the_storefront(env_factory, request_factory, signals) -> None:
    _, view = await _build(env_factory, request_factory, signals)
    page_types = {p["page_type"] for p in view.pages}
    assert {"homepage", "collection", "product", "cart", "checkout", "search", "account"} <= page_types


async def test_all_six_graphs_are_populated(env_factory, request_factory, signals) -> None:
    _, view = await _build(env_factory, request_factory, signals)
    assert set(view.graphs.keys()) == {g.value for g in GraphKind}
    for kind, g in view.graphs.items():
        assert g["nodes"], f"graph {kind} has no nodes"


async def test_execution_order_is_a_valid_topological_order(env_factory, request_factory, signals) -> None:
    env, view = await _build(env_factory, request_factory, signals)
    order = await env.facade.execution_order(WireframePlanId.from_string(view.plan_id))
    position = {row["id"]: row["execution_order"] for row in order}
    # Every dependency is built strictly before the section that depends on it.
    for row in order:
        for dep in row["dependencies"]:
            assert position[dep] < position[row["id"]]
    # Orders are unique and contiguous from 0.
    orders = sorted(row["execution_order"] for row in order)
    assert orders == list(range(len(orders)))


async def test_product_page_has_gallery_buybox_and_reviews(env_factory, request_factory, signals) -> None:
    env, view = await _build(env_factory, request_factory, signals)
    pdp = (await env.facade.page(WireframePlanId.from_string(view.plan_id), PageType.PRODUCT)).page
    types = {s["type"] for s in pdp["sections"]}
    assert {"product_gallery", "buy_box", "reviews", "trust"} <= types
    buy_box = next(s for s in pdp["sections"] if s["type"] == "buy_box")
    comps = {c["component"] for c in buy_box["required_components"]}
    assert "add_to_cart" in comps
    # High-stakes conversion section escalates approval.
    assert buy_box["approval_requirement"]["gate"] == ApprovalGate.DESIGN_DIRECTOR.value


async def test_checkout_requires_strategy_signoff(env_factory, request_factory, signals) -> None:
    env, view = await _build(env_factory, request_factory, signals)
    checkout = (await env.facade.page(WireframePlanId.from_string(view.plan_id), PageType.CHECKOUT)).page
    gates = {s["type"]: s["approval_requirement"]["gate"] for s in checkout["sections"]}
    assert gates["checkout_form"] == ApprovalGate.STRATEGY_SIGNOFF.value
    assert gates["payment"] == ApprovalGate.STRATEGY_SIGNOFF.value


async def test_every_required_section_is_execution_ready(env_factory, request_factory, signals) -> None:
    _, view = await _build(env_factory, request_factory, signals)
    for page in view.pages:
        for section in page["sections"]:
            if section["is_required"]:
                assert section["required_components"], section["type"]
                assert section["success_criteria"]
                assert section["review_checklist"]
                assert section["responsive_behaviour"]
                assert section["accessibility_requirements"]


async def test_approval_dependencies_mirror_section_dependencies(env_factory, request_factory, signals) -> None:
    env, view = await _build(env_factory, request_factory, signals)
    approval = (await env.facade.approval_plan(WireframePlanId.from_string(view.plan_id))).approval
    # Some approval requirement has an upstream dependency (mirrors section deps).
    assert any(r["depends_on"] for r in approval["requirements"])


async def test_optional_pages_appear_when_requested(env_factory, request_factory, signals) -> None:
    _, view = await _build(env_factory, request_factory, signals, has_blog=True, has_landing=True)
    page_types = {p["page_type"] for p in view.pages}
    assert {"blog", "landing"} <= page_types


async def test_rebuild_under_lineage_bumps_version(env_factory, request_factory, signals) -> None:
    env = env_factory(signals)
    v1 = await env.facade.plan(BuildWireframePlan(request=request_factory()))
    lineage = WireframePlanLineageId.from_string(v1.lineage_id)
    v2 = await env.facade.plan(BuildWireframePlan(request=request_factory(), lineage_id=lineage))
    assert v2.version == 2 and v2.lineage_id == v1.lineage_id
    history = await env.facade.history(lineage)
    assert [h.version for h in history] == [1, 2]


async def test_determinism_same_input_same_structure(env_factory, request_factory, signals) -> None:
    _, a = await _build(env_factory, request_factory, signals)
    _, b = await _build(env_factory, request_factory, signals)
    assert {p["page_type"] for p in a.pages} == {p["page_type"] for p in b.pages}
    assert a.quality.overall_score == b.quality.overall_score
    assert a.section_count == b.section_count


async def test_figma_plan_bundle_is_neutral_and_ordered(env_factory, request_factory, signals) -> None:
    env, view = await _build(env_factory, request_factory, signals)
    bundle = await env.facade.figma_plan_bundle(WireframePlanId.from_string(view.plan_id))
    assert bundle.pages
    # Sections come pre-ordered for build; the bundle carries the approval plan.
    first_page = bundle.pages[0]
    orders = [s["execution_order"] for s in first_page["sections"]]
    assert orders == sorted(orders)
    assert bundle.approval_plan["requirements"]
