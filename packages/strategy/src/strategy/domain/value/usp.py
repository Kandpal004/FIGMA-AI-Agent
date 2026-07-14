"""The unique selling proposition — the one defensible reason to choose this brand.

A :class:`UniqueSellingProposition` distils the single, defensible claim that no
competitor can make as credibly, together with what makes it defensible.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import StrategyEvidenceId

__all__ = ["InvalidUSPError", "UniqueSellingProposition"]


class InvalidUSPError(DesignDirectorError):
    """Raised when a USP is constructed with invalid data."""

    code = "invalid_usp"
    http_status = 422


@dataclass(frozen=True, slots=True)
class UniqueSellingProposition:
    """The cited, single defensible claim.

    Attributes:
        statement: The unique claim.
        defensibility: Why it is hard for competitors to copy.
        evidence_ids: The evidence supporting it.
    """

    statement: str
    defensibility: str = ""
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidUSPError("UniqueSellingProposition.statement must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
