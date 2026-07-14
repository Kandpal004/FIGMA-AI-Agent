"""The Ideal Customer Profile — the qualifying definition of who to serve.

An :class:`IdealCustomerProfile` sharpens the personas into a decision rule: the
segments to target, the graphic attributes that define them, the signals that qualify
a prospect, and the ones that disqualify. It is cited and singular per report.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import StrategyEvidenceId

__all__ = ["IdealCustomerProfile", "InvalidICPError"]


class InvalidICPError(DesignDirectorError):
    """Raised when an ICP is constructed with invalid data."""

    code = "invalid_icp"
    http_status = 422


@dataclass(frozen=True, slots=True)
class IdealCustomerProfile:
    """The cited, qualifying definition of the ideal customer.

    Attributes:
        summary: A one-line statement of who the ideal customer is.
        segments: The target segments.
        attributes: The defining graphic attributes (e.g. "shops on mobile").
        qualifying_signals: Signals that a prospect is a good fit.
        disqualifiers: Signals that a prospect is a poor fit.
        evidence_ids: The evidence supporting the profile.
    """

    summary: str
    segments: tuple[str, ...] = ()
    attributes: tuple[str, ...] = ()
    qualifying_signals: tuple[str, ...] = ()
    disqualifiers: tuple[str, ...] = ()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.summary or not self.summary.strip():
            raise InvalidICPError("IdealCustomerProfile.summary must be non-empty.")
        object.__setattr__(self, "segments", tuple(self.segments))
        object.__setattr__(self, "attributes", tuple(self.attributes))
        object.__setattr__(self, "qualifying_signals", tuple(self.qualifying_signals))
        object.__setattr__(self, "disqualifiers", tuple(self.disqualifiers))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
