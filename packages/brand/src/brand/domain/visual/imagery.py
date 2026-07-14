"""Imagery direction — strategic intent for photography and illustration.

:class:`PhotographyDirection` and :class:`IllustrationDirection` state the treatment,
subject, and mood imagery must carry — they specify no assets, crops, or filters (that
is a later phase). Cited.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId
from brand.domain.shared.value_objects import IllustrationStyle, PhotoTreatment

__all__ = [
    "IllustrationDirection",
    "InvalidImageryError",
    "PhotographyDirection",
]


class InvalidImageryError(DesignDirectorError):
    """Raised when imagery direction is constructed with invalid data."""

    code = "invalid_imagery_direction"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PhotographyDirection:
    """The cited strategic intent for photography.

    Attributes:
        treatment: The photographic treatment.
        subject_focus: What the photography centres on.
        mood: The mood the photography must carry.
        principles: Photographic principles to honour.
        evidence_ids: The evidence supporting it.
    """

    treatment: PhotoTreatment
    subject_focus: str = ""
    mood: str = ""
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class IllustrationDirection:
    """The cited strategic intent for illustration (``NONE`` when not used).

    Attributes:
        style: The illustration style.
        role: What role illustration plays for the brand.
        principles: Illustration principles to honour.
        evidence_ids: The evidence supporting it.
    """

    style: IllustrationStyle
    role: str = ""
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
