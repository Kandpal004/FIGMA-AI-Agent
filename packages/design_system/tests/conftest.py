"""Shared fixtures for the Design System Engine test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from design_system.application.contracts import RawSignal
from design_system.application.ports.clock import Clock
from design_system.application.request import DesignSystemRequest
from design_system.domain.context.context import DesignSystemBrief, ProjectContext
from design_system.domain.shared.value_objects import Direction, Platform, ProvenanceKind
from design_system.infrastructure.adapters.inmemory_inputs import (
    InMemoryBrandInput,
    InMemoryBusinessStrategyInput,
    InMemoryComponentIntelligenceInput,
    InMemoryCreativeDirectorInput,
    InMemoryDesignLanguageInput,
    InMemoryIAInput,
    InMemoryKnowledgeAdvisor,
    InMemoryPsychologyInput,
    InMemoryUXInput,
    InMemoryWireframeInput,
)
from design_system.infrastructure.container import build_in_memory_environment

FIXED_NOW = datetime(2026, 7, 14, 12, 0, 0, tzinfo=UTC)


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
    """A rich, cross-provenance signal set covering the design system's grounding needs."""
    P = ProvenanceKind
    return [
        signal(P.DESIGN_LANGUAGE, "d1", "Abstract type/space/radius scales and palette intent",
               0.85, "token", "scale", "typography", "color", "design", "language"),
        signal(P.COMPONENT_INTELLIGENCE, "ci1",
               "Composition needs header, product card, cart drawer, forms fully specified",
               0.9, "component", "variant", "state", "token", "atomic"),
        signal(P.CREATIVE_DIRECTOR, "cd1", "Approved premium direction; reject generic defaults",
               0.9, "quality", "approved", "premium", "theme", "shadow"),
        signal(P.BUSINESS_STRATEGY, "b1", "Premium positioning; protect conversion via performance",
               0.9, "business", "positioning", "performance", "conversion"),
        signal(P.BRAND_STRATEGY, "br1", "Elegant restrained premium brand shapes colour and type",
               0.85, "brand", "color", "typography", "tone"),
        signal(P.PSYCHOLOGY, "p1", "Clear feedback states and calm motion build trust",
               0.9, "state", "motion", "feedback", "trust"),
        signal(P.UX_STRATEGY, "ux1", "WCAG AA contrast and keyboard operability everywhere",
               0.9, "accessibility", "contrast", "focus", "interaction", "motion"),
        signal(P.INFORMATION_ARCHITECTURE, "ia1", "Pages to cover; RTL reading direction supported",
               0.85, "structure", "page", "rtl", "direction"),
        signal(P.WIREFRAME, "w1", "Responsive grid, breakpoints, and spacing rhythm",
               0.9, "grid", "breakpoint", "spacing", "container", "layout"),
        signal(P.KNOWLEDGE, "k1", "Three-tier tokens, theming, and accessibility best-practice",
               0.85, "token", "theme", "accessibility", "design-system"),
    ]


@pytest.fixture
def request_factory():
    def _make(
        *,
        product_category: str = "skincare",
        platforms: tuple[Platform, ...] | None = None,
        directions: tuple[Direction, ...] = (Direction.LTR, Direction.RTL),
        dark_mode: bool = True,
        locales: tuple[str, ...] = ("en", "ar"),
        market: str = "premium",
    ) -> DesignSystemRequest:
        kwargs = {
            "product_category": product_category,
            "directions": directions,
            "dark_mode": dark_mode,
            "locales": locales,
        }
        if platforms is not None:
            kwargs["platforms"] = platforms
        brief = DesignSystemBrief(**kwargs)
        return DesignSystemRequest(
            brief=brief,
            project=ProjectContext(project_id="proj-x", platform="shopify_plus", market=market),
        )

    return _make


@pytest.fixture
def env_factory():
    """Build an in-memory environment whose input ports return the given signals."""

    def _make(signals_list=()):
        buckets: dict[ProvenanceKind, list[RawSignal]] = {p: [] for p in ProvenanceKind}
        for s in signals_list:
            buckets.setdefault(s.provenance, []).append(s)
        P = ProvenanceKind
        return build_in_memory_environment(
            design_language=InMemoryDesignLanguageInput(buckets[P.DESIGN_LANGUAGE]),
            component_intelligence=InMemoryComponentIntelligenceInput(
                buckets[P.COMPONENT_INTELLIGENCE]
            ),
            creative_director=InMemoryCreativeDirectorInput(buckets[P.CREATIVE_DIRECTOR]),
            business_strategy=InMemoryBusinessStrategyInput(buckets[P.BUSINESS_STRATEGY]),
            brand=InMemoryBrandInput(buckets[P.BRAND_STRATEGY]),
            psychology=InMemoryPsychologyInput(buckets[P.PSYCHOLOGY]),
            ux=InMemoryUXInput(buckets[P.UX_STRATEGY]),
            ia=InMemoryIAInput(buckets[P.INFORMATION_ARCHITECTURE]),
            wireframe=InMemoryWireframeInput(buckets[P.WIREFRAME]),
            knowledge=InMemoryKnowledgeAdvisor(buckets[P.KNOWLEDGE]),
            clock=FixedClock(),
        )

    return _make
