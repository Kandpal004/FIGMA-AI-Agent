"""Integration test: strategy grounded in the REAL Phase-3 Knowledge and Phase-6
Research engines — no fakes, live corpora."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

# --- Phase 3: Knowledge Engine ---------------------------------------------
from knowledge.application.commands import ActivateEntry, AddEntry, ProposeEntry
from knowledge.application.query_service import KnowledgeQueryService
from knowledge.domain.entry.source import Source, SourceKind as KSourceKind
from knowledge.domain.shared.ids import EntryVersionId
from knowledge.domain.shared.value_objects import Confidence as KConf, Priority
from knowledge.domain.taxonomy.category import KnowledgeCategory
from knowledge.infrastructure.container import build_in_memory_environment as build_knowledge
from knowledge.infrastructure.inmemory import InMemoryKnowledgeSearchPort

# --- Phase 6: Research Engine ----------------------------------------------
from research.application.commands import Research
from research.domain.collection.artifact import RawArtifact
from research.domain.shared.ids import ArtifactId, ResearchReportId, ResearchSourceId
from research.domain.shared.value_objects import (
    ArtifactKind,
    ProviderKind as RProviderKind,
    SourceKind as RSourceKind,
)
from research.domain.source.request import ResearchRequest
from research.domain.source.source import ResearchSource, SourceLocator
from research.infrastructure.adapters.inmemory_source import InMemorySource
from research.infrastructure.container import (
    build_default_registry,
    build_in_memory_environment as build_research,
)

# --- Phase 7: Strategy Engine ----------------------------------------------
from strategy.application.commands import BuildStrategy
from strategy.domain.shared.ids import StrategicDecisionId, StrategyReportId
from strategy.infrastructure.adapters.knowledge_advisor_adapter import (
    KnowledgeAdvisorAdapter,
)
from strategy.infrastructure.adapters.research_input_adapter import ResearchInputAdapter
from strategy.infrastructure.container import build_in_memory_environment as build_strategy

from .conftest import FixedClock


async def _author(kenv, category, title, statement):
    view = await kenv.facade.add(
        AddEntry(
            category=category, title=title, statement=statement, description="d",
            source=Source(name="NNG", kind=KSourceKind.RESEARCH_INSTITUTE),
            confidence=KConf.of(0.9), priority=Priority.HIGH,
        )
    )
    vid = EntryVersionId.from_string(view.entry_version_id)
    await kenv.facade.propose(ProposeEntry(entry_version_id=vid))
    await kenv.facade.activate(ActivateEntry(entry_version_id=vid))


async def _produce_research_report():
    """Run the real Phase-6 engine to produce a research report, return (facade, id)."""
    source = ResearchSource(
        id=ResearchSourceId.new(),
        kind=RSourceKind.BUSINESS_WEBSITE,
        provider=RProviderKind.IN_MEMORY,
        locator=SourceLocator(uri="https://acme.example"),
        name="Acme",
        trust=0.8,
    )
    payload = json.dumps(
        {
            "evidence": [
                {"claim": "Product pages show verified reviews and ratings", "confidence": 0.9, "category": "website"},
                {"claim": "Checkout displays secure-payment and returns messaging", "confidence": 0.85, "category": "website"},
            ]
        }
    )
    artifact = RawArtifact(
        id=ArtifactId.new(), source_id=source.id, kind=ArtifactKind.STRUCTURED,
        payload=payload, locator=source.locator, collected_at=datetime.now(UTC),
    )
    in_memory = InMemorySource()
    in_memory.register(source.id, [artifact])
    registry = build_default_registry(in_memory_source=in_memory)
    renv = build_research(registry=registry)
    request = ResearchRequest.build("proj-acme", "Acquire evidence", sources=(source,))
    view = await renv.facade.research(Research(request=request))
    return renv.facade, ResearchReportId.from_string(view.report_id)


@pytest.mark.asyncio
async def test_strategy_grounded_in_live_knowledge_and_research(request_factory):
    # Phase 3: seed a live knowledge corpus (a single keyword-rich principle that
    # several strategic topics resolve to).
    kenv = build_knowledge()
    await _author(
        kenv,
        KnowledgeCategory.CONVERSION_OPTIMIZATION,
        "Trust and clear value drive conversion",
        "Visible customer trust signals and a clear value proposition and positioning lift conversion and retention.",
    )
    query_service = KnowledgeQueryService(kenv.repository, InMemoryKnowledgeSearchPort(kenv.storage))
    knowledge_adapter = KnowledgeAdvisorAdapter(query_service)

    # Phase 6: produce a live research report.
    research_facade, report_id = await _produce_research_report()
    research_adapter = ResearchInputAdapter(research_facade, report_id)

    # Phase 7: build strategy over the real upstream adapters.
    env = build_strategy(
        research=research_adapter, knowledge=knowledge_adapter, clock=FixedClock()
    )
    view = await env.facade.build(BuildStrategy(request=request_factory()))

    assert view.is_usable
    assert view.quality.grounding == 1.0
    assert view.evidence_count > 0

    # The strategy must cite both live knowledge and live research evidence.
    rid = StrategyReportId.from_string(view.report_id)
    provenances: set[str] = set()
    for decision in view.decisions:
        trace = await env.facade.explain(rid, StrategicDecisionId.from_string(decision.id))
        provenances.update(e["provenance"] for e in trace.evidence)
    assert "knowledge" in provenances
    assert "research" in provenances
