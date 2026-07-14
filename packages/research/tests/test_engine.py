"""Engine tests — the acquisition pipeline end to end, over in-memory persistence."""

from __future__ import annotations

import pytest

from research.application.commands import Research
from research.application.source_registry import UnregisteredProviderError
from research.domain.shared.ids import ResearchReportId, ResearchReportLineageId
from research.domain.shared.value_objects import ArtifactKind, ProviderKind, SourceKind

from .conftest import HTML_PAGE, STRUCTURED_PAYLOAD, make_artifact, make_source


@pytest.mark.asyncio
async def test_pipeline_extracts_evidence_and_entities_from_html(
    env_factory, request_factory, html_source
):
    artifact = make_artifact(html_source, kind=ArtifactKind.HTML, payload=HTML_PAGE)
    env = env_factory({html_source.id: [artifact]})
    view = await env.facade.research(Research(request=request_factory(html_source)))

    assert view.is_usable
    assert len(view.evidence) > 0
    labels = {e.label for e in view.entities}
    assert "Acme Store" in labels  # <title> -> Brand
    types = {e.type for e in view.entities}
    assert "cta" in types
    assert view.quality.quality_score > 0


@pytest.mark.asyncio
async def test_pipeline_extracts_structured_payload_with_relationship(
    env_factory, request_factory, structured_source
):
    artifact = make_artifact(
        structured_source, kind=ArtifactKind.STRUCTURED, payload=STRUCTURED_PAYLOAD
    )
    env = env_factory({structured_source.id: [artifact]})
    view = await env.facade.research(Research(request=request_factory(structured_source)))

    assert len(view.evidence) == 2
    assert len(view.entities) == 2
    assert len(view.relationships) == 1
    # Category derives from the source kind (competitor website).
    assert view.results[0].category == "competitor"


@pytest.mark.asyncio
async def test_pipeline_is_deterministic(env_factory, request_factory, structured_source):
    artifact = make_artifact(
        structured_source, kind=ArtifactKind.STRUCTURED, payload=STRUCTURED_PAYLOAD
    )
    env = env_factory({structured_source.id: [artifact]})
    req = request_factory(structured_source)
    a = await env.facade.research(Research(request=req))
    b = await env.facade.research(Research(request=req))
    assert a.quality.quality_score == b.quality.quality_score
    assert len(a.evidence) == len(b.evidence) == 2


@pytest.mark.asyncio
async def test_deduplicates_identical_artifacts(env_factory, request_factory, structured_source):
    a1 = make_artifact(structured_source, kind=ArtifactKind.STRUCTURED, payload=STRUCTURED_PAYLOAD)
    a2 = make_artifact(structured_source, kind=ArtifactKind.STRUCTURED, payload=STRUCTURED_PAYLOAD)
    env = env_factory({structured_source.id: [a1, a2]})
    view = await env.facade.research(Research(request=request_factory(structured_source)))
    # Two identical payloads collapse to one result.
    assert len(view.results) == 1


@pytest.mark.asyncio
async def test_versioning_appends_to_lineage(env_factory, request_factory, structured_source):
    artifact = make_artifact(
        structured_source, kind=ArtifactKind.STRUCTURED, payload=STRUCTURED_PAYLOAD
    )
    env = env_factory({structured_source.id: [artifact]})
    lineage = ResearchReportLineageId.new()
    req = request_factory(structured_source)

    v1 = await env.facade.research(Research(request=req, lineage_id=lineage))
    v2 = await env.facade.research(Research(request=req, lineage_id=lineage))
    assert v1.version == 1
    assert v2.version == 2

    history = await env.facade.history(lineage)
    assert [r.version for r in history] == [1, 2]
    latest = await env.facade.latest(lineage)
    assert latest.version == 2


@pytest.mark.asyncio
async def test_get_and_explain_and_bundle(env_factory, request_factory, structured_source):
    from research.domain.shared.ids import EntityId

    artifact = make_artifact(
        structured_source, kind=ArtifactKind.STRUCTURED, payload=STRUCTURED_PAYLOAD
    )
    env = env_factory({structured_source.id: [artifact]})
    view = await env.facade.research(Research(request=request_factory(structured_source)))

    fetched = await env.facade.get(ResearchReportId.from_string(view.report_id))
    assert fetched.report_id == view.report_id

    bundle = await env.facade.reasoning_bundle(ResearchReportId.from_string(view.report_id))
    assert not bundle.is_empty
    assert len(bundle.entities) == 2

    entity_id = EntityId.from_string(view.entities[0].id)
    trace = await env.facade.explain(
        ResearchReportId.from_string(view.report_id), entity_id
    )
    assert trace.entity.id == view.entities[0].id
    assert len(trace.evidence) >= 1


@pytest.mark.asyncio
async def test_unregistered_provider_is_rejected(env_factory, request_factory):
    source = make_source(provider=ProviderKind.FIRECRAWL, uri="https://x.example")
    env = env_factory({})  # nothing registered for FIRECRAWL
    with pytest.raises(UnregisteredProviderError):
        await env.facade.research(Research(request=request_factory(source)))


@pytest.mark.asyncio
async def test_empty_source_yields_usable_but_empty_report(env_factory, request_factory):
    source = make_source(uri="https://empty.example")
    env = env_factory({source.id: []})  # source returns no artifacts
    view = await env.facade.research(Research(request=request_factory(source)))
    assert view.results == []
    assert view.evidence == []
    assert not view.is_usable  # no evidence -> not usable


@pytest.mark.asyncio
async def test_thin_payload_is_flagged_but_kept(env_factory, request_factory):
    source = make_source(kind=SourceKind.BRAND_GUIDELINES, uri="https://brand.example")
    thin = make_artifact(source, kind=ArtifactKind.STRUCTURED, payload='{"evidence":[]}')
    env = env_factory({source.id: [thin]})
    view = await env.facade.research(Research(request=request_factory(source)))
    # thin payload (< 20 chars of structure) surfaces a warning issue on the result.
    assert view.results
    assert any(i.startswith("warn:") for i in view.results[0].issues)
