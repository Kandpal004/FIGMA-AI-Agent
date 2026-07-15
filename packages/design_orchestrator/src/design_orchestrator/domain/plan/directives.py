"""The per-section directives — responsive, animation, accessibility, performance.

Where :mod:`choice` records *what* a section looks like, these value objects record *how it
behaves* — again by selecting from what the Design System (P16) already specified, never by
inventing:

* :class:`ResponsiveDirective` — how a section adapts across breakpoints (mobile-first).
* :class:`AnimationDirective` — which motion duration/easing tokens drive an entrance, and its
  trigger.
* :class:`AccessibilityDirective` — the role, minimum contrast, keyboard set, and focus rule.
* :class:`PerformanceDirective` — lazy-loading, load priority, and LCP participation.

These become the ``APPLY_RESPONSIVE`` / ``APPLY_ACCESSIBILITY`` execution steps and the
responsive/animation/accessibility/performance plans the aggregate carries.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from design_orchestrator.domain.shared.value_objects import Breakpoint

__all__ = [
    "AccessibilityDirective",
    "AnimationDirective",
    "InvalidDirectiveError",
    "PerformanceDirective",
    "ResponsiveDirective",
]

_TOKEN_KEY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")


class InvalidDirectiveError(DesignDirectorError):
    """Raised when a section directive is constructed with invalid data."""

    code = "invalid_design_orchestrator_directive"
    http_status = 422


def _token_key(key: str, what: str) -> str:
    normalized = key.strip().lower()
    if not _TOKEN_KEY.match(normalized):
        raise InvalidDirectiveError(
            f"{what} must reference a dotted token key; got {key!r}.", details={"key": key}
        )
    return normalized


@dataclass(frozen=True, slots=True)
class ResponsiveDirective:
    """How a section adapts across the responsive breakpoints.

    Attributes:
        behavior: A mapping of breakpoint to a short behavioural note. Must be mobile-first
            (define ``MOBILE``).
    """

    behavior: Mapping[Breakpoint, str] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        data = {bp: note.strip() for bp, note in self.behavior.items() if note and note.strip()}
        if Breakpoint.MOBILE not in data:
            raise InvalidDirectiveError(
                "ResponsiveDirective must be mobile-first (define MOBILE behaviour)."
            )
        object.__setattr__(self, "behavior", MappingProxyType(data))

    @property
    def bands(self) -> tuple[Breakpoint, ...]:
        return tuple(self.behavior.keys())


@dataclass(frozen=True, slots=True)
class AnimationDirective:
    """Which motion tokens drive a section's entrance, and its trigger.

    Attributes:
        duration_token: The motion-duration token key.
        easing_token: The motion-easing token key.
        trigger: What triggers the animation (e.g. "on-scroll", "on-load", "none").
    """

    duration_token: str
    easing_token: str
    trigger: str = "on-scroll"

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "duration_token", _token_key(self.duration_token, "AnimationDirective.duration")
        )
        object.__setattr__(
            self, "easing_token", _token_key(self.easing_token, "AnimationDirective.easing")
        )
        if not self.trigger or not self.trigger.strip():
            raise InvalidDirectiveError("AnimationDirective.trigger must be non-empty.")
        object.__setattr__(self, "trigger", self.trigger.strip().lower())

    @property
    def token_keys(self) -> tuple[str, ...]:
        return (self.duration_token, self.easing_token)


@dataclass(frozen=True, slots=True)
class AccessibilityDirective:
    """The accessibility contract a section must uphold.

    Attributes:
        role: The ARIA role / landmark the section maps to.
        min_contrast: The minimum text contrast ratio (e.g. 4.5 for WCAG AA).
        keyboard: The keyboard interactions required.
        focus_visible: Whether a visible focus indicator is mandatory.
    """

    role: str
    min_contrast: float = 4.5
    keyboard: tuple[str, ...] = ()
    focus_visible: bool = True

    def __post_init__(self) -> None:
        if not self.role or not self.role.strip():
            raise InvalidDirectiveError("AccessibilityDirective.role must be non-empty.")
        if not self.min_contrast > 0:
            raise InvalidDirectiveError("AccessibilityDirective.min_contrast must be positive.")
        object.__setattr__(self, "role", self.role.strip())
        object.__setattr__(
            self,
            "keyboard",
            tuple(dict.fromkeys(k.strip().lower() for k in self.keyboard if k and k.strip())),
        )


@dataclass(frozen=True, slots=True)
class PerformanceDirective:
    """The performance envelope a section is planned within.

    Attributes:
        lazy_load: Whether the section defers below-the-fold work.
        priority: A 1–5 load priority (5 = above-the-fold critical).
        blocks_lcp: Whether the section can hold the largest-contentful-paint element.
    """

    lazy_load: bool = False
    priority: int = 3
    blocks_lcp: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.priority, int) or isinstance(self.priority, bool):
            raise InvalidDirectiveError("PerformanceDirective.priority must be an int.")
        if not 1 <= self.priority <= 5:
            raise InvalidDirectiveError(
                "PerformanceDirective.priority must be within [1, 5].",
                details={"priority": self.priority},
            )
