"""The ComponentSpecBundle — the neutral hand-off a future Design System phase consumes.

The Component Intelligence Engine is upstream-independent of implementation: it imports nothing
from any later phase and produces no component code. Instead it emits this neutral,
self-contained bundle — the included component decisions (with atomic level, purposes, impacts,
variants, states, token references, contracts) plus the placement/visibility/responsive/reuse
rules and the compatibility web — everything a downstream builder needs to *materialise* each
component, and nothing that pre-empts it. A future Phase-16 Design System / Component Library
Engine consumes it through a port *it* owns.

Pure domain: standard library and the specification models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from component_intelligence.domain.compatibility.compatibility import CompatibilitySet
from component_intelligence.domain.component.decision import ComponentDecision
from component_intelligence.domain.report.report import ComponentCompositionSpecification
from component_intelligence.domain.rules.composition_rules import CompositionRuleSet
from component_intelligence.domain.rules.placement_rules import PlacementRuleSet
from component_intelligence.domain.rules.responsive_rules import ResponsiveRuleSet
from component_intelligence.domain.rules.reuse_rules import ReuseRuleSet
from component_intelligence.domain.rules.visibility_rules import VisibilityRuleSet
from component_intelligence.domain.shared.ids import ComponentSpecId

__all__ = ["ComponentSpecBundle"]


@dataclass(frozen=True, slots=True)
class ComponentSpecBundle:
    """The neutral component specification a downstream Design System builds from.

    Attributes:
        spec_id: The specification version this bundle projects.
        project_id: The owning project.
        components: The included component decisions.
        compatibility: The compatibility web.
        composition_rules: How components combine.
        placement_rules: Which component belongs on which page.
        visibility_rules: When each component is shown/hidden.
        responsive_rules: How the composition reflows.
        reuse_rules: Which components are shared and must stay consistent.
        is_production_ready: Whether the composition is settled.
        created_at: When the specification was produced.
    """

    spec_id: ComponentSpecId
    project_id: str
    components: tuple[ComponentDecision, ...]
    compatibility: CompatibilitySet
    composition_rules: CompositionRuleSet
    placement_rules: PlacementRuleSet
    visibility_rules: VisibilityRuleSet
    responsive_rules: ResponsiveRuleSet
    reuse_rules: ReuseRuleSet
    is_production_ready: bool
    created_at: datetime

    @classmethod
    def from_specification(
        cls, spec: ComponentCompositionSpecification
    ) -> ComponentSpecBundle:
        return cls(
            spec_id=spec.id, project_id=spec.project_id,
            components=spec.composition.included(), compatibility=spec.compatibility,
            composition_rules=spec.composition_rules, placement_rules=spec.placement_rules,
            visibility_rules=spec.visibility_rules, responsive_rules=spec.responsive_rules,
            reuse_rules=spec.reuse_rules, is_production_ready=spec.is_production_ready,
            created_at=spec.created_at,
        )
