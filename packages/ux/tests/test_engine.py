"""Engine tests — the UX strategy pipeline end to end, over in-memory persistence."""

from __future__ import annotations

import pytest

from ux.application.commands import BuildUXStrategy
from ux.domain.shared.ids import UXNodeId, UXReportId, UXReportLineageId
from ux.domain.shared.value_objects import GraphKind, PageKind, ProvenanceKind

from .conftest import signal


@pytest.mark.asyncio
async def test_pipeline_produces_grounded_usable_strategy(env_factory, request_factory, signals):
    env = env_factory(signals)
    view = await env.facade.build(BuildUXStrategy(request=request_factory()))

    assert view.is_usable
    assert view.quality.grounding == 1.0  # everything is evidence-backed
    assert view.quality.coverage == 1.0
    assert view.quality.heuristic_validation == 1.0  # all eleven UX laws applied
    assert view.primary_user_goal
    assert len(view.pages) == 5  # default storefront page set


@pytest.mark.asyncio
async def test_all_journeys_laws_and_graphs_are_built(env_factory, request_factory, signals):
    env = env_factory(signals)
    view = await env.facade.build(BuildUXStrategy(request=request_factory()))
    # All seven journeys present and populated.
    for name in ("user", "task", "decision", "trust", "conversion", "mobile", "accessibility"):
        assert view.journeys[name]["stages"], f"{name} journey is empty"
    # All eleven laws applied, and all cited.
    assert len(view.laws) == 11
    assert all(a["evidence_ids"] for a in view.laws)
    # All five graphs present and populated.
    for name in ("decision", "navigation", "content_hierarchy", "trust_hierarchy", "interaction"):
        assert view.graphs[name]["nodes"], f"{name} graph is empty"
    # Friction and drop-off derived from the journeys.
    assert view.friction and view.dropoff


@pytest.mark.asyncio
async def test_pages_define_why_and_ctas(env_factory, request_factory, signals):
    env = env_factory(signals)
    view = await env.facade.build(BuildUXStrategy(request=request_factory()))
    checkout = next(p for p in view.pages if p["page"] == "checkout")
    assert checkout["why_it_exists"]
    assert checkout["primary_cta"] == "complete purchase"
    assert "wcag" in checkout["applicable_laws"]  # checkout must honour WCAG


@pytest.mark.asyncio
async def test_custom_page_set_is_honoured(env_factory, request_factory, signals):
    env = env_factory(signals)
    view = await env.facade.build(
        BuildUXStrategy(request=request_factory(pages=(PageKind.PRODUCT, PageKind.CHECKOUT)))
    )
    assert {p["page"] for p in view.pages} == {"product", "checkout"}


@pytest.mark.asyncio
async def test_pipeline_is_deterministic(env_factory, request_factory, signals):
    env = env_factory(signals)
    req = request_factory()
    a = await env.facade.build(BuildUXStrategy(request=req))
    b = await env.facade.build(BuildUXStrategy(request=req))
    assert a.quality.overall_score == b.quality.overall_score
    assert len(a.pages) == len(b.pages)
    assert {k: len(v["nodes"]) for k, v in a.graphs.items()} == {k: len(v["nodes"]) for k, v in b.graphs.items()}


@pytest.mark.asyncio
async def test_versioning_appends_to_lineage(env_factory, request_factory, signals):
    env = env_factory(signals)
    lineage = UXReportLineageId.new()
    req = request_factory()
    v1 = await env.facade.build(BuildUXStrategy(request=req, lineage_id=lineage))
    v2 = await env.facade.build(BuildUXStrategy(request=req, lineage_id=lineage))
    assert v1.version == 1 and v2.version == 2
    history = await env.facade.history(lineage)
    assert [r.version for r in history] == [1, 2]
    assert (await env.facade.latest(lineage)).version == 2


@pytest.mark.asyncio
async def test_design_brief_bundle_and_explain(env_factory, request_factory, signals):
    env = env_factory(signals)
    view = await env.facade.build(BuildUXStrategy(request=request_factory()))
    rid = UXReportId.from_string(view.report_id)

    bundle = await env.facade.design_brief_bundle(rid)
    assert bundle.pages and bundle.applicable_laws
    assert bundle.navigation["pattern"]

    node = view.graphs["navigation"]["nodes"][0]
    trace = await env.facade.explain(rid, GraphKind.NAVIGATION, UXNodeId.from_string(node["id"]))
    assert trace.node["kind"] == "page"
    assert trace.evidence


@pytest.mark.asyncio
async def test_no_evidence_yields_unusable_strategy(env_factory, request_factory):
    env = env_factory([])  # no signals -> nothing to ground on
    view = await env.facade.build(BuildUXStrategy(request=request_factory()))
    assert not view.is_usable
    assert view.evidence_count == 0


@pytest.mark.asyncio
async def test_single_source_still_grounds(env_factory, request_factory):
    env = env_factory([signal(ProvenanceKind.PSYCHOLOGY, "p1", "Trust and reviews drive conversion", 0.9, "trust", "review")])
    view = await env.facade.build(BuildUXStrategy(request=request_factory()))
    assert view.quality.grounding == 1.0
    assert view.pages
