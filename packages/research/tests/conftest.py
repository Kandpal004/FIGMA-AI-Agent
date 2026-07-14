"""Shared fixtures for the Research Engine test suite."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from research.application.ports.clock import Clock
from research.domain.collection.artifact import RawArtifact
from research.domain.shared.ids import ArtifactId, ResearchSourceId
from research.domain.shared.value_objects import (
    ArtifactKind,
    ProviderKind,
    SourceKind,
    Tag,
)
from research.domain.source.request import ResearchRequest
from research.domain.source.source import ResearchSource, SourceLocator
from research.infrastructure.adapters.inmemory_source import InMemorySource
from research.infrastructure.container import (
    build_default_registry,
    build_in_memory_environment,
)

FIXED_NOW = datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC)

HTML_PAGE = """
<html><head><title>Acme Store</title></head>
<body>
  <nav><a href="/shop">Shop</a><a href="/about">About</a></nav>
  <h1>Premium Skincare, Delivered</h1>
  <h2>Bestsellers</h2>
  <button class="cta">Add to Cart</button>
  <footer>Free returns within 30 days</footer>
</body></html>
"""

STRUCTURED_PAYLOAD = json.dumps(
    {
        "evidence": [
            {"claim": "Uses a sticky add-to-cart bar", "confidence": 0.9, "category": "website"},
            {"claim": "Displays star ratings on PDP", "confidence": 0.8, "category": "website"},
        ],
        "entities": [
            {"type": "cta", "label": "Sticky Add to Cart", "confidence": 0.9},
            {"type": "review", "label": "Star Ratings", "confidence": 0.85},
        ],
        "relationships": [
            {"type": "has_review", "source_label": "Sticky Add to Cart", "target_label": "Star Ratings", "confidence": 0.7}
        ],
    }
)


class FixedClock(Clock):
    def now(self) -> datetime:
        return FIXED_NOW


def make_source(
    *,
    kind: SourceKind = SourceKind.BUSINESS_WEBSITE,
    provider: ProviderKind = ProviderKind.IN_MEMORY,
    uri: str = "https://acme.example",
    trust: float = 0.8,
    name: str = "Acme",
) -> ResearchSource:
    return ResearchSource(
        id=ResearchSourceId.new(),
        kind=kind,
        provider=provider,
        locator=SourceLocator(uri=uri),
        name=name,
        trust=trust,
    )


def make_artifact(
    source: ResearchSource, *, kind: ArtifactKind, payload: str
) -> RawArtifact:
    return RawArtifact(
        id=ArtifactId.new(),
        source_id=source.id,
        kind=kind,
        payload=payload,
        locator=source.locator,
        collected_at=FIXED_NOW,
    )


@pytest.fixture
def html_source() -> ResearchSource:
    return make_source(uri="https://acme.example", name="Acme Website")


@pytest.fixture
def structured_source() -> ResearchSource:
    return make_source(
        kind=SourceKind.COMPETITOR_WEBSITE, uri="https://rival.example", name="Rival"
    )


@pytest.fixture
def env_factory():
    """Build an in-memory environment whose in-memory source returns given artifacts."""

    def _make(artifacts_by_source, *, knowledge_link=None):
        source = InMemorySource()
        for sid, arts in artifacts_by_source.items():
            source.register(sid, arts)
        registry = build_default_registry(in_memory_source=source)
        return build_in_memory_environment(
            registry=registry, knowledge_link=knowledge_link, clock=FixedClock()
        )

    return _make


@pytest.fixture
def request_factory():
    def _make(*sources, project_id: str = "proj-acme", goal: str = "Acquire evidence"):
        return ResearchRequest.build(
            project_id=project_id,
            goal=goal,
            sources=sources,
            tags=(Tag.of("ecommerce"),),
        )

    return _make
