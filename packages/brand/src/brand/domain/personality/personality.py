"""Brand personality — the human traits and attributes the brand carries.

A :class:`BrandPersonality` names the traits the brand embodies and the
:class:`BrandAttribute` s that make it concrete (each attribute pairing what the brand
*is* with what it is *not*, the classic brand-attribute discipline). Cited.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandAttributeId, BrandEvidenceId
from brand.domain.shared.value_objects import Salience

__all__ = ["BrandAttribute", "BrandPersonality", "InvalidPersonalityError"]


class InvalidPersonalityError(DesignDirectorError):
    """Raised when brand personality is constructed with invalid data."""

    code = "invalid_brand_personality"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BrandAttribute:
    """One cited brand attribute, defined by what it is and is not.

    Attributes:
        id: Attribute identity.
        trait: What the brand is (e.g. "confident").
        opposite: What the brand is not (e.g. "arrogant") — the guardrail.
        salience: How prominent the attribute is.
        evidence_ids: The evidence supporting it.
    """

    id: BrandAttributeId
    trait: str
    opposite: str = ""
    salience: Salience = Salience(3)
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.trait or not self.trait.strip():
            raise InvalidPersonalityError("BrandAttribute.trait must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class BrandPersonality:
    """The cited personality the brand embodies.

    Attributes:
        traits: The personality traits, in a few words each.
        attributes: The defining brand attributes.
        summary: A one-line personality summary.
        evidence_ids: The evidence supporting it.
    """

    traits: tuple[str, ...] = ()
    attributes: tuple[BrandAttribute, ...] = ()
    summary: str = ""
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "traits", tuple(self.traits))
        object.__setattr__(self, "attributes", tuple(self.attributes))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @classmethod
    def build(
        cls,
        *,
        traits: Iterable[str] = (),
        attributes: Iterable[BrandAttribute] = (),
        summary: str = "",
        evidence_ids: Iterable[BrandEvidenceId] = (),
    ) -> BrandPersonality:
        return cls(
            traits=tuple(traits),
            attributes=tuple(attributes),
            summary=summary,
            evidence_ids=tuple(evidence_ids),
        )

    def all_evidence_ids(self) -> tuple[BrandEvidenceId, ...]:
        return (*self.evidence_ids, *(eid for a in self.attributes for eid in a.evidence_ids))
