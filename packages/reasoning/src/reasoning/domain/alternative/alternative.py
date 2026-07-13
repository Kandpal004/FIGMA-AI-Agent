"""The Alternative-Strategy model — the roads not taken, deterministically.

The engine does not commit to a single strategy blindly; it reasons the same
inputs under other :class:`StrategyStance` s and records how each would differ. An
:class:`AlternativeStrategy` is a *summary* of one such road not taken — its stance,
what it would change, why it was not chosen, and its confidence — deliberately a
lightweight description rather than a full nested strategy (to keep the aggregate
bounded and free of recursion).

Pure domain: standard library, the shared-kernel error base, reasoning ids, and
the confidence + stance value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from reasoning.domain.confidence.confidence import ConfidenceScore
from reasoning.domain.shared.ids import AlternativeId
from reasoning.domain.shared.value_objects import StrategyStance

__all__ = ["AlternativeStrategy", "InvalidAlternativeError"]


class InvalidAlternativeError(DesignDirectorError):
    """Raised when an alternative strategy is constructed with invalid data."""

    code = "invalid_alternative"
    http_status = 422


@dataclass(frozen=True, slots=True)
class AlternativeStrategy:
    """A summary of a strategy the engine would have produced under a different stance.

    Attributes:
        id: Alternative identity.
        stance: The stance this alternative reasons under.
        summary: A short description of the alternative's thrust.
        key_differences: The concrete ways it would differ from the chosen strategy.
        why_not_chosen: Why the chosen stance prevailed over this one.
        confidence: The confidence this alternative would carry.
    """

    id: AlternativeId
    stance: StrategyStance
    summary: str
    confidence: ConfidenceScore
    key_differences: tuple[str, ...] = ()
    why_not_chosen: str = ""

    def __post_init__(self) -> None:
        if not self.summary or not self.summary.strip():
            raise InvalidAlternativeError("AlternativeStrategy.summary must be non-empty.")
        object.__setattr__(self, "key_differences", tuple(self.key_differences))
