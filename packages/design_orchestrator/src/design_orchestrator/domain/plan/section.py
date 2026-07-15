"""The section plan — the atomic unit of the execution plan.

A :class:`SectionPlan` is the orchestrator's complete decision for one section of one page: its
position in the page order, the role it plays, the component and variant chosen for it, the
layout/spacing/typography/visual choices, the token bindings, and the responsive/animation/
accessibility/performance directives — every one grounded in cited evidence and, crucially,
*selected* from what the Design System and Component Intelligence already produced.

The ``SectionPlanId`` is the join key of the whole plan: the component tree's COMPONENT nodes,
the token and variant mappings, and the execution graph's per-section steps all reference it, so
every view of the plan (structural, temporal, binding) stays consistent.

Pure domain: standard library, the shared-kernel error base, DO ids, evidence, the choice and
directive value objects, and shared value objects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from core.errors import DesignDirectorError

from design_orchestrator.domain.evidence.evidence import Citation
from design_orchestrator.domain.plan.choice import (
    LayoutRule,
    SpacingRule,
    TypographyChoice,
    VisualChoice,
)
from design_orchestrator.domain.plan.directives import (
    AccessibilityDirective,
    AnimationDirective,
    PerformanceDirective,
    ResponsiveDirective,
)
from design_orchestrator.domain.shared.ids import SectionPlanId
from design_orchestrator.domain.shared.value_objects import (
    ComponentType,
    ConsideredAlternative,
    PageType,
    Rank,
    SectionRole,
)

__all__ = ["InvalidSectionPlanError", "SectionPlan"]

_TOKEN_KEY = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")
_VARIANT = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


class InvalidSectionPlanError(DesignDirectorError):
    """Raised when a section plan is constructed with invalid data."""

    code = "invalid_design_orchestrator_section_plan"
    http_status = 422


@dataclass(frozen=True, slots=True)
class SectionPlan:
    """The orchestrator's complete decision for one section of one page.

    Attributes:
        id: Section-plan identity (the join key of the plan).
        page_type: The page this section belongs to.
        order: The 1-based position of this section in the page order.
        role: The role the section plays.
        component: The component chosen to realise the section.
        variant_name: The variant chosen for that component (must be one the component declares).
        layout: The layout rule.
        spacing: The spacing rule.
        typography: The typography choice.
        visual: The visual-language choice.
        token_bindings: Every Design-System token key this section binds (unique, non-empty).
        responsive: The responsive directive.
        animation: The animation directive.
        accessibility: The accessibility directive.
        performance: The performance directive.
        considered_alternative: The component/variant the orchestrator weighed and rejected.
        citations: The evidence supporting this section (must resolve in the evidence graph).
    """

    id: SectionPlanId
    page_type: PageType
    order: Rank
    role: SectionRole
    component: ComponentType
    variant_name: str
    layout: LayoutRule
    spacing: SpacingRule
    typography: TypographyChoice
    visual: VisualChoice
    token_bindings: tuple[str, ...]
    responsive: ResponsiveDirective
    animation: AnimationDirective
    accessibility: AccessibilityDirective
    performance: PerformanceDirective
    considered_alternative: ConsideredAlternative | None = None
    citations: tuple[Citation, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        variant = self.variant_name.strip().lower()
        if not _VARIANT.match(variant):
            raise InvalidSectionPlanError(
                "SectionPlan.variant_name must be a lower-case identifier.",
                details={"variant_name": self.variant_name},
            )
        object.__setattr__(self, "variant_name", variant)

        bindings = tuple(
            dict.fromkeys(b.strip().lower() for b in self.token_bindings if b and b.strip())
        )
        if not bindings:
            raise InvalidSectionPlanError(
                "SectionPlan must bind at least one token (no hard-coded values).",
                details={"component": self.component.value},
            )
        for key in bindings:
            if not _TOKEN_KEY.match(key):
                raise InvalidSectionPlanError(
                    f"Token binding {key!r} is not a valid dotted token key.",
                    details={"component": self.component.value},
                )
        object.__setattr__(self, "token_bindings", bindings)
        object.__setattr__(self, "citations", tuple(self.citations))

    @property
    def evidence_ids(self) -> tuple:
        return tuple(c.evidence_id for c in self.citations)

    @property
    def choice_token_keys(self) -> tuple[str, ...]:
        """Every token key referenced by this section's choices and directives."""
        keys: list[str] = []
        keys.extend(self.spacing.token_keys)
        keys.extend(self.typography.token_keys)
        keys.extend(self.visual.surface_tokens)
        keys.extend(self.animation.token_keys)
        return tuple(dict.fromkeys(keys))
