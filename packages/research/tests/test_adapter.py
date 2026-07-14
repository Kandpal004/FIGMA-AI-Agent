"""Adapter tests — the extractors as units, and grounding over the REAL Phase-3
Knowledge Engine corpus."""

from __future__ import annotations

import pytest
from knowledge.application.commands import ActivateEntry, AddEntry, ProposeEntry
from knowledge.application.query_service import KnowledgeQueryService
from knowledge.domain.entry.source import Source, SourceKind
from knowledge.domain.shared.ids import EntryVersionId
from knowledge.domain.shared.value_objects import Confidence as KConf, Priority
from knowledge.domain.taxonomy.category import KnowledgeCategory
from knowledge.infrastructure.container import build_in_memory_environment as build_knowledge
from knowledge.infrastructure.inmemory import InMemoryKnowledgeSearchPort

from research.application.commands import Research
from research.domain.collection.artifact import RawArtifact
from research.domain.shared.ids import ArtifactId
from research.domain.shared.value_objects import ArtifactKind, EntityType
from research.infrastructure.adapters.html_extractor import HtmlExtractor
from research.infrastructure.adapters.knowledge_link_adapter import KnowledgeLinkAdapter
from research.infrastructure.adapters.structured_extractor import StructuredExtractor

from .conftest import HTML_PAGE, make_artifact, make_source


# --------------------------- extractor units ---------------------------- #
@pytest.mark.asyncio
async def test_html_extractor_pulls_title_headings_cta_and_footer():
    source = make_source()
    artifact = make_artifact(source, kind=ArtifactKind.HTML, payload=HTML_PAGE)
    extraction = await HtmlExtractor().extract(artifact)

    labels = {e.label for e in extraction.entities}
    types = {e.type for e in extraction.entities}
    assert "Acme Store" in labels
    assert EntityType.BRAND in types
    assert EntityType.CTA in types
    assert extraction.evidence  # every extracted structure carries evidence


@pytest.mark.asyncio
async def test_structured_extractor_degrades_on_malformed_json():
    source = make_source()
    artifact = RawArtifact(
        id=ArtifactId.new(),
        source_id=source.id,
        kind=ArtifactKind.STRUCTURED,
        payload="{not valid json",
        locator=source.locator,
        collected_at=make_artifact(source, kind=ArtifactKind.STRUCTURED, payload="{}").collected_at,
    )
    extraction = await StructuredExtractor().extract(artifact)
    assert extraction.entities == ()
    assert extraction.evidence == ()
    assert extraction.relationships == ()


# --------------------------- real P3 grounding -------------------------- #
async def _author(kenv, category, title, statement):
    view = await kenv.facade.add(
        AddEntry(
            category=category,
            title=title,
            statement=statement,
            description="d",
            source=Source(name="NNG", kind=SourceKind.RESEARCH_INSTITUTE),
            confidence=KConf.of(0.9),
            priority=Priority.HIGH,
        )
    )
    vid = EntryVersionId.from_string(view.entry_version_id)
    await kenv.facade.propose(ProposeEntry(entry_version_id=vid))
    await kenv.facade.activate(ActivateEntry(entry_version_id=vid))


@pytest.mark.asyncio
async def test_grounds_evidence_in_live_knowledge_corpus(env_factory, request_factory):
    import json

    kenv = build_knowledge()
    await _author(
        kenv,
        KnowledgeCategory.CONVERSION_OPTIMIZATION,
        "Sticky add-to-cart",
        "A sticky add-to-cart bar lifts conversion on mobile.",
    )
    query_service = KnowledgeQueryService(
        kenv.repository, InMemoryKnowledgeSearchPort(kenv.storage)
    )
    link = KnowledgeLinkAdapter(query_service)

    source = make_source(uri="https://acme.example")
    payload = json.dumps(
        {
            "evidence": [
                {"claim": "Sticky add-to-cart bar on product pages", "confidence": 0.9, "category": "website"}
            ]
        }
    )
    artifact = make_artifact(source, kind=ArtifactKind.STRUCTURED, payload=payload)
    env = env_factory({source.id: [artifact]}, knowledge_link=link)

    view = await env.facade.research(Research(request=request_factory(source)))
    assert view.evidence
    grounded = [e for e in view.evidence if e.is_grounded]
    assert grounded, "expected the sticky-cart evidence to link to the live corpus"
    assert grounded[0].knowledge_id
