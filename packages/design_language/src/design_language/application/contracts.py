"""Neutral application contracts — the data that crosses the engine's ports.

These are the vocabulary the pipeline speaks in, independent of any upstream engine:

* :class:`RawSignal` — one neutral fact an input adapter supplies (from Business Strategy,
  Brand, Psychology, the Creative Director, Knowledge, Research, or Competitor). The evidence
  consolidator turns these into cited :class:`~design_language.domain.evidence.evidence.DLEvidence`.
* :class:`LanguageInput` — the assembled input to a run: the brief and project plus every raw
  signal gathered.
* :class:`LanguageDraft` — the designer's proposed language: the Visual DNA, the token system,
  the philosophies and personalities, the grid and responsive systems, and the language
  selection, citing evidence by id. The engine validates grounding, derives the rules and
  graphs and explanation, scores, and assembles the specification.

Pure application: standard library, and the domain models the draft carries.
"""

from __future__ import annotations

from dataclasses import dataclass

from design_language.domain.context.context import DesignBrief, ProjectContext
from design_language.domain.dna.visual_dna import VisualDNA
from design_language.domain.language.selection import LanguageSelection
from design_language.domain.personality.personality import PersonalitySet
from design_language.domain.philosophy.philosophy import PhilosophySet
from design_language.domain.shared.value_objects import ProvenanceKind
from design_language.domain.system.grid_system import GridSystem
from design_language.domain.system.responsive import ResponsiveStrategy
from design_language.domain.tokens.visual_tokens import VisualTokens

__all__ = ["LanguageDraft", "LanguageInput", "RawSignal"]


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
class LanguageInput:
    """The assembled input to a design-language run."""

    brief: DesignBrief
    project: ProjectContext
    signals: tuple[RawSignal, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "signals", tuple(self.signals))

    def signals_by(self, provenance: ProvenanceKind) -> tuple[RawSignal, ...]:
        return tuple(s for s in self.signals if s.provenance is provenance)


@dataclass(frozen=True, slots=True)
class LanguageDraft:
    """The designer's proposed language — cited, awaiting rules, graphs, and assembly."""

    visual_dna: VisualDNA
    tokens: VisualTokens
    philosophies: PhilosophySet
    personalities: PersonalitySet
    grid_system: GridSystem
    responsive_strategy: ResponsiveStrategy
    language_selection: LanguageSelection
