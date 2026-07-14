"""Behavioural tests for the design-language engine — end-to-end through the facade."""

from __future__ import annotations

import pytest

from design_language.application.commands import BuildDesignLanguage
from design_language.domain.shared.ids import (
    DesignLanguageSpecId,
    DesignLanguageSpecLineageId,
)
from design_language.domain.shared.value_objects import (
    GraphKind,
    IndustryPreset,
    LanguageArchetype,
)

pytestmark = pytest.mark.asyncio


async def test_produces_a_production_ready_language(env_factory, request_factory, signals) -> None:
    env = env_factory(signals)
    v = await env.facade.design(BuildDesignLanguage(request=request_factory()))
    assert v.is_production_ready
    assert v.quality.grounding == 1.0
    assert v.quality.overall_score >= 90.0
    assert v.determined_attribute_count == 19
    assert v.evidence_count > 0
    assert v.version == 1


async def test_all_nineteen_attributes_determined(env_factory, request_factory, signals) -> None:
    env = env_factory(signals)
    v = await env.facade.design(BuildDesignLanguage(request=request_factory()))
    # 7 DNA attributes + 8 required philosophies + 4 personalities.
    assert v.visual_dna["visual_style"] and v.visual_dna["essence"]
    for kind in ("spacing", "grid", "alignment", "container", "elevation", "surface", "motion", "interaction"):
        assert kind in v.philosophies
    for kind in ("typography", "iconography", "illustration", "photography"):
        assert kind in v.personalities


async def test_both_graphs_are_populated(env_factory, request_factory, signals) -> None:
    env = env_factory(signals)
    v = await env.facade.design(BuildDesignLanguage(request=request_factory()))
    assert set(v.graphs.keys()) == {g.value for g in GraphKind}
    for kind, g in v.graphs.items():
        assert g["nodes"], f"graph {kind} has no nodes"


async def test_selection_records_considered_alternatives_and_why(env_factory, request_factory, signals) -> None:
    env = env_factory(signals)
    v = await env.facade.design(BuildDesignLanguage(request=request_factory()))
    assert v.language_selection["considered"], "must weigh and reject alternatives"
    assert v.explanation["why_selected"]
    assert v.explanation["why_rejected"]
    assert v.explanation["business_alignment"]


async def test_anti_generic_constraints_present(env_factory, request_factory, signals) -> None:
    env = env_factory(signals)
    v = await env.facade.design(BuildDesignLanguage(request=request_factory()))
    kinds = {c["kind"] for c in v.constraints}
    assert {"trend_avoidance", "generic_pattern_ban", "accent_limit"} <= kinds
    assert v.consistency_rules


async def test_industry_and_tier_shape_the_language(env_factory, request_factory, signals) -> None:
    env = env_factory(signals)
    beauty = await env.facade.design(BuildDesignLanguage(request=request_factory(industry=IndustryPreset.BEAUTY)))
    b2b = await env.facade.design(BuildDesignLanguage(request=request_factory(industry=IndustryPreset.B2B)))
    luxury = await env.facade.design(BuildDesignLanguage(request=request_factory(industry=IndustryPreset.LUXURY, tier="luxury")))
    # Different industries select different languages.
    assert beauty.language_selection["archetype"] != b2b.language_selection["archetype"]
    # A luxury brief lands at the top luxury level; a B2B one does not.
    assert luxury.visual_dna["luxury_level"] == 5
    assert b2b.visual_dna["luxury_level"] < 5


async def test_preferred_archetype_is_honoured(env_factory, request_factory, signals) -> None:
    env = env_factory(signals)
    v = await env.facade.design(BuildDesignLanguage(
        request=request_factory(preferred_archetype=LanguageArchetype.STRIPE)
    ))
    assert v.language_selection["archetype"] == LanguageArchetype.STRIPE.value


async def test_design_system_bundle_is_neutral(env_factory, request_factory, signals) -> None:
    env = env_factory(signals)
    v = await env.facade.design(BuildDesignLanguage(request=request_factory()))
    bundle = await env.facade.design_system_bundle(DesignLanguageSpecId.from_string(v.spec_id))
    assert bundle.visual_dna and bundle.tokens and bundle.selection
    assert bundle.is_production_ready
    # Tokens are abstract scales, never concrete pixels.
    assert "base_unit" in bundle.tokens["spacing"] and "ratio" in bundle.tokens["type_scale"]


async def test_determinism_same_input_same_language(env_factory, request_factory, signals) -> None:
    env = env_factory(signals)
    a = await env.facade.design(BuildDesignLanguage(request=request_factory()))
    b = await env.facade.design(BuildDesignLanguage(request=request_factory()))
    assert a.language_selection["archetype"] == b.language_selection["archetype"]
    assert a.quality.overall_score == b.quality.overall_score
    # Structure is deterministic (evidence ids are freshly minted per run, so drop them).
    drop_ev = lambda d: {k: v for k, v in d.items() if k != "evidence_ids"}
    assert drop_ev(a.visual_dna) == drop_ev(b.visual_dna)
    assert a.determined_attribute_count == b.determined_attribute_count


async def test_rebuild_under_lineage_bumps_version(env_factory, request_factory, signals) -> None:
    env = env_factory(signals)
    v1 = await env.facade.design(BuildDesignLanguage(request=request_factory()))
    lineage = DesignLanguageSpecLineageId.from_string(v1.lineage_id)
    v2 = await env.facade.design(BuildDesignLanguage(request=request_factory(), lineage_id=lineage))
    assert v2.version == 2
    history = await env.facade.history(lineage)
    assert [h.version for h in history] == [1, 2]
