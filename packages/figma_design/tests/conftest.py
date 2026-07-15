"""Shared fixtures for the Figma Design Engine test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from figma_design.application.contracts import RawSignal
from figma_design.application.ports.clock import Clock
from figma_design.application.request import FigmaDesignRequest
from figma_design.domain.context.context import FigmaBrief, ProjectContext, SourceRefs
from figma_design.domain.shared.value_objects import DeviceClass, ProvenanceKind
from figma_design.infrastructure.adapters.inmemory_inputs import (
    InMemoryComponentIntelligenceInput,
    InMemoryCreativeDirectorInput,
    InMemoryDesignLanguageInput,
    InMemoryDesignOrchestratorInput,
    InMemoryDesignSystemInput,
    InMemoryKnowledgeAdvisor,
)
from figma_design.infrastructure.container import build_in_memory_environment

FIXED_NOW = datetime(2026, 7, 15, 12, 0, 0, tzinfo=UTC)


class FixedClock(Clock):
    def now(self) -> datetime:
        return FIXED_NOW


def signal(
    provenance: ProvenanceKind, ref: str, claim: str, confidence: float, *tags: str
) -> RawSignal:
    return RawSignal(
        provenance=provenance, external_ref=ref, claim=claim,
        confidence=confidence, source_name=provenance.value, tags=tags,
    )


@pytest.fixture
def signals() -> list[RawSignal]:
    """A rich, cross-provenance signal set covering the model's grounding needs."""
    P = ProvenanceKind
    return [
        signal(P.DESIGN_ORCHESTRATOR, "ep1", "Ordered pages and sections to lay out", 0.9,
               "page", "section", "order", "auto-layout"),
        signal(P.DESIGN_SYSTEM, "ds1", "Tokens become variables and styles", 0.9,
               "variable", "style", "token", "mode"),
        signal(P.COMPONENT_INTELLIGENCE, "ci1", "Included components become component sets", 0.9,
               "component-set", "variant", "instance"),
        signal(P.DESIGN_LANGUAGE, "dl1", "Premium restrained visual language", 0.85,
               "style", "typography", "visual"),
        signal(P.CREATIVE_DIRECTOR, "cd1", "Library-grade file with clean auto-layout", 0.9,
               "quality", "library", "handoff", "dev-mode"),
        signal(P.KNOWLEDGE, "k1", "Professional Figma file organization best-practice", 0.85,
               "figma", "file-craft", "variable", "organization"),
    ]


@pytest.fixture
def request_factory():
    def _make(
        *,
        product_category: str = "skincare",
        devices: tuple[DeviceClass, ...] = (DeviceClass.DESKTOP, DeviceClass.TABLET,
                                            DeviceClass.MOBILE),
        dark_mode: bool = True,
        market: str = "premium",
    ) -> FigmaDesignRequest:
        return FigmaDesignRequest(
            brief=FigmaBrief(product_category=product_category, devices=devices,
                             dark_mode=dark_mode),
            project=ProjectContext(project_id="proj-x", platform="shopify_plus", market=market),
            source_refs=SourceRefs(execution_plan_id="ep1", design_system_spec_id="ds1"),
        )

    return _make


def _ports(signals_list):
    buckets: dict[ProvenanceKind, list[RawSignal]] = {p: [] for p in ProvenanceKind}
    for s in signals_list:
        buckets.setdefault(s.provenance, []).append(s)
    P = ProvenanceKind
    return dict(
        design_orchestrator=InMemoryDesignOrchestratorInput(buckets[P.DESIGN_ORCHESTRATOR]),
        design_system=InMemoryDesignSystemInput(buckets[P.DESIGN_SYSTEM]),
        component_intelligence=InMemoryComponentIntelligenceInput(buckets[P.COMPONENT_INTELLIGENCE]),
        design_language=InMemoryDesignLanguageInput(buckets[P.DESIGN_LANGUAGE]),
        creative_director=InMemoryCreativeDirectorInput(buckets[P.CREATIVE_DIRECTOR]),
        knowledge=InMemoryKnowledgeAdvisor(buckets[P.KNOWLEDGE]),
    )


@pytest.fixture
def env_factory():
    """Build an in-memory environment whose input ports return the given signals."""

    def _make(signals_list=()):
        return build_in_memory_environment(clock=FixedClock(), **_ports(signals_list))

    return _make


@pytest.fixture
def built_model(signals):
    """A real model built through the in-memory engine (for aggregate-level tests)."""
    import asyncio

    from figma_design.application.commands import BuildFigmaDesign

    env = build_in_memory_environment(clock=FixedClock(), **_ports(signals))
    request = FigmaDesignRequest(
        brief=FigmaBrief(product_category="skincare"),
        project=ProjectContext(project_id="proj-x"),
        source_refs=SourceRefs(execution_plan_id="ep1"),
    )
    return asyncio.run(env.engine.build(BuildFigmaDesign(request=request)))
