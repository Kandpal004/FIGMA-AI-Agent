"""Shared fixtures for the Reasoning Engine test suite."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from reasoning.application.ports.knowledge_advisor import AdvisedPrinciple
from reasoning.domain.request.request import ReasoningRequest
from reasoning.domain.shared.value_objects import ReasoningDimension as D, StrategyStance
from reasoning.infrastructure.container import (
    ReasoningEnvironment,
    build_in_memory_environment,
)
from reasoning.infrastructure.inmemory import Clock, InMemoryKnowledgeAdvisor


class FixedClock(Clock):
    def now(self) -> datetime:
        return datetime(2026, 7, 13, 12, 0, 0, tzinfo=UTC)


def _p(kid: str, title: str, statement: str, conf: float = 0.85) -> AdvisedPrinciple:
    return AdvisedPrinciple(
        knowledge_id=kid, entry_version_id=f"{kid}-v1", category="cat",
        title=title, statement=statement, source_name="src", confidence=conf, relevance="rel",
    )


def full_script() -> dict:
    return {
        D.BUSINESS: [_p("b", "AOV", "Grow average order value.")],
        D.CUSTOMER: [_p("c", "Shopper", "Design-led shopper.")],
        D.TARGET_MARKET: [_p("m", "Premium", "Affluent buyers.")],
        D.CUSTOMER_PROBLEMS: [_p("pr", "Overload", "Choice overload.")],
        D.OBJECTIONS: [_p("ob", "Price", "Is it worth it?")],
        D.EMOTIONAL_TRIGGERS: [_p("em", "Belonging", "Curated taste.")],
        D.TRUST_MECHANISMS: [_p("tr", "Reviews", "Verified reviews.")],
        D.CONVERSION: [_p("cv1", "CTA", "One prominent CTA.", 0.9), _p("cv2", "Urgency", "Scarcity converts.", 0.7)],
        D.USER_EXPERIENCE: [_p("ux", "Fitts", "Big close targets.", 0.9)],
        D.ACCESSIBILITY: [_p("a", "Contrast", "4.5:1 contrast.", 0.95)],
        D.PLATFORM_CONSTRAINTS: [_p("pf", "Locked", "Checkout locked.", 0.9)],
        D.COMPETITIVE: [_p("cp", "Aesop", "Study Aesop.")],
        D.DESIGN_SYSTEM: [_p("ds", "Editorial", "Restrained editorial system.")],
        D.TYPOGRAPHY: [_p("ty", "Serif", "High-contrast serif.")],
        D.SPACING: [_p("sp", "Generous", "Generous whitespace.")],
        D.VISUAL_HIERARCHY: [_p("vh", "Focal", "One focal point.")],
        D.STRUCTURE: [_p("st1", "Gallery", "Gallery anchors PDP."), _p("st2", "Buy Box", "Buy box holds CTA.")],
        D.CREATIVE_REVIEW: [_p("cr", "CTA review", "Review CTA vs brand.")],
    }


@pytest.fixture
def request_pdp() -> ReasoningRequest:
    return ReasoningRequest(
        user_request="Design a premium PDP", project_id="p1", section_id="s1",
        page_type="product", platform="shopify_plus", goal="increase add-to-cart",
        stance=StrategyStance.BRAND_FIRST,
    )


@pytest.fixture
def env_factory():
    def _make(script: dict | None = None) -> ReasoningEnvironment:
        advisor = InMemoryKnowledgeAdvisor(script if script is not None else full_script())
        return build_in_memory_environment(advisor, clock=FixedClock())

    return _make


@pytest.fixture
def full_script_dict() -> dict:
    """A fresh copy of the full advisor script, for tests that mutate it."""
    return full_script()
