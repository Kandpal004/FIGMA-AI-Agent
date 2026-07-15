"""Engine behaviour tests — the pipeline end-to-end over in-memory adapters.

Proves the engine produces a complete, grounded, deterministic execution plan: every in-scope
page ordered, every section bound to Design-System tokens and a variant, the component tree and
layout model, the deterministic execution order, the review gates ending in pre-generation,
sensible quality, determinism, and versioning.
"""

from __future__ import annotations

import pytest

from design_orchestrator.application.commands import BuildExecutionPlan
from design_orchestrator.domain.shared.ids import DesignExecutionPlanId, DesignExecutionPlanLineageId
from design_orchestrator.domain.shared.value_objects import (
    GraphKind,
    PageType,
    ProvenanceKind,
    ReviewGateKind,
)


@pytest.fixture
def env(env_factory, signals):
    return env_factory(signals)


async def test_orchestrate_produces_complete_plan(env, request_factory):
    view = await env.facade.orchestrate(BuildExecutionPlan(request=request_factory()))

    assert view.page_count == 7  # the default storefront page set
    assert view.section_count > 0
    assert view.evidence_count == 11  # one per provenance supplied
    assert set(view.graphs) == {GraphKind.EXECUTION.value, GraphKind.LAYOUT.value}
    assert view.quality.is_fully_grounded
    assert view.quality.binding_integrity == 1.0
    assert view.quality.coverage == 1.0
    assert view.quality.band in {"excellent", "good"}
    assert view.is_production_ready


async def test_sections_bind_tokens_and_variants(env, request_factory):
    view = await env.facade.orchestrate(BuildExecutionPlan(request=request_factory()))
    for page in view.pages:
        assert page["sections"]
        for section in page["sections"]:
            assert section["token_bindings"], section["component"]
            assert section["variant_name"]
            # every referenced choice token is bound
            referenced = {
                section["spacing"]["gap_token"], section["spacing"]["block_token"],
                section["typography"]["heading_token"], section["typography"]["body_token"],
                *section["visual"]["surface_tokens"],
                section["animation"]["duration_token"], section["animation"]["easing_token"],
            }
            assert referenced <= set(section["token_bindings"])


async def test_execution_order_is_deterministic_and_starts_with_setup(env, request_factory):
    view = await env.facade.orchestrate(BuildExecutionPlan(request=request_factory()))
    labels = [s["label"] for s in view.execution_order]
    assert labels[0] == "setup_theme"
    assert labels[1] == "setup_tokens"
    # last steps are the review gates, ending in pre_generation
    assert labels[-1].endswith(ReviewGateKind.PRE_GENERATION.value)


async def test_component_tree_and_layout(env, request_factory):
    view = await env.facade.orchestrate(BuildExecutionPlan(request=request_factory()))
    kinds = {n["kind"] for n in view.component_tree}
    assert {"root", "page", "section", "component", "variant"} <= kinds
    roots = [n for n in view.component_tree if n["parent_id"] is None]
    assert len(roots) == 1
    assert view.layout["regions"]
    assert view.layout["placements"]


async def test_review_plan_ends_in_pre_generation(env, request_factory):
    view = await env.facade.orchestrate(BuildExecutionPlan(request=request_factory()))
    gates = [c["gate"] for c in view.review_plan]
    assert gates[-1] == ReviewGateKind.PRE_GENERATION.value
    assert ReviewGateKind.TOKENS_APPROVED.value in gates
    assert ReviewGateKind.ACCESSIBILITY_APPROVED.value in gates


async def test_scoped_pages_only(env, request_factory):
    view = await env.facade.orchestrate(
        BuildExecutionPlan(request=request_factory(pages=(PageType.PRODUCT, PageType.CART)))
    )
    assert {p["page_type"] for p in view.pages} == {PageType.PRODUCT.value, PageType.CART.value}
    assert view.quality.coverage == 1.0


async def test_bundle_projection(env, request_factory):
    view = await env.facade.orchestrate(BuildExecutionPlan(request=request_factory()))
    plan_id = DesignExecutionPlanId.from_string(view.plan_id)
    bundle = await env.facade.execution_bundle(plan_id)
    assert bundle.execution_order
    assert bundle.token_mapping
    assert bundle.variant_mapping
    assert bundle.source_refs["design_system_spec_id"] == "ds1"


async def test_determinism(env_factory, signals, request_factory):
    v1 = await env_factory(signals).facade.orchestrate(BuildExecutionPlan(request=request_factory()))
    v2 = await env_factory(signals).facade.orchestrate(BuildExecutionPlan(request=request_factory()))
    # component order per page is identical
    order1 = [(p["page_type"], [s["component"] for s in p["sections"]]) for p in v1.pages]
    order2 = [(p["page_type"], [s["component"] for s in p["sections"]]) for p in v2.pages]
    assert order1 == order2
    assert [s["label"] for s in v1.execution_order] == [s["label"] for s in v2.execution_order]
    assert v1.quality.overall_score == v2.quality.overall_score


async def test_versioning(env, request_factory):
    lineage = DesignExecutionPlanLineageId.new()
    await env.facade.orchestrate(BuildExecutionPlan(request=request_factory(), lineage_id=lineage))
    await env.facade.orchestrate(BuildExecutionPlan(request=request_factory(), lineage_id=lineage))
    history = await env.facade.history(lineage)
    assert [p.version for p in history] == [1, 2]
    assert (await env.facade.latest(lineage)).version == 2


async def test_all_upstream_provenances_surface_in_graph_nodes(env, request_factory):
    view = await env.facade.orchestrate(BuildExecutionPlan(request=request_factory()))
    plan_id = DesignExecutionPlanId.from_string(view.plan_id)
    plan = env.storage.by_id[plan_id]
    node_ev = set(plan.graphs.evidence_ids())
    provs = {plan.evidence_graph.get(e).provenance for e in node_ev}
    supplied = {
        ProvenanceKind.DESIGN_SYSTEM, ProvenanceKind.COMPONENT_INTELLIGENCE,
        ProvenanceKind.WIREFRAME, ProvenanceKind.CREATIVE_DIRECTOR,
        ProvenanceKind.DESIGN_LANGUAGE, ProvenanceKind.INFORMATION_ARCHITECTURE,
        ProvenanceKind.UX_STRATEGY, ProvenanceKind.PSYCHOLOGY, ProvenanceKind.BRAND_STRATEGY,
        ProvenanceKind.BUSINESS_STRATEGY, ProvenanceKind.KNOWLEDGE,
    }
    assert supplied <= provs
