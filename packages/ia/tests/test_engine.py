"""Behavioural tests for the IA engine — end-to-end through the in-memory facade."""

from __future__ import annotations

import pytest

from ia.application.commands import BuildIA
from ia.domain.shared.ids import IAReportId, IAReportLineageId
from ia.domain.shared.value_objects import GraphKind, PageType

pytestmark = pytest.mark.asyncio


async def _build(env_factory, request_factory, signals, **brief):
    env = env_factory(signals)
    view = await env.facade.build(BuildIA(request=request_factory(**brief)))
    return env, view


async def test_build_produces_grounded_usable_ia(env_factory, request_factory, signals) -> None:
    _, view = await _build(env_factory, request_factory, signals)
    assert view.is_usable
    assert view.quality.grounding == 1.0
    assert view.quality.overall_score >= 90.0
    assert view.evidence_count > 0
    assert view.version == 1


async def test_default_sitemap_covers_the_storefront_pages(env_factory, request_factory, signals) -> None:
    _, view = await _build(env_factory, request_factory, signals)
    required = {p["page_type"] for p in view.required_pages}
    assert {"homepage", "collection", "product", "cart", "checkout", "search", "account"} <= required


async def test_all_six_graphs_are_populated(env_factory, request_factory, signals) -> None:
    _, view = await _build(env_factory, request_factory, signals)
    assert set(view.graphs.keys()) == {g.value for g in GraphKind}
    for kind, g in view.graphs.items():
        assert g["nodes"], f"graph {kind} has no nodes"


async def test_product_page_leads_with_add_to_cart(env_factory, request_factory, signals) -> None:
    env, view = await _build(env_factory, request_factory, signals)
    pdp = (await env.facade.page(IAReportId.from_string(view.report_id), PageType.PRODUCT)).page
    assert pdp["required_sections"]
    primary = pdp["primary_actions"]
    assert primary, "PDP must define a primary action"
    assert any("cart" in a["action"].lower() for a in primary)


async def test_product_relationships_include_cross_sell_and_related(env_factory, request_factory, signals) -> None:
    env, view = await _build(env_factory, request_factory, signals)
    rels = await env.facade.relationships(IAReportId.from_string(view.report_id))
    kinds = {r["kind"] for r in rels}
    assert "cross_sell" in kinds or "related" in kinds
    # every relationship endpoint resolves to a page in the site map (structural integrity)
    present = view.required_pages + view.optional_pages
    page_types = {p["page_type"] for p in present}
    for r in rels:
        assert r["source"] in page_types and r["target"] in page_types


async def test_large_catalog_enables_faceted_discovery(env_factory, request_factory, signals) -> None:
    env, view = await _build(env_factory, request_factory, signals, catalog_scale="large")
    discovery = await env.facade.discovery(IAReportId.from_string(view.report_id))
    assert discovery["filtering"]["facets"]


async def test_optional_pages_appear_when_requested(env_factory, request_factory, signals) -> None:
    _, view = await _build(env_factory, request_factory, signals, has_blog=True, has_wishlist=True)
    optional = {p["page_type"] for p in view.optional_pages}
    assert {"blog", "wishlist"} & optional


async def test_rebuild_under_lineage_bumps_version(env_factory, request_factory, signals) -> None:
    env = env_factory(signals)
    v1 = await env.facade.build(BuildIA(request=request_factory()))
    lineage = IAReportLineageId.from_string(v1.lineage_id)
    v2 = await env.facade.build(BuildIA(request=request_factory(), lineage_id=lineage))
    assert v2.version == 2
    assert v2.lineage_id == v1.lineage_id
    history = await env.facade.history(lineage)
    assert [h.version for h in history] == [1, 2]


async def test_determinism_same_input_same_structure(env_factory, request_factory, signals) -> None:
    _, a = await _build(env_factory, request_factory, signals)
    _, b = await _build(env_factory, request_factory, signals)
    assert {p["page_type"] for p in a.required_pages} == {p["page_type"] for p in b.required_pages}
    assert a.quality.overall_score == b.quality.overall_score


async def test_wireframe_brief_bundle_is_required_first(env_factory, request_factory, signals) -> None:
    env, view = await _build(env_factory, request_factory, signals)
    bundle = await env.facade.wireframe_brief_bundle(IAReportId.from_string(view.report_id))
    assert bundle.pages
    # the neutral hand-off downstream wireframing consumes
    assert bundle.navigation is not None
