"""Neutral application contracts — the data that crosses the engine's ports.

These are the vocabulary the pipeline speaks in, independent of any upstream engine or
downstream consumer:

* :class:`RawSignal` — one neutral fact an input adapter supplies (from Business
  Strategy, Knowledge, Research, Competitor, or Reasoning). The evidence consolidator
  turns these into cited :class:`~brand.domain.evidence.evidence.BrandEvidence`.
* :class:`BrandInput` — the assembled input to a brand run: the brand brief and project
  plus every raw signal gathered.
* :class:`BrandDraft` — the strategist's proposed brand *content* (classification,
  identity, character, emotional strategy, visual direction, verbal system), already
  citing evidence by id. The engine validates, lifts it into decisions, derives
  governance, scores, and assembles the report.

Pure application: standard library, and the domain models the draft carries.
"""

from __future__ import annotations

from dataclasses import dataclass

from brand.domain.classification.classification import BrandClassification
from brand.domain.context.context import BrandBrief, ProjectContext
from brand.domain.emotional.emotional_strategy import EmotionalStrategy
from brand.domain.identity.identity import BrandIdentity
from brand.domain.personality.character import BrandCharacter
from brand.domain.shared.value_objects import ProvenanceKind
from brand.domain.verbal.verbal_system import BrandVerbalSystem
from brand.domain.visual.visual_direction import BrandVisualDirection

__all__ = ["BrandDraft", "BrandInput", "RawSignal"]


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
class BrandInput:
    """The assembled input to a brand run."""

    brief: BrandBrief
    project: ProjectContext
    signals: tuple[RawSignal, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "signals", tuple(self.signals))

    def signals_by(self, provenance: ProvenanceKind) -> tuple[RawSignal, ...]:
        return tuple(s for s in self.signals if s.provenance is provenance)


@dataclass(frozen=True, slots=True)
class BrandDraft:
    """The strategist's proposed brand content — cited, awaiting validation and assembly."""

    classification: BrandClassification
    identity: BrandIdentity
    character: BrandCharacter
    emotional: EmotionalStrategy
    visual: BrandVisualDirection
    verbal: BrandVerbalSystem
