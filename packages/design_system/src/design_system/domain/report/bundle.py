"""The DesignSystemBundle — the neutral hand-off a future UI / Figma phase consumes.

The Design System Engine is downstream-independent of rendering: it imports nothing from any
later phase and produces no UI and no Figma. Instead it emits this neutral, self-contained
bundle — the resolved token set, the component specs (with variants/states/responsive/
accessibility/performance and the developer/Shopify/Magento mappings), the themes, the
localization contract, and the enforced constraints — everything a downstream builder needs to
*materialise* a compliant UI, and nothing that pre-empts how. A future UI-generation / Figma /
codegen phase consumes it through a port *it* owns.

Pure domain: standard library and the specification models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from design_system.domain.component.spec import ComponentSpecSet
from design_system.domain.constraint.constraint import ConstraintSet
from design_system.domain.report.report import DesignSystemSpecification
from design_system.domain.shared.ids import DesignSystemSpecId
from design_system.domain.theme.localization import Localization
from design_system.domain.theme.theme import ThemeSet
from design_system.domain.token.token import TokenSet

__all__ = ["DesignSystemBundle"]


@dataclass(frozen=True, slots=True)
class DesignSystemBundle:
    """The neutral design-system specification a downstream UI phase builds from.

    Attributes:
        spec_id: The specification version this bundle projects.
        project_id: The owning project.
        token_set: The resolved three-tier token set.
        component_specs: The complete component specifications.
        theme_set: The light/dark themes.
        localization: The direction/locale contract.
        constraint_set: The rules every future UI must obey.
        is_production_ready: Whether the specification is settled.
        created_at: When the specification was produced.
    """

    spec_id: DesignSystemSpecId
    project_id: str
    token_set: TokenSet
    component_specs: ComponentSpecSet
    theme_set: ThemeSet
    localization: Localization
    constraint_set: ConstraintSet
    is_production_ready: bool
    created_at: datetime

    @classmethod
    def from_specification(cls, spec: DesignSystemSpecification) -> DesignSystemBundle:
        return cls(
            spec_id=spec.id,
            project_id=spec.project_id,
            token_set=spec.token_set,
            component_specs=spec.component_specs,
            theme_set=spec.theme_set,
            localization=spec.localization,
            constraint_set=spec.constraint_set,
            is_production_ready=spec.is_production_ready,
            created_at=spec.created_at,
        )
