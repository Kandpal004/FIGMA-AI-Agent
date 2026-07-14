"""The DesignSystemBundle — the neutral hand-off a future Design System phase consumes.

The Design Language Engine is upstream-independent of design tooling: it imports nothing from
any later phase and produces no concrete values. Instead it emits this neutral, self-contained
bundle — the Visual DNA, the abstract token system, the grid and responsive systems, the
philosophies and personalities, and the consistency/composition/constraint rules — everything
a downstream builder needs to *materialise* the language into concrete tokens, palettes, type
ramps, and eventually Figma variables, and nothing that pre-empts it. A future Phase-15 Design
System Engine consumes it through a port *it* owns.

Pure domain: standard library and the specification models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from design_language.domain.dna.visual_dna import VisualDNA
from design_language.domain.language.selection import LanguageSelection
from design_language.domain.personality.personality import PersonalitySet
from design_language.domain.philosophy.philosophy import PhilosophySet
from design_language.domain.report.report import DesignLanguageSpecification
from design_language.domain.rules.composition import CompositionRuleSet
from design_language.domain.rules.consistency import ConsistencyRuleSet
from design_language.domain.rules.constraint import ConstraintSet
from design_language.domain.shared.ids import DesignLanguageSpecId
from design_language.domain.shared.value_objects import IndustryPreset
from design_language.domain.system.grid_system import GridSystem
from design_language.domain.system.responsive import ResponsiveStrategy
from design_language.domain.tokens.visual_tokens import VisualTokens

__all__ = ["DesignSystemBundle"]


@dataclass(frozen=True, slots=True)
class DesignSystemBundle:
    """The neutral design language a downstream Design System builds from.

    Attributes:
        spec_id: The specification version this bundle projects.
        project_id: The owning project.
        industry: The industry preset.
        selection: The selected language and its reasoning.
        visual_dna: The distilled visual identity.
        tokens: The abstract token system.
        grid_system: The structural grid.
        responsive_strategy: The responsive posture.
        philosophies: The eleven philosophies.
        personalities: The four personalities.
        consistency_rules: The consistency invariants.
        composition_rules: The composition rules.
        constraints: The visual constraints.
        is_production_ready: Whether the language is settled.
        created_at: When the specification was produced.
    """

    spec_id: DesignLanguageSpecId
    project_id: str
    industry: IndustryPreset
    selection: LanguageSelection
    visual_dna: VisualDNA
    tokens: VisualTokens
    grid_system: GridSystem
    responsive_strategy: ResponsiveStrategy
    philosophies: PhilosophySet
    personalities: PersonalitySet
    consistency_rules: ConsistencyRuleSet
    composition_rules: CompositionRuleSet
    constraints: ConstraintSet
    is_production_ready: bool
    created_at: datetime

    @classmethod
    def from_specification(
        cls, spec: DesignLanguageSpecification
    ) -> DesignSystemBundle:
        return cls(
            spec_id=spec.id, project_id=spec.project_id, industry=spec.industry,
            selection=spec.language_selection, visual_dna=spec.visual_dna, tokens=spec.tokens,
            grid_system=spec.grid_system, responsive_strategy=spec.responsive_strategy,
            philosophies=spec.philosophies, personalities=spec.personalities,
            consistency_rules=spec.consistency_rules, composition_rules=spec.composition_rules,
            constraints=spec.constraints, is_production_ready=spec.is_production_ready,
            created_at=spec.created_at,
        )
