"""The reasoning core and authoring lifecycle, driven through the facade."""

from __future__ import annotations

import pytest

from knowledge.application.commands import (
    ActivateEntry,
    AddRelation,
    ProposeEntry,
    ReviseEntry,
)
from knowledge.domain.entry.applicability import Applicability
from knowledge.domain.entry.relation import RelationType
from knowledge.domain.entry.source import Source, SourceKind
from knowledge.domain.reasoning.context import DecisionContext
from knowledge.domain.shared.ids import EntryVersionId, KnowledgeId
from knowledge.domain.shared.value_objects import Confidence, Platform, Priority, Tag
from knowledge.domain.taxonomy.category import KnowledgeCategory

NNG = Source(name="Nielsen Norman Group", kind=SourceKind.RESEARCH_INSTITUTE)
BAYMARD = Source(name="Baymard Institute", kind=SourceKind.RESEARCH_INSTITUTE)
CD = Source(name="Creative Director", kind=SourceKind.CREATIVE_DIRECTOR)


async def _corpus(env, author_active):
    hicks = await author_active(
        category=KnowledgeCategory.UX_LAWS, title="Hick's Law",
        statement="Reduce choices to speed decisions.", description="d", source=NNG,
        confidence=Confidence.of(0.92), priority=Priority.HIGH,
        applicability=Applicability.build(page_types=["product"]),
    )
    cro = await author_active(
        category=KnowledgeCategory.CONVERSION_OPTIMIZATION, title="Prominent Add-to-Cart",
        statement="A single high-contrast CTA lifts conversion.", description="d", source=BAYMARD,
        confidence=Confidence.of(0.85), priority=Priority.CRITICAL,
        applicability=Applicability.build(page_types=["product"], component_types=["buy_box"],
                                          platforms=[Platform.SHOPIFY_PLUS]),
    )
    minimal = await author_active(
        category=KnowledgeCategory.CREATIVE_DIRECTION, title="Restrained Buy Box",
        statement="Keep the buy box understated.", description="d", source=CD,
        confidence=Confidence.of(0.7), priority=Priority.HIGH,
        applicability=Applicability.build(page_types=["product"], component_types=["buy_box"]),
    )
    shopify = await author_active(
        category=KnowledgeCategory.SHOPIFY_PLUS, title="Checkout is Locked",
        statement="Shopify checkout customization is limited.", description="d",
        source=Source(name="Shopify", kind=SourceKind.INDUSTRY), priority=Priority.CRITICAL,
        applicability=Applicability.build(platforms=[Platform.SHOPIFY_PLUS]),
    )
    # a DRAFT that must never surface
    from knowledge.application.commands import AddEntry
    await env.facade.add(AddEntry(
        category=KnowledgeCategory.UX_LAWS, title="Draft Only", statement="hidden",
        description="d", source=NNG, applicability=Applicability.build(page_types=["product"])))

    # relations: cro CONTRADICTS minimal ; hicks SUPPORTS cro
    await env.facade.add_relation(AddRelation(
        entry_version_id=EntryVersionId.from_string(cro.entry_version_id),
        relation_type=RelationType.CONTRADICTS,
        target=KnowledgeId.from_string(minimal.knowledge_id)))
    await env.facade.add_relation(AddRelation(
        entry_version_id=EntryVersionId.from_string(hicks.entry_version_id),
        relation_type=RelationType.SUPPORTS,
        target=KnowledgeId.from_string(cro.knowledge_id)))
    return hicks, cro, minimal, shopify


async def test_rationale_selects_ranks_and_resolves_conflict(env, author_active) -> None:
    _hicks, _cro, _minimal, _shopify = await _corpus(env, author_active)
    ctx = DecisionContext.build(
        page_type="product", component_type="buy_box", platform=Platform.SHOPIFY_PLUS,
        goal="increase add-to-cart",
    )
    rationale = await env.facade.ask(ctx)
    titles = [c.title for c in rationale.citations]

    assert "Draft Only" not in titles              # drafts never served
    assert {"Prominent Add-to-Cart", "Restrained Buy Box", "Hick's Law"} <= set(titles)
    assert rationale.primary.title == "Prominent Add-to-Cart"  # CRITICAL ranks first

    # deterministic
    again = await env.facade.ask(ctx)
    assert [c.title for c in again.citations] == titles

    # conflict resolved by priority x confidence (34 vs 21)
    assert len(rationale.conflicts) == 1
    assert rationale.conflicts[0].winner.title == "Prominent Add-to-Cart"
    assert rationale.conflicts[0].loser.title == "Restrained Buy Box"


async def test_which_apply_respects_applicability(env, author_active) -> None:
    await _corpus(env, author_active)
    cart = await env.facade.which_apply(DecisionContext.build(page_type="cart"))
    assert "Prominent Add-to-Cart" not in [e.title for e in cart]  # product/buy_box only


async def test_explain_uses_reverse_supporting_chain(env, author_active) -> None:
    _hicks, cro, _minimal, _shopify = await _corpus(env, author_active)
    explanation = await env.facade.explain(KnowledgeId.from_string(cro.knowledge_id))
    titles = [c.title for c in explanation.citations]
    assert titles[0] == "Prominent Add-to-Cart"
    assert "Hick's Law" in titles  # hicks SUPPORTS cro (incoming edge)


async def test_platform_constraints(env, author_active) -> None:
    await _corpus(env, author_active)
    constraints = await env.facade.platform_constraints(Platform.SHOPIFY_PLUS)
    assert any(e.title == "Checkout is Locked" for e in constraints)


async def test_revise_activate_supersedes_prior(env, author_active) -> None:
    hicks, _cro, _minimal, _shopify = await _corpus(env, author_active)
    kid = KnowledgeId.from_string(hicks.knowledge_id)
    v2 = await env.facade.revise(ReviseEntry(
        from_entry_version_id=EntryVersionId.from_string(hicks.entry_version_id),
        statement="Fewer, grouped choices decide faster."))
    assert v2.version == 2
    vid = EntryVersionId.from_string(v2.entry_version_id)
    await env.facade.propose(ProposeEntry(entry_version_id=vid))
    await env.facade.activate(ActivateEntry(entry_version_id=vid))

    current = await env.facade.get_active(kid)
    assert current.version == 2
    history = await env.facade.history(kid)
    assert [e.version for e in history] == [1, 2]
    assert history[0].status == "superseded"
