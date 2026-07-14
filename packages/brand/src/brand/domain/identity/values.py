"""Brand values — the principles the brand holds and acts on.

A :class:`BrandValue` is one cited principle with the behaviour that proves it; the
:class:`BrandValues` collection is the immutable set produced by identity synthesis.
Values are held, not decorative — each names how it shows up.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId, BrandValueId
from brand.domain.shared.value_objects import Priority

__all__ = ["BrandValue", "BrandValues", "InvalidValueError"]


class InvalidValueError(DesignDirectorError):
    """Raised when a brand value is constructed with invalid data."""

    code = "invalid_brand_value_principle"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BrandValue:
    """One cited brand value.

    Attributes:
        id: Value identity.
        name: The value's name (e.g. "Radical transparency").
        description: What the value means.
        behavior: How the value shows up in practice.
        priority: Its priority relative to other values.
        evidence_ids: The evidence supporting it.
    """

    id: BrandValueId
    name: str
    description: str
    behavior: str = ""
    priority: Priority = Priority(3)
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidValueError("BrandValue.name must be non-empty.")
        if not self.description or not self.description.strip():
            raise InvalidValueError("BrandValue.description must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class BrandValues:
    """An immutable set of brand values."""

    values: tuple[BrandValue, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", tuple(self.values))

    @classmethod
    def of(cls, values: Iterable[BrandValue]) -> BrandValues:
        return cls(values=tuple(values))

    def __len__(self) -> int:
        return len(self.values)

    def __iter__(self):
        return iter(self.values)

    def by_priority(self) -> tuple[BrandValue, ...]:
        return tuple(sorted(self.values, key=lambda v: int(v.priority), reverse=True))

    def evidence_ids(self) -> tuple[BrandEvidenceId, ...]:
        return tuple(eid for v in self.values for eid in v.evidence_ids)
