"""Shared fixtures for the Homepage Design Workflow test suite."""

from __future__ import annotations

import pytest

from homepage_workflow.composition import build_homepage_environment
from homepage_workflow.runner import HomepageWorkflowRunner


@pytest.fixture
def brief() -> dict[str, object]:
    """A realistic homepage design brief."""
    return {
        "product_category": "skincare",
        "brand_name": "Aesop",
        "industry": "beauty skincare",
        "market": "premium",
        "descriptors": ["premium", "minimal"],
        "business_goals": ["grow retention", "increase AOV"],
        "user_goals": ["buy with confidence"],
    }


@pytest.fixture
async def homepage_env():
    """A freshly wired homepage environment (all real engines)."""
    return await build_homepage_environment()


@pytest.fixture
def runner(homepage_env) -> HomepageWorkflowRunner:
    """A runner over the wired homepage environment."""
    return HomepageWorkflowRunner(homepage_env)
