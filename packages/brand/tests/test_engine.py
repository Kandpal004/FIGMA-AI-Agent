"""Engine tests — the brand pipeline end to end, over in-memory persistence."""

from __future__ import annotations

import pytest

from brand.application.commands import BuildBrand
from brand.domain.shared.ids import (
    BrandDecisionId,
    BrandReportId,
    BrandReportLineageId,
)
from brand.domain.shared.value_objects import BrandCategory, ProvenanceKind

from .conftest import signal


@pytest.mark.asyncio
async def test_pipeline_produces_grounded_usable_brand(env_factory, request_factory, signals):
    env = env_factory(signals)
    view = await env.facade.build(BuildBrand(request=request_factory()))

    assert view.is_usable
    assert view.quality.grounding == 1.0  # every decision cites resolvable evidence
    assert view.quality.coverage == 1.0
    assert view.primary_category == "beauty"
    assert "premium" in view.secondary_categories
    assert view.archetype == "lover"  # beauty → Lover archetype
    assert view.decisions
    assert all(d.evidence_ids for d in view.decisions)  # anti-hallucination contract
    assert view.validation_rules  # the brand is enforceable, not just descriptive


@pytest.mark.asyncio
async def test_classification_follows_brief_signals(env_factory, request_factory, signals):
    env = env_factory(signals)
    tech = await env.facade.build(
        BuildBrand(request=request_factory(industry="developer tools", descriptors=("technical",), market="mass"))
    )
    assert tech.primary_category == "technical"
    assert tech.archetype == "creator"

    enterprise = await env.facade.build(
        BuildBrand(request=request_factory(industry="b2b saas", descriptors=("enterprise",), market="mass"))
    )
    assert enterprise.primary_category == "enterprise"


@pytest.mark.asyncio
async def test_category_hint_overrides_derivation(env_factory, request_factory, signals):
    env = env_factory(signals)
    view = await env.facade.build(
        BuildBrand(request=request_factory(category_hint=BrandCategory.LUXURY))
    )
    assert view.primary_category == "luxury"
    assert view.archetype == "ruler"


@pytest.mark.asyncio
async def test_pipeline_is_deterministic(env_factory, request_factory, signals):
    env = env_factory(signals)
    req = request_factory()
    a = await env.facade.build(BuildBrand(request=req))
    b = await env.facade.build(BuildBrand(request=req))
    assert a.quality.overall_score == b.quality.overall_score
    assert a.primary_category == b.primary_category
    assert len(a.decisions) == len(b.decisions)


@pytest.mark.asyncio
async def test_versioning_appends_to_lineage(env_factory, request_factory, signals):
    env = env_factory(signals)
    lineage = BrandReportLineageId.new()
    req = request_factory()
    v1 = await env.facade.build(BuildBrand(request=req, lineage_id=lineage))
    v2 = await env.facade.build(BuildBrand(request=req, lineage_id=lineage))
    assert v1.version == 1
    assert v2.version == 2
    history = await env.facade.history(lineage)
    assert [r.version for r in history] == [1, 2]
    assert (await env.facade.latest(lineage)).version == 2


@pytest.mark.asyncio
async def test_guidelines_bundle_and_explain(env_factory, request_factory, signals):
    env = env_factory(signals)
    view = await env.facade.build(BuildBrand(request=request_factory()))
    rid = BrandReportId.from_string(view.report_id)

    bundle = await env.facade.guidelines_bundle(rid)
    assert bundle.primary_category == "beauty"
    assert bundle.validation_rules
    assert bundle.visual.direction["typography"]["display_voice"] == "editorial_serif"

    color = next(d for d in view.decisions if d.type == "color")
    trace = await env.facade.explain(rid, BrandDecisionId.from_string(color.id))
    assert "archetype" in [d.type for d in trace.derives_from]
    assert "personality" in [d.type for d in trace.expresses]
    assert trace.evidence


@pytest.mark.asyncio
async def test_no_evidence_yields_unusable_brand(env_factory, request_factory):
    env = env_factory([])  # no signals at all
    view = await env.facade.build(BuildBrand(request=request_factory()))
    # With no evidence, no decision can be grounded.
    assert view.decisions == []
    assert not view.is_usable


@pytest.mark.asyncio
async def test_single_source_still_grounds(env_factory, request_factory):
    env = env_factory([signal(ProvenanceKind.BUSINESS_STRATEGY, "s1", "Premium brand built on trust and clarity", 0.9, "premium", "trust", "brand")])
    view = await env.facade.build(BuildBrand(request=request_factory()))
    assert view.quality.grounding == 1.0
    assert view.decisions
