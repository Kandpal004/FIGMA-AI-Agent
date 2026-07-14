"""The industry-preset knowledge base — the twelve supported industries, codified.

For each :class:`IndustryPreset` this encodes the primary language archetype that best serves
the category, the credible alternatives and *why each loses*, and a luxury bias. The designer
uses this to select a deliberate language and to record the considered-and-rejected
alternatives the spec requires.

Pure data over the shared value objects. No I/O, no framework.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_language.domain.shared.value_objects import IndustryPreset, LanguageArchetype

__all__ = ["IndustryLanguagePreset", "preset_for"]

_I = IndustryPreset
_A = LanguageArchetype


class UnknownIndustryError(DesignDirectorError):
    """Raised when no preset exists for an industry."""

    code = "design_language_unknown_industry"
    http_status = 422


@dataclass(frozen=True, slots=True)
class IndustryLanguagePreset:
    """The codified language guidance for one industry.

    Attributes:
        industry: The industry.
        primary: The archetype that best serves the category.
        alternatives: Credible alternatives paired with why each is rejected.
        luxury_bias: An adjustment to the DNA luxury level for the category.
    """

    industry: IndustryPreset
    primary: LanguageArchetype
    alternatives: tuple[tuple[LanguageArchetype, str], ...]
    luxury_bias: int = 0


_PRESETS: tuple[IndustryLanguagePreset, ...] = (
    IndustryLanguagePreset(_I.FASHION, _A.NIKE, (
        (_A.GYMSHARK, "less editorial restraint than the brand warrants"),
        (_A.LUXURY_FASHION, "too exclusive for the target tier"),
    )),
    IndustryLanguagePreset(_I.BEAUTY, _A.AESOP, (
        (_A.LUXURY_BEAUTY, "more overtly luxe than the brand warrants"),
        (_A.MINIMAL_EDITORIAL, "too austere for a sensorial category"),
    )),
    IndustryLanguagePreset(_I.LUXURY, _A.LUXURY_FASHION, (
        (_A.AESOP, "apothecary restraint rather than couture presence"),
        (_A.APPLE, "tech-precise rather than couture"),
    ), luxury_bias=1),
    IndustryLanguagePreset(_I.JEWELLERY, _A.LUXURY_FASHION, (
        (_A.LUXURY_BEAUTY, "sensorial rather than exhibited craft"),
        (_A.MINIMAL_EDITORIAL, "lacks the material warmth jewellery needs"),
    ), luxury_bias=1),
    IndustryLanguagePreset(_I.ELECTRONICS, _A.PREMIUM_ELECTRONICS, (
        (_A.DYSON, "engineering-forward rather than product-as-sculpture"),
        (_A.NOTHING, "signature quirk over broad premium appeal"),
    )),
    IndustryLanguagePreset(_I.FURNITURE, _A.MINIMAL_EDITORIAL, (
        (_A.AESOP, "apothecary rather than spatial editorial"),
        (_A.APPLE, "tech-precise rather than material-warm"),
    )),
    IndustryLanguagePreset(_I.SUPPLEMENTS, _A.PREMIUM_SUPPLEMENTS, (
        (_A.AESOP, "apothecary-luxury over accessible wellness"),
        (_A.APPLE, "too clinical and cool for wellness warmth"),
    )),
    IndustryLanguagePreset(_I.HEALTHCARE, _A.PREMIUM_SUPPLEMENTS, (
        (_A.ENTERPRISE_SAAS, "utilitarian over reassuring warmth"),
        (_A.APPLE, "too cool for the reassurance care demands"),
    )),
    IndustryLanguagePreset(_I.FOOD, _A.PREMIUM_SUPPLEMENTS, (
        (_A.AESOP, "too restrained for appetite appeal"),
        (_A.MATERIAL_3, "too systematic and loud for craft food"),
    )),
    IndustryLanguagePreset(_I.PET, _A.PREMIUM_SUPPLEMENTS, (
        (_A.GYMSHARK, "too aggressive for companionship warmth"),
        (_A.NOTION, "too neutral for playful warmth"),
    )),
    IndustryLanguagePreset(_I.B2B, _A.STRIPE, (
        (_A.LINEAR, "too dark and intense for broad enterprise trust"),
        (_A.ENTERPRISE_SAAS, "dependable but less crafted"),
    )),
    IndustryLanguagePreset(_I.MARKETPLACE, _A.SHOPIFY_POLARIS, (
        (_A.MATERIAL_3, "expressive over merchant-neutral"),
        (_A.STRIPE, "too premium-crafted for a broad marketplace"),
    )),
)

_BY_INDUSTRY: dict[IndustryPreset, IndustryLanguagePreset] = {
    p.industry: p for p in _PRESETS
}


def preset_for(industry: IndustryPreset) -> IndustryLanguagePreset:
    """Return the codified language preset for an industry."""
    preset = _BY_INDUSTRY.get(industry)
    if preset is None:  # pragma: no cover - all industries are defined
        raise UnknownIndustryError(
            f"No preset for industry {industry.value}.", details={"industry": industry.value}
        )
    return preset
