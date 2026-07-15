"""Behavioural tests for the component-intelligence engine — end-to-end through the facade."""

from __future__ import annotations

import pytest

from component_intelligence.application.commands import BuildComposition
from component_intelligence.domain.shared.ids import ComponentSpecId, ComponentSpecLineageId
from component_intelligence.domain.shared.value_objects import ComponentType, GraphKind, PageType

pytestmark = pytest.mark.asyncio


async def _compose(env_factory, request_factory, signals, **brief):
    env = env_factory(signals)
    view = await env.facade.compose(BuildComposition(request=request_factory(**brief)))
    return env, view


async def test_produces_a_production_ready_composition(env_factory, request_factory, signals) -> None:
    _, v = await _compose(env_factory, request_factory, signals)
    assert v.is_production_ready
    assert v.quality.grounding == 1.0
    assert v.quality.overall_score >= 90.0
    assert v.included_count > 0
    assert v.evidence_count > 0
    assert v.version == 1


async def test_both_graphs_are_populated(env_factory, request_factory, signals) -> None:
    _, v = await _compose(env_factory, request_factory, signals)
    assert set(v.graphs.keys()) == {g.value for g in GraphKind}
    for kind, g in v.graphs.items():
        assert g["nodes"], f"graph {kind} has no nodes"


async def test_every_included_component_is_fully_specified(env_factory, request_factory, signals) -> None:
    _, v = await _compose(env_factory, request_factory, signals)
    for decision in v.components:
        if decision["inclusion"] == "included":
            assert decision["purposes"]["business"]
            assert decision["usage"]["when_to_use"] and decision["usage"]["when_not_to_use"]
            assert decision["responsive_rules"] and decision["interaction_rules"]
            assert decision["required_inputs"] and decision["expected_outputs"]
            assert decision["success_criteria"] and decision["failure_criteria"]
            assert decision["variants"] and decision["states"]


async def test_conflicting_components_are_resolved(env_factory, request_factory, signals) -> None:
    """Mini Cart and Cart Drawer conflict — exactly one survives, never both."""
    _, v = await _compose(env_factory, request_factory, signals)
    included = {d["component"] for d in v.components if d["inclusion"] == "included"}
    assert not ({"mini_cart", "cart_drawer"} <= included)
    assert not ({"hero", "hero_carousel"} <= included)
    # And the conflict is recorded in the compatibility web.
    conflict_pairs = {frozenset((c["source"], c["target"])) for c in v.compatibility["conflicts"]}
    assert frozenset(("cart_drawer", "mini_cart")) in conflict_pairs


async def test_dependencies_are_closed(env_factory, request_factory, signals) -> None:
    _, v = await _compose(env_factory, request_factory, signals)
    included = {d["component"] for d in v.components if d["inclusion"] == "included"}
    for decision in v.components:
        if decision["inclusion"] == "included":
            for dep in decision["dependencies"]:
                assert dep in included, f"{decision['component']} depends on excluded {dep}"


async def test_page_components_are_placed_in_order(env_factory, request_factory, signals) -> None:
    env, v = await _compose(env_factory, request_factory, signals)
    sid = ComponentSpecId.from_string(v.spec_id)
    product = await env.facade.page_components(sid, PageType.PRODUCT)
    assert product
    components = [r["component"] for r in product]
    assert "product_gallery" in components and "header" in components
    # No two conflicting components share the page.
    assert not ({"mini_cart", "cart_drawer"} <= set(components))


async def test_why_surfaces_when_and_when_not(env_factory, request_factory, signals) -> None:
    env, v = await _compose(env_factory, request_factory, signals)
    sid = ComponentSpecId.from_string(v.spec_id)
    why = await env.facade.why(sid, ComponentType.STICKY_ADD_TO_CART)
    assert why["impacts"]["conversion_effect"] == "strong"
    assert why["when_to_use"] and why["when_not_to_use"]


async def test_conversion_and_trust_intelligence(env_factory, request_factory, signals) -> None:
    _, v = await _compose(env_factory, request_factory, signals)
    by_component = {d["component"]: d for d in v.components}
    assert by_component["trust_badges"]["impacts"]["trust_effect"] == "strong"
    assert by_component["variant_picker"]["impacts"]["conversion_effect"] == "strong"
    assert by_component["filters"]["impacts"]["friction_effect"] == "strong"


async def test_determinism(env_factory, request_factory, signals) -> None:
    _, a = await _compose(env_factory, request_factory, signals)
    _, b = await _compose(env_factory, request_factory, signals)
    incl_a = {d["component"] for d in a.components if d["inclusion"] == "included"}
    incl_b = {d["component"] for d in b.components if d["inclusion"] == "included"}
    assert incl_a == incl_b
    assert a.quality.overall_score == b.quality.overall_score


async def test_design_system_bundle_is_neutral(env_factory, request_factory, signals) -> None:
    env, v = await _compose(env_factory, request_factory, signals)
    bundle = await env.facade.design_system_bundle(ComponentSpecId.from_string(v.spec_id))
    assert bundle.components and bundle.placement_rules
    assert bundle.is_production_ready
    # Carries variants and token refs for the downstream design system.
    assert all("variants" in c and "design_token_refs" in c for c in bundle.components)


async def test_rebuild_under_lineage_bumps_version(env_factory, request_factory, signals) -> None:
    env = env_factory(signals)
    v1 = await env.facade.compose(BuildComposition(request=request_factory()))
    lineage = ComponentSpecLineageId.from_string(v1.lineage_id)
    v2 = await env.facade.compose(BuildComposition(request=request_factory(), lineage_id=lineage))
    assert v2.version == 2
    history = await env.facade.history(lineage)
    assert [h.version for h in history] == [1, 2]
