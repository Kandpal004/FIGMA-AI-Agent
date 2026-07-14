"""Section requirement value objects — the non-visual constraints a section must satisfy.

Each of these captures one axis of a section's execution requirements, in planning terms:
what data it needs, what assets it needs, how it must behave interactively and responsively,
and what it must satisfy for accessibility, SEO, and performance. None of these describe a
visual property — they describe *requirements the future Figma design must honour*.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from wireframe.domain.shared.value_objects import (
    AccessibilityKind,
    AssetKind,
    Breakpoint,
    DataKind,
    InteractionKind,
    PerformanceKind,
    ResponsiveIntent,
    SEOKind,
)

__all__ = [
    "AccessibilityRequirement",
    "AssetRequirement",
    "DataRequirement",
    "InteractionRequirement",
    "InvalidRequirementError",
    "PerformanceConsideration",
    "ResponsiveBehaviour",
    "ResponsiveRule",
    "SEORequirement",
]


class InvalidRequirementError(DesignDirectorError):
    """Raised when a section requirement is constructed with invalid data."""

    code = "invalid_wireframe_requirement"
    http_status = 422


@dataclass(frozen=True, slots=True)
class DataRequirement:
    """A kind of data the section needs supplied to be built.

    Attributes:
        kind: The data kind.
        description: What the data is used for.
        required: Whether the section cannot function without it.
    """

    kind: DataKind
    description: str = ""
    required: bool = True


@dataclass(frozen=True, slots=True)
class AssetRequirement:
    """An asset the section needs produced or sourced.

    Attributes:
        kind: The asset kind.
        description: What the asset is for.
        required: Whether the section cannot function without it.
    """

    kind: AssetKind
    description: str = ""
    required: bool = True


@dataclass(frozen=True, slots=True)
class InteractionRequirement:
    """An interaction behaviour the section requires (intent, not visual treatment).

    Attributes:
        kind: The interaction kind.
        intent: What the interaction should accomplish.
    """

    kind: InteractionKind
    intent: str = ""


@dataclass(frozen=True, slots=True)
class ResponsiveRule:
    """How the section should behave at one breakpoint."""

    breakpoint: Breakpoint
    intent: ResponsiveIntent


@dataclass(frozen=True, slots=True)
class ResponsiveBehaviour:
    """The section's per-breakpoint behaviour intent (no pixels, no layout spec).

    Attributes:
        rules: One behaviour rule per relevant breakpoint.
    """

    rules: tuple[ResponsiveRule, ...] = ()

    def __post_init__(self) -> None:
        seen: set[Breakpoint] = set()
        for rule in self.rules:
            if rule.breakpoint in seen:
                raise InvalidRequirementError(
                    "ResponsiveBehaviour has two rules for the same breakpoint.",
                    details={"breakpoint": rule.breakpoint.value},
                )
            seen.add(rule.breakpoint)
        object.__setattr__(self, "rules", tuple(self.rules))

    def at(self, breakpoint: Breakpoint) -> ResponsiveIntent | None:
        return next((r.intent for r in self.rules if r.breakpoint is breakpoint), None)


@dataclass(frozen=True, slots=True)
class AccessibilityRequirement:
    """An accessibility requirement the section must satisfy (WCAG intent).

    Attributes:
        kind: The accessibility kind.
        intent: What must be true for the section to be accessible.
    """

    kind: AccessibilityKind
    intent: str = ""


@dataclass(frozen=True, slots=True)
class SEORequirement:
    """An SEO requirement the section must satisfy.

    Attributes:
        kind: The SEO kind.
        intent: What the section must do for SEO.
    """

    kind: SEOKind
    intent: str = ""


@dataclass(frozen=True, slots=True)
class PerformanceConsideration:
    """A performance consideration the section must honour.

    Attributes:
        kind: The performance kind.
        intent: What the section must do for performance.
    """

    kind: PerformanceKind
    intent: str = ""
