"""Brand purpose — mission, vision, and promise.

The three purpose statements: the :class:`BrandMission` (why the brand exists, now),
the :class:`BrandVision` (the future it is working toward), and the
:class:`BrandPromise` (what every customer can always count on). Each is cited.

Pure domain: standard library, the shared-kernel error base, brand ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from brand.domain.shared.ids import BrandEvidenceId

__all__ = [
    "BrandMission",
    "BrandPromise",
    "BrandVision",
    "InvalidPurposeError",
]


class InvalidPurposeError(DesignDirectorError):
    """Raised when a purpose statement is constructed with invalid data."""

    code = "invalid_brand_purpose"
    http_status = 422


def _require(value: str, field: str) -> None:
    if not value or not value.strip():
        raise InvalidPurposeError(f"{field} must be non-empty.")


@dataclass(frozen=True, slots=True)
class BrandMission:
    """Why the brand exists, today.

    Attributes:
        statement: The mission statement.
        evidence_ids: The evidence supporting it.
    """

    statement: str
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.statement, "BrandMission.statement")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class BrandVision:
    """The future the brand is working toward.

    Attributes:
        statement: The vision statement.
        horizon: The time horizon it looks to.
        evidence_ids: The evidence supporting it.
    """

    statement: str
    horizon: str = ""
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.statement, "BrandVision.statement")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class BrandPromise:
    """What every customer can always count on.

    Attributes:
        statement: The promise statement.
        proof_points: Why the promise is credible.
        evidence_ids: The evidence supporting it.
    """

    statement: str
    proof_points: tuple[str, ...] = ()
    evidence_ids: tuple[BrandEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.statement, "BrandPromise.statement")
        object.__setattr__(self, "proof_points", tuple(self.proof_points))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
