"""Engine tests — the psychology pipeline end to end, over in-memory persistence."""

from __future__ import annotations

import pytest

from psychology.application.commands import BuildPsychology
from psychology.domain.shared.ids import (
    PsychNodeId,
    PsychologyReportId,
    PsychologyReportLineageId,
)
from psychology.domain.shared.value_objects import GraphKind, ProvenanceKind

from .conftest import signal


@pytest.mark.asyncio
async def test_pipeline_produces_grounded_usable_model(env_factory, request_factory, signals):
    env = env_factory(signals)
    view = await env.facade.build(BuildPsychology(request=request_factory()))

    assert view.is_usable
    assert view.quality.grounding == 1.0  # everything is evidence-backed
    assert view.quality.coverage == 1.0
    assert view.quality.framework_validation == 1.0  # all five frameworks applied
    assert view.awareness == "solution_aware"
    assert view.sophistication == "stage_5_identification"  # premium market


@pytest.mark.asyncio
async def test_all_matrices_and_graphs_are_built(env_factory, request_factory, signals):
    env = env_factory(signals)
    view = await env.facade.build(BuildPsychology(request=request_factory()))
    # All nine matrices present.
    for name in ("objection", "trust", "motivation", "emotion", "behavior", "risk", "value", "confidence", "retention"):
        assert view.matrices[name], f"{name} matrix is empty"
    # All six graphs present and populated.
    for name in ("decision", "emotion", "trust", "objection", "motivation", "behavior"):
        assert view.graphs[name]["nodes"], f"{name} graph is empty"
    # All matrix cells cite evidence (anti-hallucination).
    assert all(c["evidence_ids"] for cells in view.matrices.values() for c in cells)


@pytest.mark.asyncio
async def test_sophistication_follows_market(env_factory, request_factory, signals):
    env = env_factory(signals)
    mass = await env.facade.build(BuildPsychology(request=request_factory(market="mass", price_band="value")))
    assert mass.sophistication == "stage_4_amplified_mechanism"


@pytest.mark.asyncio
async def test_fogg_lever_is_computed(env_factory, request_factory, signals):
    env = env_factory(signals)
    view = await env.facade.build(BuildPsychology(request=request_factory()))
    assert view.frameworks["fogg"]["primary_lever"] in {"increase_ability", "increase_motivation", "fix_prompt"}
    assert "behavioral_economics" in view.frameworks["applied"]


@pytest.mark.asyncio
async def test_pipeline_is_deterministic(env_factory, request_factory, signals):
    env = env_factory(signals)
    req = request_factory()
    a = await env.facade.build(BuildPsychology(request=req))
    b = await env.facade.build(BuildPsychology(request=req))
    assert a.quality.overall_score == b.quality.overall_score
    assert a.awareness == b.awareness
    assert {k: len(v) for k, v in a.matrices.items()} == {k: len(v) for k, v in b.matrices.items()}


@pytest.mark.asyncio
async def test_versioning_appends_to_lineage(env_factory, request_factory, signals):
    env = env_factory(signals)
    lineage = PsychologyReportLineageId.new()
    req = request_factory()
    v1 = await env.facade.build(BuildPsychology(request=req, lineage_id=lineage))
    v2 = await env.facade.build(BuildPsychology(request=req, lineage_id=lineage))
    assert v1.version == 1 and v2.version == 2
    history = await env.facade.history(lineage)
    assert [r.version for r in history] == [1, 2]
    assert (await env.facade.latest(lineage)).version == 2


@pytest.mark.asyncio
async def test_ux_directive_bundle_and_explain(env_factory, request_factory, signals):
    env = env_factory(signals)
    view = await env.facade.build(BuildPsychology(request=request_factory()))
    rid = PsychologyReportId.from_string(view.report_id)

    bundle = await env.facade.ux_directive_bundle(rid)
    assert bundle.awareness == "solution_aware"
    assert bundle.objections and bundle.feasible_behaviors

    node = view.graphs["motivation"]["nodes"][0]
    trace = await env.facade.explain(rid, GraphKind.MOTIVATION, PsychNodeId.from_string(node["id"]))
    assert trace.node["kind"] in {"motivation", "need"}
    assert trace.evidence


@pytest.mark.asyncio
async def test_no_evidence_yields_unusable_model(env_factory, request_factory):
    env = env_factory([])  # no signals -> nothing to ground on
    view = await env.facade.build(BuildPsychology(request=request_factory()))
    assert not view.is_usable
    assert view.quality.grounding < 1.0 or view.evidence_count == 0


@pytest.mark.asyncio
async def test_single_source_still_grounds(env_factory, request_factory):
    env = env_factory([signal(ProvenanceKind.BRAND_STRATEGY, "b1", "Trust and reviews drive confidence", 0.9, "trust", "review")])
    view = await env.facade.build(BuildPsychology(request=request_factory()))
    assert view.quality.grounding == 1.0
    assert view.matrices["objection"]
