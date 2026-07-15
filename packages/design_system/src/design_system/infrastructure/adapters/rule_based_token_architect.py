"""The deterministic, rule-based Token Architect — the default design-system brain.

Implements :class:`TokenArchitectPort` without any LLM: it turns the codified
:data:`~design_system.infrastructure.adapters.token_baseline.BASELINE` into cited domain
objects, adapting to the brief (dark mode, RTL, target platforms) and grounding every token and
component in the consolidated evidence. It is fully deterministic — the same input and evidence
always yield the same draft — so the engine's output is reproducible and auditable.

It cites, never invents: each token and component references real evidence ids drawn from the
graph it is given, spreading citations across the upstream provenances so the produced graphs
can be explained back to every engine that grounded the system. When evidence for a preferred
provenance is absent it falls back to any available evidence, so grounding never fabricates.

Pure infrastructure: the baseline data, the mapping factory, the domain models, and the
application contracts/ports.
"""

from __future__ import annotations

from design_system.application.contracts import DesignSystemDraft, DesignSystemInput
from design_system.application.ports.token_architect import TokenArchitectPort
from design_system.domain.component.mapping import PlatformMapping
from design_system.domain.component.spec import (
    AccessibilitySpec,
    ComponentSpec,
    ComponentSpecSet,
    PerformanceBudget,
)
from design_system.domain.component.variant import (
    ComponentProperty,
    ComponentStateSpec,
    ComponentVariant,
    ResponsiveSpec,
)
from design_system.domain.evidence.evidence import Citation, DSEvidence, EvidenceGraph
from design_system.domain.shared.ids import ComponentSpecId, TokenId
from design_system.domain.shared.value_objects import (
    Direction,
    Platform,
    ProvenanceKind,
    Ratio,
    StateKind,
    TokenCategory,
)
from design_system.domain.theme.localization import Localization
from design_system.domain.theme.theme import Theme, ThemeSet
from design_system.domain.token.scales import (
    BorderScale,
    ElevationScale,
    RadiusScale,
    ShadowScale,
    SpacingScale,
    TypographyScale,
)
from design_system.domain.token.state import StateTokens
from design_system.domain.token.systems import (
    BreakpointSystem,
    ContainerRules,
    GridSystem,
    InteractionTokens,
    MotionSystem,
)
from design_system.domain.token.token import DesignToken, TokenSet, TokenValue
from design_system.domain.shared.ids import ThemeId
from design_system.domain.shared.value_objects import ThemeMode
from design_system.infrastructure.adapters.platform_mappings import PlatformMappingFactory
from design_system.infrastructure.adapters.token_baseline import (
    BASELINE,
    ComponentBlueprint,
    StateBlueprint,
    TokenBaseline,
)

__all__ = ["RuleBasedTokenArchitect"]

# Preferred provenances per token category (first available wins; falls back to any).
_CATEGORY_PROVENANCE: dict[TokenCategory, tuple[ProvenanceKind, ...]] = {
    TokenCategory.COLOR: (ProvenanceKind.BRAND_STRATEGY, ProvenanceKind.DESIGN_LANGUAGE),
    TokenCategory.TYPOGRAPHY: (ProvenanceKind.BRAND_STRATEGY, ProvenanceKind.DESIGN_LANGUAGE),
    TokenCategory.SPACING: (ProvenanceKind.WIREFRAME, ProvenanceKind.DESIGN_LANGUAGE),
    TokenCategory.RADIUS: (ProvenanceKind.DESIGN_LANGUAGE, ProvenanceKind.CREATIVE_DIRECTOR),
    TokenCategory.SHADOW: (ProvenanceKind.DESIGN_LANGUAGE, ProvenanceKind.CREATIVE_DIRECTOR),
    TokenCategory.ELEVATION: (ProvenanceKind.DESIGN_LANGUAGE, ProvenanceKind.CREATIVE_DIRECTOR),
    TokenCategory.BORDER: (ProvenanceKind.DESIGN_LANGUAGE, ProvenanceKind.WIREFRAME),
    TokenCategory.MOTION: (ProvenanceKind.UX_STRATEGY, ProvenanceKind.PSYCHOLOGY),
    TokenCategory.INTERACTION: (ProvenanceKind.UX_STRATEGY, ProvenanceKind.PSYCHOLOGY),
    TokenCategory.OPACITY: (ProvenanceKind.CREATIVE_DIRECTOR, ProvenanceKind.KNOWLEDGE),
    TokenCategory.Z_INDEX: (ProvenanceKind.WIREFRAME, ProvenanceKind.KNOWLEDGE),
}
_DEFAULT_TOKEN_PROVENANCE = (ProvenanceKind.KNOWLEDGE, ProvenanceKind.DESIGN_LANGUAGE)

