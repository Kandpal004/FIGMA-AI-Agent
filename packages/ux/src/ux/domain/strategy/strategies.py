"""The UX strategies — navigation, content, interaction, error recovery, disclosure, trust.

Six cited strategic value objects, grouped by :class:`UXStrategies`, that state *how* the
experience behaves at the level of principle (never layout): how the user navigates, how
content is prioritised, how interactions feel and give feedback, how errors are prevented
and recovered, how complexity is progressively disclosed, and where trust is established.

Pure domain: standard library, the shared-kernel error base, UX ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from ux.domain.shared.ids import UXEvidenceId
from ux.domain.shared.value_objects import (
    InteractionPattern,
    NavPattern,
)

__all__ = [
    "ContentStrategy",
    "ErrorRecoveryStrategy",
    "InteractionStrategy",
    "InvalidStrategyError",
    "NavigationStrategy",
    "ProgressiveDisclosureStrategy",
    "TrustStrategy",
    "UXStrategies",
]


class InvalidStrategyError(DesignDirectorError):
    """Raised when a UX strategy is constructed with invalid data."""

    code = "invalid_ux_strategy"
    http_status = 422


def _require(value: str, field: str) -> None:
    if not value or not value.strip():
        raise InvalidStrategyError(f"{field} must be non-empty.")


@dataclass(frozen=True, slots=True)
class NavigationStrategy:
    """How the user navigates (grounded in the mental model and Jakob's Law).

    Attributes:
        pattern: The overall navigation pattern.
        primary_nav: The primary navigation items.
        wayfinding: How the user always knows where they are.
        principles: Navigation principles to honour.
        evidence_ids: The evidence supporting it.
    """

    pattern: NavPattern
    primary_nav: tuple[str, ...] = ()
    wayfinding: str = ""
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "primary_nav", tuple(self.primary_nav))
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class ContentStrategy:
    """How content is prioritised and voiced.

    Attributes:
        hierarchy_intent: How content hierarchy should feel across pages.
        leads_with: What content leads across the experience.
        principles: Content principles to honour.
        evidence_ids: The evidence supporting it.
    """

    hierarchy_intent: str
    leads_with: tuple[str, ...] = ()
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        _require(self.hierarchy_intent, "ContentStrategy.hierarchy_intent")
        object.__setattr__(self, "leads_with", tuple(self.leads_with))
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class InteractionStrategy:
    """How interactions feel and give feedback.

    Attributes:
        patterns: The interaction patterns to use.
        feedback_intent: How the system should acknowledge user action.
        principles: Interaction principles to honour.
        evidence_ids: The evidence supporting it.
    """

    patterns: tuple[InteractionPattern, ...] = ()
    feedback_intent: str = ""
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "patterns", tuple(self.patterns))
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class ErrorRecoveryStrategy:
    """How errors are prevented and recovered (Nielsen error heuristics).

    Attributes:
        prevention: How errors are prevented before they happen.
        recovery: How the user recovers when an error occurs.
        principles: Error-handling principles to honour.
        evidence_ids: The evidence supporting it.
    """

    prevention: tuple[str, ...] = ()
    recovery: tuple[str, ...] = ()
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "prevention", tuple(self.prevention))
        object.__setattr__(self, "recovery", tuple(self.recovery))
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class ProgressiveDisclosureStrategy:
    """How complexity is revealed progressively (Tesler's Law, Miller's Law).

    Attributes:
        reveal_first: What is shown up front.
        reveal_on_demand: What is revealed only when the user needs it.
        principles: Disclosure principles to honour.
        evidence_ids: The evidence supporting it.
    """

    reveal_first: tuple[str, ...] = ()
    reveal_on_demand: tuple[str, ...] = ()
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "reveal_first", tuple(self.reveal_first))
        object.__setattr__(self, "reveal_on_demand", tuple(self.reveal_on_demand))
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class TrustStrategy:
    """Where trust is established across the experience.

    Attributes:
        trust_moments: The moments where trust must be established.
        signals: The trust signals to deploy.
        principles: Trust principles to honour.
        evidence_ids: The evidence supporting it.
    """

    trust_moments: tuple[str, ...] = ()
    signals: tuple[str, ...] = ()
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "trust_moments", tuple(self.trust_moments))
        object.__setattr__(self, "signals", tuple(self.signals))
        object.__setattr__(self, "principles", tuple(self.principles))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class UXStrategies:
    """The six cited UX strategies, grouped."""

    navigation: NavigationStrategy
    content: ContentStrategy
    interaction: InteractionStrategy
    error_recovery: ErrorRecoveryStrategy
    disclosure: ProgressiveDisclosureStrategy
    trust: TrustStrategy

    def evidence_ids(self) -> tuple[UXEvidenceId, ...]:
        return (
            *self.navigation.evidence_ids,
            *self.content.evidence_ids,
            *self.interaction.evidence_ids,
            *self.error_recovery.evidence_ids,
            *self.disclosure.evidence_ids,
            *self.trust.evidence_ids,
        )
