"""Neutral application contracts — the data that crosses the engine's ports.

These are the vocabulary the pipeline speaks in, independent of any upstream engine:

* :class:`RawSignal` — one neutral fact an input adapter supplies (from any upstream engine). The
  evidence consolidator turns these into cited
  :class:`~figma_design.domain.evidence.evidence.FDEvidence`.
* :class:`FigmaInput` — the assembled input to a run: the brief, project, source refs, and every
  raw signal gathered.
* :class:`FigmaDraft` — the composer's proposed pages (with layer trees), variable collections,
  style set, and component-set catalog, each citing evidence by id. The engine resolves the
  variable/style/instance bindings, builds the five graphs, scores, and assembles the model.

Pure application: standard library, and the domain models the draft carries. It imports no Figma
SDK, MCP client, or HTTP library.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from figma_design.domain.component.component_set import ComponentSetCatalog
from figma_design.domain.context.context import FigmaBrief, ProjectContext, SourceRefs
from figma_design.domain.page.page import FigmaPage
from figma_design.domain.shared.value_objects import ProvenanceKind
from figma_design.domain.style.style import StyleSet
from figma_design.domain.variable.collection import VariableCollection

__all__ = ["FigmaDraft", "FigmaInput", "RawSignal"]


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
class FigmaInput:
    """The assembled input to a Figma-modelling run."""

    brief: FigmaBrief
    project: ProjectContext
    source_refs: SourceRefs = field(default_factory=SourceRefs)
    signals: tuple[RawSignal, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "signals", tuple(self.signals))

    def signals_by(self, provenance: ProvenanceKind) -> tuple[RawSignal, ...]:
        return tuple(s for s in self.signals if s.provenance is provenance)


@dataclass(frozen=True, slots=True)
class FigmaDraft:
    """The composer's proposed model — cited, awaiting resolution and assembly.

    Carries the organized pages (with layer trees), variable collections, published styles, and
    component-set catalog the composer built. The engine resolves the bindings, derives the five
    graphs, and assembles the versioned model.
    """

    pages: tuple[FigmaPage, ...]
    collections: tuple[VariableCollection, ...]
    style_set: StyleSet
    component_sets: ComponentSetCatalog

    def __post_init__(self) -> None:
        object.__setattr__(self, "pages", tuple(self.pages))
        object.__setattr__(self, "collections", tuple(self.collections))

    @property
    def nodes(self) -> tuple:
        return tuple(node for page in self.pages for node in page.tree)