# The provenances spread across component specs so every upstream engine surfaces in the graphs.
_COMPONENT_PROVENANCE_CYCLE = (
    ProvenanceKind.COMPONENT_INTELLIGENCE,
    ProvenanceKind.UX_STRATEGY,
    ProvenanceKind.PSYCHOLOGY,
    ProvenanceKind.WIREFRAME,
    ProvenanceKind.CREATIVE_DIRECTOR,
    ProvenanceKind.INFORMATION_ARCHITECTURE,
    ProvenanceKind.BUSINESS_STRATEGY,
)


class _CiteSource:
    """Picks real evidence, preferring given provenances, falling back to any."""

    def __init__(self, evidence: EvidenceGraph) -> None:
        self._by_prov: dict[ProvenanceKind, list[DSEvidence]] = {}
        for item in evidence:
            self._by_prov.setdefault(item.provenance, []).append(item)
        self._any: list[DSEvidence] = list(evidence)

    def cite(self, *preferred: ProvenanceKind) -> tuple[Citation, ...]:
        for provenance in preferred:
            bucket = self._by_prov.get(provenance)
            if bucket:
                return (Citation(evidence_id=bucket[0].id, relevance="grounds this decision"),)
        if self._any:
            return (Citation(evidence_id=self._any[0].id, relevance="grounds this decision"),)
        return ()


