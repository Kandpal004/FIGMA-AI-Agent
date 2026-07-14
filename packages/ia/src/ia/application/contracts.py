"""Neutral application contracts — the data that crosses the engine's ports.

These are the vocabulary the pipeline speaks in, independent of any upstream engine or
downstream consumer:

* :class:`RawSignal` — one neutral fact an input adapter supplies (from UX, Psychology,
  Brand, Business Strategy, Knowledge, Research, Competitor, or Reasoning). The evidence
  consolidator turns these into cited :class:`~ia.domain.evidence.evidence.IAEvidence`.
* :class:`IAInput` — the assembled input to a run: the brief and project plus every raw
  signal gathered.
* :class:`IADraft` — the architect's proposed *content* (the site map, navigation, page
  relationships, and product discovery), already citing evidence by id. The engine
  validates, builds the six graphs, scores, and assembles the report.

Pure application: standard library, and the domain models the draft carries.
"""

from __future__ import annotations

from dataclasses import dataclass

from ia.domain.context.context import IABrief, ProjectContext
from ia.domain.discovery.discovery import Discovery
from ia.domain.navigation.navigation import Navigation
from ia.domain.relationship.relationship import RelationshipSet
from ia.domain.shared.value_objects import ProvenanceKind
from ia.domain.sitemap.sitemap import SiteMap

__all__ = ["IADraft", "IAInput", "RawSignal"]


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
class IAInput:
    """The assembled input to an IA run."""

    brief: IABrief
    project: ProjectContext
    signals: tuple[RawSignal, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "signals", tuple(self.signals))

    def signals_by(self, provenance: ProvenanceKind) -> tuple[RawSignal, ...]:
        return tuple(s for s in self.signals if s.provenance is provenance)


@dataclass(frozen=True, slots=True)
class IADraft:
    """The architect's proposed content — cited, awaiting validation and assembly."""

    sitemap: SiteMap
    navigation: Navigation
    relationships: RelationshipSet
    discovery: Discovery
