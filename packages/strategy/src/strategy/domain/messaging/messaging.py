"""The messaging framework — the themes the brand communicates.

A :class:`MessagingFramework` is a primary message plus the cited
:class:`MessagingPillar` s that support it. Each pillar carries a theme, its message,
and supporting points. This decides *what* to say and *why*; it never writes final
copy.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import MessagingPillarId, StrategyEvidenceId

__all__ = ["InvalidMessagingError", "MessagingFramework", "MessagingPillar"]


class InvalidMessagingError(DesignDirectorError):
    """Raised when messaging is constructed with invalid data."""

    code = "invalid_messaging"
    http_status = 422


@dataclass(frozen=True, slots=True)
class MessagingPillar:
    """One cited messaging pillar.

    Attributes:
        id: Pillar identity.
        theme: The theme it communicates.
        message: The core message of the theme.
        supporting_points: The points that substantiate the message.
        evidence_ids: The evidence supporting it.
    """

    id: MessagingPillarId
    theme: str
    message: str
    supporting_points: tuple[str, ...] = ()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.theme or not self.theme.strip():
            raise InvalidMessagingError("MessagingPillar.theme must be non-empty.")
        if not self.message or not self.message.strip():
            raise InvalidMessagingError("MessagingPillar.message must be non-empty.")
        object.__setattr__(self, "supporting_points", tuple(self.supporting_points))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class MessagingFramework:
    """The cited messaging framework."""

    primary_message: str
    pillars: tuple[MessagingPillar, ...] = ()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.primary_message or not self.primary_message.strip():
            raise InvalidMessagingError("MessagingFramework.primary_message must be non-empty.")
        object.__setattr__(self, "pillars", tuple(self.pillars))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @classmethod
    def build(
        cls,
        primary_message: str,
        *,
        pillars: Iterable[MessagingPillar] = (),
        evidence_ids: Iterable[StrategyEvidenceId] = (),
    ) -> MessagingFramework:
        return cls(
            primary_message=primary_message,
            pillars=tuple(pillars),
            evidence_ids=tuple(evidence_ids),
        )

    def all_evidence_ids(self) -> tuple[StrategyEvidenceId, ...]:
        return (*self.evidence_ids, *(eid for p in self.pillars for eid in p.evidence_ids))
