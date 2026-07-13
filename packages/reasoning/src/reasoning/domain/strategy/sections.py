"""The thematic strategy sections — the structured answers to every question.

Each section is an immutable container of :class:`EvidencedStatement` s (and, for
single-answer questions, an optional one). Single-answer fields are ``| None`` so
the strategy can still be assembled when a dimension is a
:class:`~reasoning.domain.strategy.gap.KnowledgeGap` — the missing answer is
recorded as a gap, not fabricated here.

Every section exposes :meth:`statements`, so the aggregate can collect all cited
claims uniformly for confidence scoring and evidence-integrity validation.

Pure domain: standard library plus the evidenced-statement value object.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from reasoning.domain.strategy.statement import EvidencedStatement

__all__ = [
    "BusinessObjective",
    "CompetitiveStrategy",
    "ConversionStrategy",
    "CustomerProfile",
    "ExperienceStrategy",
    "PlatformStrategy",
    "ReviewStrategy",
    "VisualStrategy",
]


def _collect(*groups: object) -> tuple[EvidencedStatement, ...]:
    """Flatten optional statements and statement tuples into one tuple."""
    out: list[EvidencedStatement] = []
    for group in groups:
        if group is None:
            continue
        if isinstance(group, EvidencedStatement):
            out.append(group)
        else:
            out.extend(group)  # type: ignore[arg-type]
    return tuple(out)


@dataclass(frozen=True, slots=True)
class BusinessObjective:
    """The business objective the design must serve."""

    objective: EvidencedStatement | None = None
    secondary: tuple[EvidencedStatement, ...] = ()

    def statements(self) -> tuple[EvidencedStatement, ...]:
        return _collect(self.objective, self.secondary)


@dataclass(frozen=True, slots=True)
class CustomerProfile:
    """Who the customer is and what moves them."""

    who: EvidencedStatement | None = None
    target_market: EvidencedStatement | None = None
    problems: tuple[EvidencedStatement, ...] = ()
    objections: tuple[EvidencedStatement, ...] = ()
    emotional_triggers: tuple[EvidencedStatement, ...] = ()
    trust_mechanisms: tuple[EvidencedStatement, ...] = ()

    def statements(self) -> tuple[EvidencedStatement, ...]:
        return _collect(
            self.who,
            self.target_market,
            self.problems,
            self.objections,
            self.emotional_triggers,
            self.trust_mechanisms,
        )


@dataclass(frozen=True, slots=True)
class ConversionStrategy:
    """The CRO principles the design should apply."""

    principles: tuple[EvidencedStatement, ...] = ()

    def statements(self) -> tuple[EvidencedStatement, ...]:
        return tuple(self.principles)


@dataclass(frozen=True, slots=True)
class ExperienceStrategy:
    """The UX principles and accessibility rules that apply."""

    ux_principles: tuple[EvidencedStatement, ...] = ()
    accessibility_rules: tuple[EvidencedStatement, ...] = ()

    def statements(self) -> tuple[EvidencedStatement, ...]:
        return _collect(self.ux_principles, self.accessibility_rules)


@dataclass(frozen=True, slots=True)
class PlatformStrategy:
    """The platform limitations that constrain the design."""

    shopify_constraints: tuple[EvidencedStatement, ...] = ()
    magento_constraints: tuple[EvidencedStatement, ...] = ()

    def statements(self) -> tuple[EvidencedStatement, ...]:
        return _collect(self.shopify_constraints, self.magento_constraints)


@dataclass(frozen=True, slots=True)
class CompetitiveStrategy:
    """The competitors to research and why."""

    competitors_to_research: tuple[EvidencedStatement, ...] = ()

    def statements(self) -> tuple[EvidencedStatement, ...]:
        return tuple(self.competitors_to_research)


@dataclass(frozen=True, slots=True)
class VisualStrategy:
    """The visual direction — design system, typography, spacing, hierarchy.

    Directions, never designs (e.g. "high-contrast serif for editorial trust", not
    a type spec).
    """

    design_system: EvidencedStatement | None = None
    typography: EvidencedStatement | None = None
    spacing: EvidencedStatement | None = None
    visual_hierarchy: EvidencedStatement | None = None

    def statements(self) -> tuple[EvidencedStatement, ...]:
        return _collect(
            self.design_system, self.typography, self.spacing, self.visual_hierarchy
        )


@dataclass(frozen=True, slots=True)
class ReviewStrategy:
    """What the Creative Director should review."""

    review_points: tuple[EvidencedStatement, ...] = field(default_factory=tuple)

    def statements(self) -> tuple[EvidencedStatement, ...]:
        return tuple(self.review_points)
