"""Integration test: intelligence over the REAL Phase-3 Knowledge Engine corpus."""

from __future__ import annotations

from knowledge.application.commands import ActivateEntry, AddEntry, ProposeEntry
from knowledge.application.reasoner import KnowledgeReasoner
from knowledge.domain.entry.source import Source, SourceKind
from knowledge.domain.shared.ids import EntryVersionId
from knowledge.domain.shared.value_objects import Confidence as KConf, Priority
from knowledge.domain.taxonomy.category import KnowledgeCategory
from knowledge.infrastructure.container import build_in_memory_environment as build_knowledge

from competitive.application.commands import AnalyzeCompetitors
from competitive.infrastructure.adapters.knowledge_advisor_adapter import KnowledgeAdvisorAdapter
from competitive.infrastructure.container import build_in_memory_environment
from competitive.infrastructure.inmemory import InMemoryDataSource


async def _author(kenv, category, title, statement):
    view = await kenv.facade.add(AddEntry(
        category=category, title=title, statement=statement, description="d",
        source=Source(name="NNG", kind=SourceKind.RESEARCH_INSTITUTE),
        confidence=KConf.of(0.9), priority=Priority.HIGH))
    vid = EntryVersionId.from_string(view.entry_version_id)
    await kenv.facade.propose(ProposeEntry(entry_version_id=vid))
    await kenv.facade.activate(ActivateEntry(entry_version_id=vid))


async def test_grounds_recommendations_in_live_corpus(observations, brief):
    kenv = build_knowledge()
    await _author(kenv, KnowledgeCategory.CONVERSION_OPTIMIZATION, "Prominent CTA", "One high-contrast CTA.")
    await _author(kenv, KnowledgeCategory.TYPOGRAPHY, "Editorial serif", "Serif conveys editorial trust.")

    adapter = KnowledgeAdvisorAdapter(KnowledgeReasoner(kenv.repository))
    env = build_in_memory_environment(data_source=InMemoryDataSource(observations), advisor=adapter)
    view = await env.facade.analyze(AnalyzeCompetitors(brief=brief))

    assert view.evidence and any(e.statement == "One high-contrast CTA." for e in view.evidence)
    assert len(view.recommendations) >= 1 and all(r.evidence_ids for r in view.recommendations)
    assert view.is_actionable
