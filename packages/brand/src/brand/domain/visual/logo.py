"""Logo direction — strategic intent for the brand mark (never a rendered logo).

A :class:`LogoDirection` states what the mark must express and the principles that
govern it — it does not draw the logo. Cited.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId

__all__ = ["InvalidLogoError", "LogoDirection"]


class InvalidLogoError(DesignDirectorError):
    """Raised when logo direction is constructed with invalid data."""

    code = "invalid_logo_direction"
    http_status = 422


@dataclass(frozen=True, slots=True)
class LogoDirection:
    """The cited strategic intent for the brand mark.

    Attributes:
        intent: What the mark must express.
        style: The stylistic register (e.g. "wordmark", "monogram", "combination").
        principles: The principles the mark must honour.
        avoid: Anti-patterns the mark must avoid.
        evidence_ids: The evidence supporting it.
    """

    intent: str
    style: str = ""
    principles: tuple[str, ...] = ()
    avoid: tuple[str, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.intent or not self.intent.strip():
            raise InvalidLogoError("LogoDirection.intent must be non-empty.")
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "avoid", tuple(self.avoid))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
