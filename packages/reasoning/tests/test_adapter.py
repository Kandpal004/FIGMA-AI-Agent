"""Integration test: reasoning over the REAL Phase-3 Knowledge Engine corpus."""

from __future__ import annotations

import pytest

from knowledge.application.commands import ActivateEntry, AddEntry, ProposeEntry
from knowledge.application.reasoner import KnowledgeReasoner
from knowledge.domain.entry.applicability import Applicability
from knowledge.domain.entry.source import Source, SourceKind
from knowledge.domain.shared.ids import EntryVersionId
from knowledge.domain.shared.value_objects import Confidence, Platform, Priority
from knowledge.domain.taxonomy.category import KnowledgeCategory
from knowledge.infrastructure.container import build_in_memory_environment as build_knowledge

from reasoning.application.commands import GenerateStrategy
from reasoning.domain.request.request import ReasoningRequest
from reasoning.domain.shared.value_objects import StrategyStance
from reasoning.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter
from reasoning.infrastructure.container import build_in_memory_environment


async def _author(kenv, cat, title, statement, *, page_types=("product",), platforms=(), conf=0.85, prio=Priority.NORMAL):
    view = await kenv.facade.add(AddEntry(
        category=cat, title=title, statement=statement, description="d",
        source=Source(name="NNG", kind=SourceKind.RESEARCH_INSTITUTE),
        confidence=Confidence.of(conf), priority=prio,
        applicability=Applicability.build(page_types=page_types, platforms=platforms)))
    vid = EntryVersionId.from_string(view.entry_version_id)
    await kenv.facade.propose(ProposeEntry(entry_version_id=vid))
    await kenv.facade.activate(ActivateEntry(entry_version_id=vid))


async def test_reasons_over_live_knowledge_corpus():
    kenv = build_knowledge()
    await _author(kenv, KnowledgeCategory.UX_LAWS, "Fitts's Law", "Big, close primary targets.", conf=0.9)
    await _author(kenv, KnowledgeCategory.CONVERSION_OPTIMIZATION, "Prominent CTA",
                  "One high-contrast CTA.", conf=0.85, prio=Priority.CRITICAL)
    await _author(kenv, KnowledgeCategory.ACCESSIBILITY, "Contrast", "4.5:1 minimum.", conf=0.95)
    await _author(kenv, KnowledgeCategory.SHOPIFY_PLUS, "Checkout locked", "Checkout is limited.",
                  page_types=(), platforms=[Platform.SHOPIFY_PLUS], conf=0.9)
    await _author(kenv, KnowledgeCategory.DESIGN_PRINCIPLES, "Gallery", "Product gallery anchors the PDP.")

    adapter = KnowledgeAdvisorAdapter(KnowledgeReasoner(kenv.repository))
    env = build_in_memory_environment(adapter)
    request = ReasoningRequest(user_request="PDP", project_id="p", section_id="s",
                               page_type="product", platform="shopify_plus", stance=StrategyStance.CONVERSION_FIRST)
    view = await env.facade.reason(GenerateStrategy(request=request))

    # every cited principle came from the real corpus (pinned version ids)
    assert view.ux_principles and view.ux_principles[0].statement == "Big, close primary targets."
    assert view.cro_principles and view.accessibility_rules
    assert view.shopify_constraints and view.risk_overall_level == "critical"
    assert view.sections  # from DESIGN_PRINCIPLES structure knowledge
    assert view.evidence_count >= 5
