"""Tests for the Homepage Workflow input model (request.py)."""

from __future__ import annotations

from homepage_workflow.request import (
    BrandAssets,
    HomepageRequest,
    ProductCatalog,
)


def _full_request() -> HomepageRequest:
    return HomepageRequest(
        brand_name="Aesop",
        business_description="Premium botanical skincare for discerning customers.",
        product_catalog=ProductCatalog(
            product_category="skincare", categories=("cleansers", "serums"), product_count=48,
            hero_products=("Resurrection Hand Balm",),
        ),
        design_brief="A calm, editorial homepage that converts through trust and clarity.",
        website_url="https://aesop.com",
        competitor_urls=("https://glossier.com",),
        brand_assets=BrandAssets(logo="logo.svg", colors=("#0A0A0C",), fonts=("Suisse",)),
        descriptors=("premium", "minimal"),
        business_goals=("grow retention",),
        user_goals=("buy with confidence",),
    )


# --------------------------------------------------------------------------- #
# Validation                                                                   #
# --------------------------------------------------------------------------- #
def test_a_complete_request_is_valid():
    v = _full_request().validate()
    assert v.is_valid and not v.missing


def test_missing_required_inputs_are_reported_not_raised():
    req = HomepageRequest(brand_name="Aesop")  # no business_description / brief / catalog
    v = req.validate()
    assert not v.is_valid
    assert set(v.missing) == {"business_description", "design_brief", "product_catalog"}


def test_optional_gaps_produce_warnings_not_failure():
    req = HomepageRequest(
        brand_name="Aesop", business_description="Skincare.",
        product_catalog=ProductCatalog(product_category="skincare"), design_brief="Convert.",
    )
    v = req.validate()
    assert v.is_valid
    assert any("competitor" in w.lower() for w in v.warnings)
    assert any("brand assets" in w.lower() for w in v.warnings)


def test_invalid_urls_are_flagged():
    req = HomepageRequest(
        brand_name="Aesop", business_description="Skincare.",
        product_catalog=ProductCatalog(product_category="skincare"), design_brief="Convert.",
        website_url="not-a-url", competitor_urls=("ftp://x",),
    )
    v = req.validate()
    assert v.is_valid  # required inputs present
    assert any("website_url" in w for w in v.warnings)
    assert any("ftp://x" in w for w in v.warnings)


# --------------------------------------------------------------------------- #
# Brief round-trip                                                             #
# --------------------------------------------------------------------------- #
def test_brief_round_trips():
    req = _full_request()
    brief = req.to_brief()
    assert brief["brand_name"] == "Aesop"
    assert brief["product_category"] == "skincare"
    assert brief["industry"] == "skincare"  # resolved from catalog
    rebuilt = HomepageRequest.from_brief(brief)
    assert rebuilt.brand_name == req.brand_name
    assert rebuilt.product_catalog.product_category == "skincare"
    assert rebuilt.product_catalog.categories == ("cleansers", "serums")
    assert rebuilt.competitor_urls == ("https://glossier.com",)
    assert rebuilt.brand_assets.logo == "logo.svg"
    assert rebuilt.validate().is_valid


def test_resolved_industry_falls_back_to_category():
    req = HomepageRequest(
        brand_name="X", business_description="Y",
        product_catalog=ProductCatalog(product_category="footwear"), design_brief="Z",
    )
    assert req.resolved_industry == "footwear"
    req2 = HomepageRequest(
        brand_name="X", business_description="Y",
        product_catalog=ProductCatalog(product_category="footwear"), design_brief="Z",
        industry="fashion footwear",
    )
    assert req2.resolved_industry == "fashion footwear"


def test_to_json_includes_validation():
    doc = _full_request().to_json()
    assert doc["validation"]["is_valid"] is True
    assert doc["product_catalog"]["product_count"] == 48
