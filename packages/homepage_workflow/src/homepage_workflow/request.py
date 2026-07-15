"""The Homepage Workflow input model — every supported input, and how it is validated.

A :class:`HomepageRequest` captures everything a caller can supply to design a homepage: the four
required inputs (brand name, business description, product catalog, design brief) and the four
optional enrichments (website URL, competitor URLs, brand assets, an existing Figma file). It is a
plain, immutable input DTO — not an engine or abstraction — with two jobs:

* :meth:`HomepageRequest.validate` reports whether the request is complete enough to run, without
  raising, so the workflow's *Validate Inputs* step can pause the run (``NEEDS_INPUT``) and tell the
  caller exactly what is missing.
* :meth:`HomepageRequest.to_brief` projects the request into the neutral ``brief`` mapping the
  Director run carries and the engine executor reads, and :meth:`HomepageRequest.from_brief`
  reconstructs it — so the request round-trips through the Director without the domain importing it.

Pure input data: standard library and the shared-kernel error base only.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

__all__ = [
    "BrandAssets",
    "HomepageRequest",
    "InvalidHomepageRequestError",
    "ProductCatalog",
    "RequestValidation",
]


class InvalidHomepageRequestError(DesignDirectorError):
    """Raised when a homepage request carries structurally invalid data."""

    code = "invalid_homepage_request"
    http_status = 422


def _clean(values: Iterable[str] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, str):
        return (values.strip(),) if values.strip() else ()
    return tuple(str(v).strip() for v in values if str(v).strip())


def _is_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


# --------------------------------------------------------------------------- #
# Product catalog                                                              #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class ProductCatalog:
    """The product catalog the homepage merchandises.

    Attributes:
        product_category: The primary product/offer category (e.g. "skincare").
        categories: The catalog's top-level categories.
        product_count: The approximate number of products (0 if unknown).
        hero_products: Names/handles of hero products to feature.
    """

    product_category: str = ""
    categories: tuple[str, ...] = ()
    product_count: int = 0
    hero_products: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "product_category", self.product_category.strip())
        object.__setattr__(self, "categories", _clean(self.categories))
        object.__setattr__(self, "hero_products", _clean(self.hero_products))
        if not isinstance(self.product_count, int) or self.product_count < 0:
            raise InvalidHomepageRequestError("ProductCatalog.product_count must be an int >= 0.")

    @property
    def is_present(self) -> bool:
        return bool(self.product_category)

    def to_json(self) -> dict[str, object]:
        return {
            "product_category": self.product_category,
            "categories": list(self.categories),
            "product_count": self.product_count,
            "hero_products": list(self.hero_products),
        }


# --------------------------------------------------------------------------- #
# Brand assets                                                                 #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class BrandAssets:
    """Optional brand assets that ground the design.

    Attributes:
        logo: A reference to the brand logo (URL or asset id).
        colors: The brand colour palette (hex or names).
        fonts: The brand fonts.
        imagery_style: A short description of the brand's imagery style.
    """

    logo: str = ""
    colors: tuple[str, ...] = ()
    fonts: tuple[str, ...] = ()
    imagery_style: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "logo", self.logo.strip())
        object.__setattr__(self, "colors", _clean(self.colors))
        object.__setattr__(self, "fonts", _clean(self.fonts))
        object.__setattr__(self, "imagery_style", self.imagery_style.strip())

    @property
    def is_present(self) -> bool:
        return bool(self.logo or self.colors or self.fonts or self.imagery_style)

    def to_json(self) -> dict[str, object]:
        return {
            "logo": self.logo,
            "colors": list(self.colors),
            "fonts": list(self.fonts),
            "imagery_style": self.imagery_style,
        }


# --------------------------------------------------------------------------- #
# Validation result                                                            #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class RequestValidation:
    """The outcome of validating a homepage request.

    Attributes:
        is_valid: Whether every required input is present.
        missing: The required inputs that are missing.
        warnings: Non-blocking notes (e.g. optional enrichments not supplied).
    """

    is_valid: bool
    missing: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_json(self) -> dict[str, object]:
        return {
            "is_valid": self.is_valid,
            "missing": list(self.missing),
            "warnings": list(self.warnings),
        }


# --------------------------------------------------------------------------- #
# The homepage request                                                         #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class HomepageRequest:
    """Everything a caller supplies to design a homepage.

    The four required inputs are ``brand_name``, ``business_description``, ``product_catalog`` and
    ``design_brief``; the rest are optional enrichments or engine hints. Required fields are *not*
    enforced at construction — completeness is reported by :meth:`validate` so the Validate Inputs
    step can gate the run and report exactly what is missing.

    Attributes:
        brand_name: The brand's name (required).
        business_description: What the business is and does (required).
        product_catalog: The catalog to merchandise (required).
        design_brief: The design brief / goals for the homepage (required).
        website_url: The brand's current website, if any (optional).
        competitor_urls: Competitor sites to analyse (optional).
        brand_assets: Existing brand assets (optional).
        existing_figma_file: A reference to an existing Figma file to build on (optional).
        industry: The brand's industry (defaults to the product category).
        market: The market segment (e.g. "premium").
        platform: The commerce platform (e.g. "shopify_plus").
        business_goals: The business goals the homepage must serve.
        user_goals: The user goals the homepage must serve.
        descriptors: Brand descriptors (e.g. "premium", "minimal").
    """

    brand_name: str = ""
    business_description: str = ""
    product_catalog: ProductCatalog = field(default_factory=ProductCatalog)
    design_brief: str = ""
    website_url: str = ""
    competitor_urls: tuple[str, ...] = ()
    brand_assets: BrandAssets = field(default_factory=BrandAssets)
    existing_figma_file: str = ""
    industry: str = ""
    market: str = "premium"
    platform: str = "shopify_plus"
    business_goals: tuple[str, ...] = ()
    user_goals: tuple[str, ...] = ()
    descriptors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "brand_name", self.brand_name.strip())
        object.__setattr__(self, "business_description", self.business_description.strip())
        object.__setattr__(self, "design_brief", self.design_brief.strip())
        object.__setattr__(self, "website_url", self.website_url.strip())
        object.__setattr__(self, "existing_figma_file", self.existing_figma_file.strip())
        object.__setattr__(self, "competitor_urls", _clean(self.competitor_urls))
        object.__setattr__(self, "industry", self.industry.strip())
        object.__setattr__(self, "market", self.market.strip() or "premium")
        object.__setattr__(self, "platform", self.platform.strip() or "shopify_plus")
        object.__setattr__(self, "business_goals", _clean(self.business_goals))
        object.__setattr__(self, "user_goals", _clean(self.user_goals))
        object.__setattr__(self, "descriptors", _clean(self.descriptors))

    # -- validation -------------------------------------------------------- #
    def validate(self) -> RequestValidation:
        """Report whether the request is complete enough to run (never raises)."""
        missing: list[str] = []
        if not self.brand_name:
            missing.append("brand_name")
        if not self.business_description:
            missing.append("business_description")
        if not self.design_brief:
            missing.append("design_brief")
        if not self.product_catalog.is_present:
            missing.append("product_catalog")

        warnings: list[str] = []
        if self.website_url and not _is_url(self.website_url):
            warnings.append("website_url is not a valid http(s) URL and will be ignored.")
        for url in self.competitor_urls:
            if not _is_url(url):
                warnings.append(f"competitor URL {url!r} is not a valid http(s) URL.")
        if not self.competitor_urls:
            warnings.append("No competitor URLs supplied; competitor analysis uses market defaults.")
        if not self.brand_assets.is_present:
            warnings.append("No brand assets supplied; the design language will originate them.")

        return RequestValidation(
            is_valid=not missing, missing=tuple(missing), warnings=tuple(warnings)
        )

    @property
    def resolved_industry(self) -> str:
        return self.industry or self.product_catalog.product_category

    # -- brief round-trip -------------------------------------------------- #
    def to_brief(self) -> dict[str, object]:
        """Project the request into the neutral run ``brief`` mapping the executor reads."""
        return {
            "brand_name": self.brand_name,
            "business_description": self.business_description,
            "design_brief": self.design_brief,
            "product_category": self.product_catalog.product_category,
            "product_catalog": self.product_catalog.to_json(),
            "website_url": self.website_url,
            "competitor_urls": list(self.competitor_urls),
            "brand_assets": self.brand_assets.to_json(),
            "existing_figma_file": self.existing_figma_file,
            "industry": self.resolved_industry,
            "market": self.market,
            "platform": self.platform,
            "business_goals": list(self.business_goals),
            "user_goals": list(self.user_goals),
            "descriptors": list(self.descriptors),
        }

    @classmethod
    def from_brief(cls, brief: Mapping[str, object]) -> HomepageRequest:
        """Reconstruct a request from the Director run's ``brief`` mapping."""
        catalog_raw = brief.get("product_catalog")
        if isinstance(catalog_raw, Mapping):
            catalog = ProductCatalog(
                product_category=str(catalog_raw.get("product_category", "")),
                categories=_clean(catalog_raw.get("categories")),
                product_count=int(catalog_raw.get("product_count", 0) or 0),
                hero_products=_clean(catalog_raw.get("hero_products")),
            )
        else:
            catalog = ProductCatalog(product_category=str(brief.get("product_category", "")))

        assets_raw = brief.get("brand_assets")
        if isinstance(assets_raw, Mapping):
            assets = BrandAssets(
                logo=str(assets_raw.get("logo", "")),
                colors=_clean(assets_raw.get("colors")),
                fonts=_clean(assets_raw.get("fonts")),
                imagery_style=str(assets_raw.get("imagery_style", "")),
            )
        else:
            assets = BrandAssets()

        return cls(
            brand_name=str(brief.get("brand_name", "")),
            business_description=str(brief.get("business_description", "")),
            product_catalog=catalog,
            design_brief=str(brief.get("design_brief", "")),
            website_url=str(brief.get("website_url", "")),
            competitor_urls=_clean(brief.get("competitor_urls")),
            brand_assets=assets,
            existing_figma_file=str(brief.get("existing_figma_file", "")),
            industry=str(brief.get("industry", "")),
            market=str(brief.get("market", "") or "premium"),
            platform=str(brief.get("platform", "") or "shopify_plus"),
            business_goals=_clean(brief.get("business_goals")),
            user_goals=_clean(brief.get("user_goals")),
            descriptors=_clean(brief.get("descriptors")),
        )

    def to_json(self) -> dict[str, object]:
        doc = self.to_brief()
        doc["validation"] = self.validate().to_json()
        return doc
