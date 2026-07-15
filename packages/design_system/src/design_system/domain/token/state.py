"""State tokens — the token deltas that express each interaction state.

Every interactive component must express the ten UI states (default, hover, focus, active,
disabled, loading, empty, error, success, warning). Rather than hard-code visuals per component,
the design system defines each state once as a set of semantic token keys the state activates
(e.g. ``HOVER`` → ``{"bg": "color.action.primary.hover", "shadow": "shadow.md"}``). Component
specs then reference these state definitions, guaranteeing every state is expressed in tokens
and consistent system-wide.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from design_system.domain.shared.value_objects import StateKind

__all__ = ["InvalidStateTokensError", "StateTokens"]


class InvalidStateTokensError(DesignDirectorError):
    """Raised when state tokens are constructed with invalid data."""

    code = "invalid_design_system_state_tokens"
    http_status = 422


@dataclass(frozen=True, slots=True)
class StateTokens:
    """The semantic token keys a single interaction state activates.

    Attributes:
        state: Which state this describes.
        token_refs: A mapping of visual slot (``"bg"``, ``"fg"``, ``"border"``, ``"shadow"``,
            ``"opacity"``, …) to the semantic token key that slot resolves to in this state.
            May be empty only for ``DEFAULT`` inheritance, but must be non-empty otherwise.
    """

    state: StateKind
    token_refs: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        refs = {
            slot.strip().lower(): ref.strip().lower()
            for slot, ref in self.token_refs.items()
            if slot and slot.strip() and ref and ref.strip()
        }
        if self.state is not StateKind.DEFAULT and not refs:
            raise InvalidStateTokensError(
                "A non-default state must activate at least one token.",
                details={"state": self.state.value},
            )
        object.__setattr__(self, "token_refs", MappingProxyType(refs))

    @property
    def token_keys(self) -> tuple[str, ...]:
        return tuple(self.token_refs.values())
