"""The knowledge taxonomy: categories and subcategories.

:class:`KnowledgeCategory` is the top-level classification of every entry — the
seventeen domains the Knowledge Engine covers, verbatim from the product's
requirements. :class:`Subcategory` is a normalized, curated refinement within a
category (e.g. ``"fitts-law"`` under ``UX_LAWS``).

Pure domain: standard library plus the shared-kernel error base only.

Testing considerations
----------------------
* There are exactly seventeen categories and each resolves by value.
* :class:`Subcategory` normalizes case/whitespace and rejects empties.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Self

from core.errors import DesignDirectorError

__all__ = ["InvalidTaxonomyError", "KnowledgeCategory", "Subcategory"]


class InvalidTaxonomyError(DesignDirectorError):
    """Raised when a taxonomy value is invalid."""

    code = "invalid_taxonomy"
    http_status = 422


class KnowledgeCategory(str, Enum):
    """The top-level classification of a knowledge entry (seventeen domains).

    The string value is the stable identifier used in persistence, queries, and
    logs, and must never change once released.
    """

    BUSINESS = "business"
    CUSTOMER_PSYCHOLOGY = "customer_psychology"
    CONVERSION_OPTIMIZATION = "conversion_optimization"
    UX_LAWS = "ux_laws"
    DESIGN_PRINCIPLES = "design_principles"
    TYPOGRAPHY = "typography"
    SPACING = "spacing"
    COLOR_THEORY = "color_theory"
    VISUAL_HIERARCHY = "visual_hierarchy"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    SEO = "seo"
    SHOPIFY_PLUS = "shopify_plus"
    MAGENTO = "magento"
    DESIGN_SYSTEM = "design_system"
    CREATIVE_DIRECTION = "creative_direction"
    COMPETITOR_INTELLIGENCE = "competitor_intelligence"


_SUBCATEGORY_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class Subcategory:
    """A normalized refinement within a :class:`KnowledgeCategory`.

    Normalized like a slug (lower case, internal whitespace collapsed to a single
    hyphen) so ``Subcategory("Fitts Law")`` and ``Subcategory("fitts law")`` are
    equal.

    Attributes:
        value: The normalized subcategory slug.
    """

    value: str

    def __post_init__(self) -> None:
        normalized = _SUBCATEGORY_WHITESPACE.sub("-", self.value.strip().lower())
        if not normalized:
            raise InvalidTaxonomyError("Subcategory must be non-empty.")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, value: str) -> Self:
        """Construct a normalized subcategory."""
        return cls(value=value)
