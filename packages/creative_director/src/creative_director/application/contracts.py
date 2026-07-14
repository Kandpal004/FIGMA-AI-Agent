"""Neutral application contracts — the data that crosses the engine's ports.

These are the vocabulary the pipeline speaks in, independent of any upstream engine:

* :class:`RawSignal` — one neutral fact an input adapter supplies (from any of the ten
  upstream engines, or a human reviewer). The evidence consolidator turns these into cited
  :class:`~creative_director.domain.evidence.evidence.CDEvidence`.
* :class:`ReviewInput` — the assembled input to a run: the subject and project plus every raw
  signal gathered.
* :class:`ReviewDraft` — the critic panel's proposed :class:`DimensionReview` s, already
  citing evidence by id. The engine validates grounding, scores, evaluates approval, builds
  the graphs and matrices, and assembles the review.

Pure application: standard library, and the domain models the draft carries.
"""

from __future__ import annotations

from dataclasses import dataclass

from creative_director.domain.context.context import ProjectContext, ReviewSubject
from creative_director.domain.review.dimension_review import DimensionReview
from creative_director.domain.shared.value_objects import ProvenanceKind

__all__ = ["RawSignal", "ReviewDraft", "ReviewInput"]


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
class ReviewInput:
    """The assembled input to a Creative Director review run."""

    subject: ReviewSubject
    project: ProjectContext
    signals: tuple[RawSignal, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "signals", tuple(self.signals))

    def signals_by(self, provenance: ProvenanceKind) -> tuple[RawSignal, ...]:
        return tuple(s for s in self.signals if s.provenance is provenance)


@dataclass(frozen=True, slots=True)
class ReviewDraft:
    """The critic panel's proposed dimension reviews — cited, awaiting scoring and approval."""

    dimension_reviews: tuple[DimensionReview, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "dimension_reviews", tuple(self.dimension_reviews))
