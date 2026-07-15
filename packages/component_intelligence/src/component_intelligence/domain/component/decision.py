"""The ComponentDecision — the engine's full intelligence about one component.

A :class:`ComponentDecision` is the heart of the engine: for one component it carries everything
the spec demands — its atomic level and inclusion, its four purposes, its impacts and outcome
effects, its behaviours (mobile, responsive, interaction, animation), its data contract and
criteria, its usage guidance (where it belongs, when to use, when not to use, what it conflicts
with), and its variants, states, and design-token references. A component may only be *included*
when it is fully understood; a component with an empty required attribute is not
production-ready.

Pure domain: standard library, the shared-kernel error base, CI ids, and the component sub-models.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.errors import DesignDirectorError

from component_intelligence.domain.component.behaviour import (
    AnimationRule,
    InteractionRule,
    MobileBehaviour,
    ResponsiveRule,
)
from component_intelligence.domain.component.contract import (
    ExpectedOutput,
    FailureCriterion,
    RequiredInput,
    SuccessCriterion,
)
from component_intelligence.domain.component.impact import ComponentImpacts
from component_intelligence.domain.component.purpose import ComponentPurposes
from component_intelligence.domain.component.usage import UsageGuidance
from component_intelligence.domain.component.variant import ComponentState, Variant
from component_intelligence.domain.shared.ids import CIEvidenceId, DecisionId
from component_intelligence.domain.shared.value_objects import (
    AtomicLevel,
    ComponentType,
    ConsideredAlternative,
    Inclusion,
    PageType,
    Priority,
)

__all__ = ["ComponentDecision", "InvalidDecisionError"]


class InvalidDecisionError(DesignDirectorError):
    """Raised when a component decision is constructed with invalid data."""

    code = "invalid_component_intelligence_decision"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ComponentDecision:
    """The engine's complete intelligence about one component.

    Attributes:
        id: Decision identity.
        component: Which component this decides.
        atomic_level: Its atomic-design level.
        inclusion: Whether it is included, optional, or excluded.
        priority: Its priority within the composition.
        purposes: Its business/user/conversion/trust purposes.
        impacts: Its SEO/accessibility/performance impacts and outcome effects.
        mobile_behaviour: How it behaves on mobile.
        responsive_rules: Its per-breakpoint behaviour.
        interaction_rules: The interactions it requires.
        animation_rules: The animations it may use.
        dependencies: Components it depends on.
        required_inputs: The data it needs.
        expected_outputs: The artifacts it produces.
        success_criteria: What makes it a success.
        failure_criteria: What makes it a failure.
        usage: Where and when it should (and should not) be used.
        variants: Its purposeful variants.
        states: The UI states it must handle.
        design_token_refs: References into the Design Language's token roles.
        considered_alternative: The alternative it was chosen over, if any.
        evidence_ids: The evidence grounding the decision.
    """

    id: DecisionId
    component: ComponentType
    atomic_level: AtomicLevel
    inclusion: Inclusion
    purposes: ComponentPurposes
    impacts: ComponentImpacts
    mobile_behaviour: MobileBehaviour
    usage: UsageGuidance
    priority: Priority = Priority(3)
    responsive_rules: tuple[ResponsiveRule, ...] = ()
    interaction_rules: tuple[InteractionRule, ...] = ()
    animation_rules: tuple[AnimationRule, ...] = ()
    dependencies: tuple[ComponentType, ...] = ()
    required_inputs: tuple[RequiredInput, ...] = ()
    expected_outputs: tuple[ExpectedOutput, ...] = ()
    success_criteria: tuple[SuccessCriterion, ...] = ()
    failure_criteria: tuple[FailureCriterion, ...] = ()
    variants: tuple[Variant, ...] = ()
    states: tuple[ComponentState, ...] = ()
    design_token_refs: tuple[str, ...] = ()
    considered_alternative: ConsideredAlternative | None = None
    evidence_ids: tuple[CIEvidenceId, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.component in self.dependencies:
            raise InvalidDecisionError(
                "A component cannot depend on itself.", details={"component": self.component.value}
            )
        if self.component in self.usage.conflicts_with:
            raise InvalidDecisionError(
                "A component cannot conflict with itself.",
                details={"component": self.component.value},
            )
        object.__setattr__(self, "dependencies", tuple(dict.fromkeys(self.dependencies)))
        object.__setattr__(self, "design_token_refs", tuple(dict.fromkeys(self.design_token_refs)))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    # -- queries ----------------------------------------------------------- #
    @property
    def is_included(self) -> bool:
        return self.inclusion is Inclusion.INCLUDED

    @property
    def improves_conversion(self) -> bool:
        return self.impacts.improves_conversion

    @property
    def builds_trust(self) -> bool:
        return self.impacts.builds_trust

    def belongs_on(self, page: PageType) -> bool:
        return self.usage.belongs_on(page)

    @property
    def is_fully_specified(self) -> bool:
        """Whether the component carries every required attribute to be built with confidence."""
        return bool(
            self.responsive_rules
            and self.interaction_rules
            and self.required_inputs
            and self.expected_outputs
            and self.success_criteria
            and self.failure_criteria
            and self.usage.page_affinity
            and self.usage.when_to_use
            and self.usage.when_not_to_use
            and self.variants
            and self.states
        )

    def all_evidence_ids(self) -> tuple[CIEvidenceId, ...]:
        ids: list[CIEvidenceId] = list(self.evidence_ids)
        ids.extend(self.purposes.evidence_ids)
        ids.extend(self.impacts.evidence_ids)
        ids.extend(self.usage.evidence_ids)
        return tuple(ids)
