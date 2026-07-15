"""ComponentPurposes — the four reasons a component exists.

Every component the engine includes must earn its place on four axes at once: the business
purpose it advances, the user purpose it serves, the conversion purpose it drives, and the
trust purpose it reinforces. :class:`ComponentPurposes` bundles them so a component can never
be added purpose-blind — the structural realisation of "every component exists because it
improves a business outcome".

Pure domain: standard library, the shared-kernel error base, CI ids, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from component_intelligence.domain.shared.ids import CIEvidenceId

__all__ = ["ComponentPurposes", "InvalidPurposeError"]


class InvalidPurposeError(DesignDirectorError):
    """Raised when component purposes are constructed with invalid data."""

    code = "invalid_component_intelligence_purpose"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ComponentPurposes:
    """The business, user, conversion, and trust purposes a component serves.

    Attributes:
        business_purpose: The commercial reason the component exists.
        user_purpose: The user need it serves.
        conversion_purpose: The conversion outcome it drives.
        trust_purpose: The trust it reinforces.
        evidence_ids: The evidence grounding the purposes.
    """

    business_purpose: str
    user_purpose: str
    conversion_purpose: str
    trust_purpose: str
    evidence_ids: tuple[CIEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        for name in ("business_purpose", "user_purpose", "conversion_purpose", "trust_purpose"):
            value = getattr(self, name)
            if not value or not value.strip():
                raise InvalidPurposeError(f"ComponentPurposes.{name} must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
