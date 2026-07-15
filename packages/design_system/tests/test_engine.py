"""Engine behaviour tests — the pipeline end-to-end over in-memory adapters.

Proves the engine produces a complete, grounded, internally consistent design system: three-tier
tokens with full integrity, every component fully specified with all three platform mappings,
light/dark themes at parity, RTL localization, the derived constraints (mandatory blocking rules
present), the six graphs, sensible quality, determinism, and versioning.
"""

from __future__ import annotations

import pytest

from design_system.application.commands import BuildDesignSystem
from design_system.domain.shared.ids import DesignSystemSpecId, DesignSystemSpecLineageId
from design_system.domain.shared.value_objects import (
    ComponentType,
    ConstraintKind,
    GraphKind,
    Platform,
    ProvenanceKind,
    ThemeMode,
    TokenTier,
)


@pytest.fixture
def env(env_factory, signals):
    return env_factory(signals)


async def test_build_produces_complete_design_system(env, request_factory):
    view = await env.facade.build(BuildDesignSystem(request=request_factory()))

    assert view.token_count > 0
    assert view.component_count > 0
    assert view.evidence_count == 10  # one per provenance supplied
    # tokens span all three tiers
    tiers = {t["tier"] for t in view.tokens}
    assert tiers == {TokenTier.PRIMITIVE.value, TokenTier.SEMANTIC.value, TokenTier.COMPONENT.value}
    # six graphs present
    assert set(view.graphs) == {k.value for k in GraphKind}
    # quality is strong and fully grounded
    assert view.quality.is_fully_grounded
    assert view.quality.token_integrity == 1.0
    assert view.quality.band in {"excellent", "good"}


async def test_every_component_is_fully_specified(env, request_factory):
    view = await env.facade.build(BuildDesignSystem(request=request_factory()))
    for spec in view.components:
        assert spec["token_refs"], spec["component"]
        # all three platform mappings present
        assert set(spec["mappings"]) == {p.value for p in
                                         (Platform.GENERIC, Platform.SHOPIFY, Platform.MAGENTO)}
        # a default state and an accessibility role
        assert any(s["state"] == "default" for s in spec["states"])
        assert spec["accessibility"]["role"]
        assert spec["responsive"]  # mobile-first behaviour present


async def test_themes_and_localization(env, request_factory):
    view = await env.facade.build(BuildDesignSystem(request=request_factory()))
    modes = {t["mode"] for t in view.themes}
    assert modes == {ThemeMode.LIGHT.value, ThemeMode.DARK.value}
    # parity: both themes remap the same keys
    keysets = [set(t["overrides"]) for t in view.themes]
    assert keysets[0] == keysets[1]
    assert view.localization["supports_rtl"] is True
    assert view.localization["mirror_properties"]


async def test_constraints_include_mandatory_and_conditional(env, request_factory):
    view = await env.facade.build(BuildDesignSystem(request=request_factory()))
    kinds = {c["kind"] for c in view.constraints}
    assert ConstraintKind.TOKEN_ONLY.value in kinds
    assert ConstraintKind.NO_HARDCODED.value in kinds
    assert ConstraintKind.THEME_PARITY.value in kinds  # dark mode requested
    assert ConstraintKind.RTL_MIRROR.value in kinds  # RTL requested
    blocking = {c["kind"] for c in view.constraints if c["enforcement"] == "blocking"}
    assert {ConstraintKind.TOKEN_ONLY.value, ConstraintKind.NO_HARDCODED.value} <= blocking


async def test_light_only_when_dark_mode_disabled(env, request_factory):
    view = await env.facade.build(
        BuildDesignSystem(request=request_factory(dark_mode=False))
    )
    modes = {t["mode"] for t in view.themes}
    assert modes == {ThemeMode.LIGHT.value}
    kinds = {c["kind"] for c in view.constraints}
    assert ConstraintKind.THEME_PARITY.value not in kinds


async def test_token_graph_encodes_three_tiers(env, request_factory):
    view = await env.facade.build(BuildDesignSystem(request=request_factory()))
    spec_id = DesignSystemSpecId.from_string(view.spec_id)
    token_graph = (await env.facade.graph(spec_id, GraphKind.TOKEN)).graph
    assert len(token_graph["nodes"]) == view.token_count
    # semantic/component tokens alias/derive from something -> edges exist
    assert token_graph["edges"]


async def test_platform_mapping_projection(env, request_factory):
    view = await env.facade.build(BuildDesignSystem(request=request_factory()))
    spec_id = DesignSystemSpecId.from_string(view.spec_id)
    shopify = await env.facade.platform_mapping(spec_id, ComponentType.PRODUCT_INFORMATION,
                                                Platform.SHOPIFY.value)
    assert shopify["primitive"]
    assert shopify["identifier"]


async def test_determinism(env_factory, signals, request_factory):
    v1 = await env_factory(signals).facade.build(BuildDesignSystem(request=request_factory()))
    v2 = await env_factory(signals).facade.build(BuildDesignSystem(request=request_factory()))
    # structure is identical (ignore freshly-minted ids/evidence)
    drop = lambda toks: [{k: t[k] for k in t if k != "evidence_ids"} for t in toks]
    assert drop(v1.tokens) == drop(v2.tokens)
    assert [c["component"] for c in v1.components] == [c["component"] for c in v2.components]
    assert {c["kind"] for c in v1.constraints} == {c["kind"] for c in v2.constraints}
    assert v1.quality.overall_score == v2.quality.overall_score


async def test_versioning(env, request_factory):
    lineage = DesignSystemSpecLineageId.new()
    await env.facade.build(BuildDesignSystem(request=request_factory(), lineage_id=lineage))
    await env.facade.build(BuildDesignSystem(request=request_factory(), lineage_id=lineage))
    history = await env.facade.history(lineage)
    assert [s.version for s in history] == [1, 2]
    assert (await env.facade.latest(lineage)).version == 2


async def test_explain_graph_node(env, request_factory):
    from design_system.domain.shared.ids import DSNodeId

    view = await env.facade.build(BuildDesignSystem(request=request_factory()))
    spec_id = DesignSystemSpecId.from_string(view.spec_id)
    comp_graph = view.graphs[GraphKind.COMPONENT.value]
    node_id = DSNodeId.from_string(comp_graph["nodes"][0]["id"])
    trace = await env.facade.explain(spec_id, GraphKind.COMPONENT, node_id)
    assert trace.node["id"] == str(node_id)


async def test_all_upstream_provenances_surface_in_graph_nodes(env, request_factory):
    """Every supplied upstream engine appears in some graph node's evidence."""
    view = await env.facade.build(BuildDesignSystem(request=request_factory()))
    spec_id = DesignSystemSpecId.from_string(view.spec_id)
    spec = env.storage.by_id[spec_id]
    node_ev = set(spec.graphs.evidence_ids())
    provs = {spec.evidence_graph.get(e).provenance for e in node_ev}
    supplied = {
        ProvenanceKind.DESIGN_LANGUAGE, ProvenanceKind.COMPONENT_INTELLIGENCE,
        ProvenanceKind.CREATIVE_DIRECTOR, ProvenanceKind.BUSINESS_STRATEGY,
        ProvenanceKind.BRAND_STRATEGY, ProvenanceKind.PSYCHOLOGY, ProvenanceKind.UX_STRATEGY,
        ProvenanceKind.INFORMATION_ARCHITECTURE, ProvenanceKind.WIREFRAME,
        ProvenanceKind.KNOWLEDGE,
    }
    assert supplied <= provs
