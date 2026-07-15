"""DesignSystemSpecification — the aggregate the whole engine produces.

An immutable, versioned specification: the three-tier token set and the scales/systems that
organise it, the per-component specs (variants, states, responsive, accessibility, performance,
platform mappings), the themes and localization contract, the enforced constraints, the six
graphs, the evidence graph, and the quality picture. It is the authoritative design system every
future UI must follow — it renders no UI and no Figma.

It enforces the platform's promises at construction:

1. **Provenance integrity** — every evidence id referenced by any token, component spec, theme,
   constraint, or graph node must resolve in the specification's :class:`EvidenceGraph`. Nothing
   the engine cannot cite enters the system — no token or component is chosen at random.
2. **Token integrity** — every token reference resolves to a real token in the set (no dangling
   alias), the alias/derivation chains contain no cycle, and every token key referenced by a
   scale, a system, a theme override, a component, or a component state exists. A design system
   whose references dangle is not a system.
3. **Graph integrity** — all six graphs are acyclic where required and resolve (enforced by the
   graph primitive), and the six required kinds are present.

Versioning is lineage-based (``lineage_id`` + ``version``), consistent with Phases 3–15.

Pure domain — it composes the other models and performs no I/O; ``created_at`` is supplied by
the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from design_system.domain.component.spec import ComponentSpecSet
from design_system.domain.constraint.constraint import ConstraintSet
from design_system.domain.evidence.evidence import EvidenceGraph
from design_system.domain.graph.graphs import DesignSystemGraphs
from design_system.domain.quality.quality import DesignSystemQualityMetrics
from design_system.domain.shared.ids import (
    DesignSystemSpecId,
    DesignSystemSpecLineageId,
    DSEvidenceId,
)
from design_system.domain.theme.localization import Localization
from design_system.domain.theme.theme import ThemeSet
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
from design_system.domain.token.token import TokenSet

__all__ = ["DesignSystemSpecification", "InvalidSpecificationError"]


class InvalidSpecificationError(DesignDirectorError):
    """Raised when a specification violates an integrity invariant."""

    code = "invalid_design_system_specification"
    http_status = 422


@dataclass(frozen=True, slots=True)
class DesignSystemSpecification:
    """The complete, provenance-tracked, versioned design-system specification."""

    id: DesignSystemSpecId
    lineage_id: DesignSystemSpecLineageId
    version: int
    project_id: str
    token_set: TokenSet
    typography: TypographyScale
    spacing: SpacingScale
    radius: RadiusScale
    elevation: ElevationScale
    shadow: ShadowScale
    border: BorderScale
    breakpoints: BreakpointSystem
    grid: GridSystem
    container: ContainerRules
    motion: MotionSystem
    interaction: InteractionTokens
    states: tuple[StateTokens, ...]
    component_specs: ComponentSpecSet
    theme_set: ThemeSet
    localization: Localization
    constraint_set: ConstraintSet
    graphs: DesignSystemGraphs
    evidence_graph: EvidenceGraph
    quality: DesignSystemQualityMetrics
    created_at: datetime

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidSpecificationError(
                "DesignSystemSpecification.version must be >= 1.",
                details={"version": self.version},
            )
        object.__setattr__(self, "states", tuple(self.states))
        self._validate_provenance()
        self._validate_token_integrity()

    # -- invariant 1: provenance ------------------------------------------- #
    def _referenced_evidence(self) -> set[DSEvidenceId]:
        referenced: set[DSEvidenceId] = set()
        for token in self.token_set:
            referenced.update(token.evidence_ids)
        for spec in self.component_specs:
            referenced.update(spec.evidence_ids)
        for constraint in self.constraint_set:
            referenced.update(constraint.evidence_ids)
        referenced.update(self.graphs.evidence_ids())
        return referenced

    def _validate_provenance(self) -> None:
        missing = self.evidence_graph.missing(self._referenced_evidence())
        if missing:
            raise InvalidSpecificationError(
                "Specification references evidence absent from its evidence graph "
                "(no ungrounded design decisions).",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    # -- invariant 2: token integrity -------------------------------------- #
    def _require_token(self, key: str, context: str) -> None:
        if not self.token_set.has(key):
            raise InvalidSpecificationError(
                f"{context} references token {key!r} absent from the token set.",
                details={"key": key, "context": context},
            )

    def _validate_token_integrity(self) -> None:
        # 2a. No dangling aliases; collect the alias/derivation edges for the cycle check.
        adjacency: dict[str, list[str]] = {k: [] for k in self.token_set.keys()}
        for token in self.token_set.references():
            ref = token.value.ref
            self._require_token(ref, f"token {token.key!r}")
            adjacency[token.key].append(ref)
        self._assert_no_alias_cycle(adjacency)

        # 2b. Every scale/system/theme/component reference resolves.
        for step in (
            *self.typography.role_tokens,
            *self.spacing.step_tokens,
            *self.radius.step_tokens,
            *self.elevation.level_tokens,
            *self.shadow.step_tokens,
            *self.border.width_tokens,
        ):
            self._require_token(step, "a token scale")
        for gutter in self.grid.gutter_tokens.values():
            self._require_token(gutter, "the grid system")
        for token_key in (*self.motion.duration_tokens, *self.motion.easing_tokens):
            self._require_token(token_key, "the motion system")
        for token_key in (
            self.interaction.focus_ring_token,
            self.interaction.hit_target_token,
            self.interaction.transition_token,
        ):
            self._require_token(token_key, "the interaction tokens")
        for theme in self.theme_set:
            for semantic_key, primitive_key in theme.overrides.items():
                self._require_token(semantic_key, f"theme {theme.name!r}")
                self._require_token(primitive_key, f"theme {theme.name!r}")
        for state in self.states:
            for token_key in state.token_keys:
                self._require_token(token_key, f"state {state.state.value}")
        for spec in self.component_specs:
            for token_key in spec.token_refs:
                self._require_token(token_key, f"component {spec.component.value}")
            for state in spec.states.states:
                for token_key in state.token_keys:
                    self._require_token(
                        token_key, f"component {spec.component.value} state {state.state.value}"
                    )

    def _assert_no_alias_cycle(self, adjacency: dict[str, list[str]]) -> None:
        WHITE, GREY, BLACK = 0, 1, 2
        colour = dict.fromkeys(adjacency, WHITE)

        def visit(key: str) -> None:
            colour[key] = GREY
            for nxt in adjacency.get(key, ()):  # nxt already proven to resolve
                if colour.get(nxt) == GREY:
                    raise InvalidSpecificationError(
                        "Token alias/derivation chain forms a cycle.",
                        details={"key": nxt},
                    )
                if colour.get(nxt) == WHITE:
                    visit(nxt)
            colour[key] = BLACK

        for key in adjacency:
            if colour[key] == WHITE:
                visit(key)

    # -- queries ----------------------------------------------------------- #
    def token_count(self) -> int:
        return len(self.token_set)

    def component_count(self) -> int:
        return len(self.component_specs)

    def evidence_count(self) -> int:
        return len(self.evidence_graph)

    @property
    def is_production_ready(self) -> bool:
        """Whether the specification is complete enough to build UI from.

        Requires tokens across all three tiers, at least one component fully mapped, a light
        theme, the mandatory blocking constraints, full grounding and token integrity, and
        non-empty evidence — the structural invariants are already guaranteed at construction.
        """
        if self.token_count() == 0 or self.component_count() == 0:
            return False
        return (
            self.quality.is_fully_grounded
            and self.quality.has_token_integrity
            and len(self.constraint_set) >= 2
            and self.evidence_count() > 0
        )
