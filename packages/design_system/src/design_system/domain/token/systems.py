"""Token systems — the responsive, layout, and motion machinery of the design system.

These value objects model the cross-cutting systems every component obeys: the responsive
:class:`BreakpointSystem` (the ordered bands and their min-widths), the :class:`GridSystem`
(columns and gutter tokens per breakpoint), the :class:`ContainerRules` (max content widths),
the :class:`MotionSystem` (duration and easing tokens), and the :class:`InteractionTokens`
(focus ring, hit target, transition defaults). They reference tokens by key rather than holding
literals, so the same rules drive every platform mapping.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from design_system.domain.shared.value_objects import Breakpoint

__all__ = [
    "BreakpointSystem",
    "ContainerRules",
    "GridSystem",
    "InteractionTokens",
    "InvalidSystemError",
    "MotionSystem",
]


class InvalidSystemError(DesignDirectorError):
    """Raised when a token system is constructed with invalid data."""

    code = "invalid_design_system_system"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BreakpointSystem:
    """The ordered responsive bands and the min-width (px) at which each begins.

    Attributes:
        min_width_px: Each supported breakpoint mapped to its lower bound in pixels. Must be
            strictly increasing across ``MOBILE < TABLET < DESKTOP < WIDE`` for the bands
            present, and must include ``MOBILE`` (mobile-first).
    """

    min_width_px: Mapping[Breakpoint, int] = field(
        default_factory=lambda: MappingProxyType({})
    )

    _ORDER = (Breakpoint.MOBILE, Breakpoint.TABLET, Breakpoint.DESKTOP, Breakpoint.WIDE)

    def __post_init__(self) -> None:
        data = dict(self.min_width_px)
        if Breakpoint.MOBILE not in data:
            raise InvalidSystemError("BreakpointSystem must be mobile-first (include MOBILE).")
        present = [bp for bp in self._ORDER if bp in data]
        widths = [data[bp] for bp in present]
        if any(w < 0 for w in widths):
            raise InvalidSystemError("Breakpoint min-widths must be non-negative.")
        if any(b <= a for a, b in zip(widths, widths[1:])):
            raise InvalidSystemError(
                "Breakpoint min-widths must strictly increase.",
                details={"widths": widths},
            )
        object.__setattr__(self, "min_width_px", MappingProxyType(data))

    @property
    def bands(self) -> tuple[Breakpoint, ...]:
        return tuple(bp for bp in self._ORDER if bp in self.min_width_px)


@dataclass(frozen=True, slots=True)
class GridSystem:
    """The layout grid: column count and gutter token per breakpoint.

    Attributes:
        columns: Column count per breakpoint (each positive).
        gutter_tokens: The spacing token key used as the gutter per breakpoint.
    """

    columns: Mapping[Breakpoint, int] = field(default_factory=lambda: MappingProxyType({}))
    gutter_tokens: Mapping[Breakpoint, str] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        cols = dict(self.columns)
        if not cols:
            raise InvalidSystemError("GridSystem must define columns for at least one breakpoint.")
        if any(c <= 0 for c in cols.values()):
            raise InvalidSystemError("Grid column counts must be positive.")
        gutters = {bp: g.strip().lower() for bp, g in self.gutter_tokens.items()}
        if any(not g for g in gutters.values()):
            raise InvalidSystemError("Grid gutter tokens must be non-empty.")
        object.__setattr__(self, "columns", MappingProxyType(cols))
        object.__setattr__(self, "gutter_tokens", MappingProxyType(gutters))


@dataclass(frozen=True, slots=True)
class ContainerRules:
    """Max content widths per breakpoint (px) — the reading-measure guardrail.

    Attributes:
        max_width_px: Each breakpoint mapped to the max container width in pixels.
    """

    max_width_px: Mapping[Breakpoint, int] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        data = dict(self.max_width_px)
        if not data:
            raise InvalidSystemError("ContainerRules must define at least one max width.")
        if any(w <= 0 for w in data.values()):
            raise InvalidSystemError("Container max widths must be positive.")
        object.__setattr__(self, "max_width_px", MappingProxyType(data))


@dataclass(frozen=True, slots=True)
class MotionSystem:
    """The motion vocabulary: named duration and easing token keys.

    Attributes:
        duration_tokens: The ordered duration token keys, fastest to slowest
            (e.g. ``("motion.fast", "motion.base", "motion.slow")``).
        easing_tokens: The named easing token keys
            (e.g. ``("ease.standard", "ease.emphasized", "ease.decelerate")``).
    """

    duration_tokens: tuple[str, ...] = ()
    easing_tokens: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        durations = tuple(d.strip().lower() for d in self.duration_tokens if d and d.strip())
        easings = tuple(e.strip().lower() for e in self.easing_tokens if e and e.strip())
        if not durations:
            raise InvalidSystemError("MotionSystem must define at least one duration token.")
        if not easings:
            raise InvalidSystemError("MotionSystem must define at least one easing token.")
        if len(set(durations)) != len(durations) or len(set(easings)) != len(easings):
            raise InvalidSystemError("MotionSystem tokens must be unique.")
        object.__setattr__(self, "duration_tokens", durations)
        object.__setattr__(self, "easing_tokens", easings)


@dataclass(frozen=True, slots=True)
class InteractionTokens:
    """The interaction defaults every interactive element inherits.

    Attributes:
        focus_ring_token: The token key describing the focus ring (accessibility-critical).
        hit_target_token: The token key for the minimum hit-target size.
        transition_token: The default transition duration token key.
    """

    focus_ring_token: str
    hit_target_token: str
    transition_token: str

    def __post_init__(self) -> None:
        for name, value in (
            ("focus_ring_token", self.focus_ring_token),
            ("hit_target_token", self.hit_target_token),
            ("transition_token", self.transition_token),
        ):
            if not value or not value.strip():
                raise InvalidSystemError(f"InteractionTokens.{name} must be non-empty.")
            object.__setattr__(self, name, value.strip().lower())
