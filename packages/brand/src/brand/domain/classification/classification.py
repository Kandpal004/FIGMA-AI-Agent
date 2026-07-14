"""Brand classification — the register the whole system expresses.

A :class:`BrandClassification` places the brand within the thirteen
:class:`BrandCategory` s: a primary category (the dominant register) plus any
secondaries (a brand may be *Beauty × Premium × Minimal*), cited and with the
alternatives it was weighed against recorded. Classification is the keystone every
downstream creative and verbal choice must express.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId
from brand.domain.shared.value_objects import (
    BrandCategory,
    Confidence,
    ConsideredAlternative,
)

__all__ = ["BrandClassification", "InvalidClassificationError"]


class InvalidClassificationError(DesignDirectorError):
    """Raised when a classification is constructed with invalid data."""

    code = "invalid_brand_classification"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BrandClassification:
    """The cited placement of the brand within the category taxonomy.

    Attributes:
        primary: The dominant brand category.
        secondary: Supporting categories the brand also expresses.
        confidence: Confidence in the classification.
        rationale: Why this classification fits.
        considered: The classifications weighed and rejected.
        evidence_ids: The evidence supporting it.
    """

    primary: BrandCategory
    secondary: tuple[BrandCategory, ...] = ()
    confidence: Confidence = Confidence(0.7)
    rationale: str = ""
    considered: tuple[ConsideredAlternative, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        # Secondary categories are distinct and never repeat the primary.
        deduped: list[BrandCategory] = []
        for category in self.secondary:
            if category is not self.primary and category not in deduped:
                deduped.append(category)
        object.__setattr__(self, "secondary", tuple(deduped))
        object.__setattr__(self, "considered", tuple(self.considered))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def all_categories(self) -> tuple[BrandCategory, ...]:
        return (self.primary, *self.secondary)

    def expresses(self, category: BrandCategory) -> bool:
        return category is self.primary or category in self.secondary
