"""Neutral application contracts — the data that crosses the engine's ports.

These are the vocabulary the pipeline speaks in, independent of any upstream engine:

* :class:`RawSignal` — one neutral fact an input adapter supplies (from any of the ten upstream
  engines). The evidence consolidator turns these into cited
  :class:`~design_system.domain.evidence.evidence.DSEvidence`.
* :class:`DesignSystemInput` — the assembled input to a run: the brief and project plus every
  raw signal gathered.
* :class:`DesignSystemDraft` — the token architect's proposed token set, scales, systems, state
  definitions, component specs, themes, and localization, each citing evidence by id. The engine
  validates grounding and token integrity, derives the constraints and the six graphs, scores,
  and assembles the specification.

Pure application: standard library, and the domain models the draft carries.
"""

from __future__ import annotations

from dataclasses import dataclass

from design_system.domain.component.spec import ComponentSpecSet
from design_system.domain.context.context import DesignSystemBrief, ProjectContext
from design_system.domain.shared.value_objects import ProvenanceKind
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

__all__ = ["DesignSystemDraft", "DesignSystemInput", "RawSignal"]


@dataclass(frozen=True, slots=True)
class RawSignal:
    """One neutral fact supplied by an input adapter.

    Attributes:
        provenance: Which source it came from.
        external_ref: Its id in that source (the audit anchor).
        claim: The crisp fact.
        confidence: Confidence in ``[0, 1]``.
        statement: Fuller supporting text, if any.
        source_name: A human-readable source label.
        tags: Free-form tags.
    """

    provenance: ProvenanceKind
    external_ref: str
    claim: str
    confidence: float = 0.7
    statement: str = ""
    source_name: str = ""
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "tags", tuple(self.tags))


@dataclass(frozen=True, slots=True)
class DesignSystemInput:
    """The assembled input to a design-system run."""

    brief: DesignSystemBrief
    project: ProjectContext
    signals: tuple[RawSignal, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "signals", tuple(self.signals))

    def signals_by(self, provenance: ProvenanceKind) -> tuple[RawSignal, ...]:
        return tuple(s for s in self.signals if s.provenance is provenance)


@dataclass(frozen=True, slots=True)
class DesignSystemDraft:
    """The token architect's proposed design system — cited, awaiting assembly.

    Carries everything the brain decides, each element citing evidence by id. The engine derives
    the constraints, the six graphs, and the quality picture, then assembles the specification.
    """

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

    def __post_init__(self) -> None:
        object.__setattr__(self, "states", tuple(self.states))