class RuleBasedTokenArchitect(TokenArchitectPort):
    """A deterministic architect that grounds the codified baseline in evidence."""

    def __init__(
        self,
        baseline: TokenBaseline = BASELINE,
        mappings: PlatformMappingFactory | None = None,
    ) -> None:
        self._baseline = baseline
        self._mappings = mappings or PlatformMappingFactory()

    async def architect(
        self, design_input: DesignSystemInput, evidence: EvidenceGraph
    ) -> DesignSystemDraft:
        cite = _CiteSource(evidence)
        brief = design_input.brief

        token_set = self._build_tokens(cite)
        component_specs = self._build_components(brief, cite)
        theme_set = self._build_themes(brief)
        localization = self._build_localization(brief)

        b = self._baseline
        return DesignSystemDraft(
            token_set=token_set,
            typography=TypographyScale(
                base_px=b.typography_base_px,
                ratio=Ratio.of(b.typography_ratio),
                role_tokens=b.typography_roles,
            ),
            spacing=SpacingScale(base_px=b.spacing_base_px, step_tokens=b.spacing_steps),
            radius=RadiusScale(step_tokens=b.radius_steps),
            elevation=ElevationScale(level_tokens=b.elevation_levels),
            shadow=ShadowScale(step_tokens=b.shadow_steps),
            border=BorderScale(width_tokens=b.border_widths),
            breakpoints=BreakpointSystem(b.breakpoints),
            grid=GridSystem(columns=b.grid_columns, gutter_tokens=b.grid_gutters),
            container=ContainerRules(b.container_widths),
            motion=MotionSystem(
                duration_tokens=b.motion_durations, easing_tokens=b.motion_easings
            ),
            interaction=InteractionTokens(
                focus_ring_token=b.focus_ring_token,
                hit_target_token=b.hit_target_token,
                transition_token=b.transition_token,
            ),
            states=self._build_states(),
            component_specs=component_specs,
            theme_set=theme_set,
            localization=localization,
        )

    # -- tokens ------------------------------------------------------------ #
    def _build_tokens(self, cite: _CiteSource) -> TokenSet:
        tokens: list[DesignToken] = []
        for bp in self._baseline.tokens:
            preferred = _CATEGORY_PROVENANCE.get(bp.category, _DEFAULT_TOKEN_PROVENANCE)
            value = (
                TokenValue.of(bp.literal)
                if bp.literal is not None
                else TokenValue.alias(bp.ref)
            )
            tokens.append(
                DesignToken(
                    id=TokenId.new(),
                    key=bp.key,
                    category=bp.category,
                    tier=bp.tier,
                    value=value,
                    description=bp.description,
                    citations=cite.cite(*preferred),
                )
            )
        return TokenSet.of(tokens)

    # -- states ------------------------------------------------------------ #
    def _build_states(self) -> tuple[StateTokens, ...]:
        return tuple(
            StateTokens(state=sb.state, token_refs=dict(sb.token_refs))
            for sb in self._baseline.states
        )

    def _state_lookup(self) -> dict[StateKind, StateBlueprint]:
        return {sb.state: sb for sb in self._baseline.states}

    # -- components -------------------------------------------------------- #
    def _build_components(self, brief, cite: _CiteSource) -> ComponentSpecSet:
        state_defs = self._state_lookup()
        specs: list[ComponentSpec] = []
        cycle = _COMPONENT_PROVENANCE_CYCLE
        for index, blueprint in enumerate(self._baseline.components):
            preferred = cycle[index % len(cycle)]
            specs.append(
                self._build_component(blueprint, state_defs, cite, preferred, brief)
            )
        return ComponentSpecSet.of(specs)

    def _build_component(
        self,
        blueprint: ComponentBlueprint,
        state_defs: dict[StateKind, StateBlueprint],
        cite: _CiteSource,
        preferred: ProvenanceKind,
        brief,
    ) -> ComponentSpec:
        properties = tuple(
            ComponentProperty(
                name=p.name,
                type=p.type,
                options=p.options,
                default=p.default,
                required=p.required,
            )
            for p in blueprint.properties
        )
        variants = tuple(
            ComponentVariant(name=v.name, property_values=dict(v.property_values),
                             description=v.description)
            for v in blueprint.variants
        )
        state_tokens = tuple(
            StateTokens(
                state=kind,
                token_refs=dict(state_defs[kind].token_refs) if kind in state_defs else {},
            )
            for kind in blueprint.states
        )
        states = ComponentStateSpec(states=state_tokens)
        responsive = ResponsiveSpec(behavior=dict(blueprint.responsive))
        accessibility = AccessibilitySpec(
            role=blueprint.role,
            keyboard=blueprint.keyboard,
            min_contrast=blueprint.min_contrast,
        )
        performance = PerformanceBudget(
            lazy_load=blueprint.lazy_load, blocks_lcp=blueprint.blocks_lcp
        )
        mappings = self._mappings.build(blueprint.component)
        mappings = self._restrict_platforms(mappings, brief)
        return ComponentSpec(
            id=ComponentSpecId.new(),
            component=blueprint.component,
            atomic_level=blueprint.atomic_level,
            token_refs=blueprint.token_refs,
            properties=properties,
            variants=variants,
            states=states,
            responsive=responsive,
            accessibility=accessibility,
            performance=performance,
            mappings=mappings,
            citations=cite.cite(preferred, ProvenanceKind.COMPONENT_INTELLIGENCE),
        )

    @staticmethod
    def _restrict_platforms(
        mappings: dict[Platform, PlatformMapping], brief
    ) -> dict[Platform, PlatformMapping]:
        # The developer contract plus the requested platforms are always present; unrequested
        # commerce platforms are still mapped (the spec requires all three) but this hook keeps
        # the door open to platform-specific tuning.
        return mappings

    # -- themes ------------------------------------------------------------ #
    def _build_themes(self, brief) -> ThemeSet:
        light = Theme(
            id=ThemeId.new(),
            mode=ThemeMode.LIGHT,
            name="Light",
            overrides=dict(self._baseline.light_theme),
        )
        if not brief.dark_mode:
            return ThemeSet.of([light])
        dark = Theme(
            id=ThemeId.new(),
            mode=ThemeMode.DARK,
            name="Dark",
            overrides=dict(self._baseline.dark_theme),
        )
        return ThemeSet.of([light, dark])

    # -- localization ------------------------------------------------------ #
    def _build_localization(self, brief) -> Localization:
        directions = brief.directions
        mirror = self._baseline.rtl_mirror_properties if Direction.RTL in directions else ()
        return Localization(
            directions=directions, locales=brief.locales, mirror_properties=mirror
        )
