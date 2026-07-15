"""Engine behaviour tests — the pipeline end-to-end over in-memory adapters.

Proves the engine produces a complete, grounded, professionally-structured Figma model: a Cover,
a Design System, a Components page, and one page per storefront page; variable collections with
theme/device modes; published styles; component sets with variants; auto-layout frames instancing
components; the five graphs; sensible quality; determinism; and versioning.
"""

from __future__ import annotations

import pytest

from figma_design.application.commands import BuildFigmaDesign
from figma_design.domain.shared.ids import FigmaDesignModelId, FigmaDesignModelLineageId
from figma_design.domain.shared.value_objects import (
    DeviceClass,
    FigmaPageKind,
    GraphKind,
    NodeType,
    ProvenanceKind,
    StyleType,
)


@pytest.fixture
def env(env_factory, signals):
    return env_factory(signals)


async def test_compose_produces_professional_file(env, request_factory):
    view = await env.facade.compose(BuildFigmaDesign(request=request_factory()))

    assert view.page_count >= 10  # cover + design system + components + 7 storefront pages
    assert view.node_count > 0
    assert view.evidence_count == 6  # one per provenance supplied
    kinds = {p["kind"] for p in view.pages}
    assert FigmaPageKind.COVER.value in kinds
    assert FigmaPageKind.DESIGN_SYSTEM.value in kinds
    assert FigmaPageKind.COMPONENTS.value in kinds
    assert FigmaPageKind.PAGE.value in kinds
    assert set(view.graphs) == {k.value for k in GraphKind}
    assert view.quality.is_fully_grounded
    assert view.quality.reference_integrity == 1.0
    assert view.quality.band in {"excellent", "good"}
    assert view.is_production_ready


async def test_variable_collections_have_theme_and_device_modes(env, request_factory):
    view = await env.facade.compose(BuildFigmaDesign(request=request_factory()))
    modes_by_name = {c["name"]: c["modes"] for c in view.collections}
    assert modes_by_name["Theme"] == ["Light", "Dark"]
    assert modes_by_name["Device"] == ["Desktop", "Tablet", "Mobile"]
    # every variable values every mode of its collection
    for c in view.collections:
        for v in c["variables"]:
            assert set(v["values"].keys()) == set(c["modes"]), v["key"]


async def test_styles_and_component_sets(env, request_factory):
    view = await env.facade.compose(BuildFigmaDesign(request=request_factory()))
    style_types = {s["type"] for s in view.styles}
    assert {StyleType.FILL.value, StyleType.TEXT.value, StyleType.EFFECT.value} <= style_types
    assert view.component_set_count > 0
    for cs in view.component_sets:
        assert any(p["type"] == "variant" for p in cs["properties"])
        assert cs["variants"]


async def test_instances_reference_declared_component_sets(env, request_factory):
    view = await env.facade.compose(BuildFigmaDesign(request=request_factory()))
    set_ids = {cs["id"] for cs in view.component_sets}
    instance_count = 0
    for page in view.pages:
        for node in page["nodes"]:
            if node["type"] == NodeType.INSTANCE.value:
                instance_count += 1
                assert node["instance"]["component_set_id"] in set_ids
    assert instance_count > 0


async def test_auto_layout_frames_present(env, request_factory):
    view = await env.facade.compose(BuildFigmaDesign(request=request_factory()))
    auto_layout_nodes = [
        n for p in view.pages for n in p["nodes"] if n["auto_layout"] is not None
    ]
    assert auto_layout_nodes
    # every auto-layout binds a spacing token for its gap
    for n in auto_layout_nodes:
        assert n["auto_layout"]["item_spacing_token"].startswith("space.")


async def test_responsive_device_frames(env, request_factory):
    view = await env.facade.compose(
        BuildFigmaDesign(request=request_factory(devices=(DeviceClass.DESKTOP, DeviceClass.MOBILE)))
    )
    names = [n["name"] for p in view.pages for n in p["nodes"]]
    assert any("Desktop" in name for name in names)
    assert any("Mobile" in name for name in names)


async def test_bundle_projection(env, request_factory):
    view = await env.facade.compose(BuildFigmaDesign(request=request_factory()))
    model_id = FigmaDesignModelId.from_string(view.model_id)
    bundle = await env.facade.design_bundle(model_id)
    assert bundle.pages
    assert bundle.collections
    assert bundle.component_sets
    assert bundle.source_refs["execution_plan_id"] == "ep1"


async def test_determinism(env_factory, signals, request_factory):
    v1 = await env_factory(signals).facade.compose(BuildFigmaDesign(request=request_factory()))
    v2 = await env_factory(signals).facade.compose(BuildFigmaDesign(request=request_factory()))
    assert v1.page_count == v2.page_count
    assert v1.node_count == v2.node_count
    names1 = [p["name"] for p in v1.pages]
    names2 = [p["name"] for p in v2.pages]
    assert names1 == names2
    assert v1.quality.overall_score == v2.quality.overall_score


async def test_versioning(env, request_factory):
    lineage = FigmaDesignModelLineageId.new()
    await env.facade.compose(BuildFigmaDesign(request=request_factory(), lineage_id=lineage))
    await env.facade.compose(BuildFigmaDesign(request=request_factory(), lineage_id=lineage))
    history = await env.facade.history(lineage)
    assert [m.version for m in history] == [1, 2]
    assert (await env.facade.latest(lineage)).version == 2


async def test_all_upstream_provenances_surface_in_graph_nodes(env, request_factory):
    view = await env.facade.compose(BuildFigmaDesign(request=request_factory()))
    model_id = FigmaDesignModelId.from_string(view.model_id)
    model = env.storage.by_id[model_id]
    node_ev = set(model.graphs.evidence_ids())
    provs = {model.evidence_graph.get(e).provenance for e in node_ev}
    supplied = {
        ProvenanceKind.DESIGN_ORCHESTRATOR, ProvenanceKind.DESIGN_SYSTEM,
        ProvenanceKind.COMPONENT_INTELLIGENCE, ProvenanceKind.DESIGN_LANGUAGE,
        ProvenanceKind.CREATIVE_DIRECTOR, ProvenanceKind.KNOWLEDGE,
    }
    assert supplied <= provs
