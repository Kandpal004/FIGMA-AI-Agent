"""Observations — the engine's structured input unit.

An :class:`Observation` is one structured finding about a competitor on one
dimension, with its provenance and confidence. It is what the data-source port
delivers (manual today; Firecrawl/Playwright/MCP/etc. later) — the engine never
fetches, it *synthesises* observations into knowledge. An optional ``strength``
carries a numeric signal (0–100) the benchmark analyzer folds into a dimension
score.

An :class:`ObservationSet` is an immutable collection with the query helpers the
profile and benchmark analyzers need.

Pure domain: standard library, the shared-kernel error base, competitive ids, and
shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from competitive.domain.shared.ids import CompetitorId, ObservationId
from competitive.domain.shared.value_objects import (
    CompetitorDimension,
    Confidence,
    ObservationSource,
    Score,
)

__all__ = ["InvalidObservationError", "Observation", "ObservationSet"]


class InvalidObservationError(DesignDirectorError):
    """Raised when an observation is constructed with invalid data."""

    code = "invalid_observation"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Observation:
    """One structured finding about a competitor on one dimension.

    Attributes:
        id: Observation identity.
        competitor_id: The competitor observed.
        dimension: The dimension the finding concerns.
        finding: The structured finding (a fact, not an opinion).
        source: Where the observation came from.
        confidence: How confident the source is in the finding.
        strength: An optional 0–100 signal of the competitor's strength on this
            dimension (folded into the benchmark score); ``None`` if not scored.
    """

    id: ObservationId
    competitor_id: CompetitorId
    dimension: CompetitorDimension
    finding: str
    source: ObservationSource
    confidence: Confidence
    strength: Score | None = None

    def __post_init__(self) -> None:
        if not self.finding or not self.finding.strip():
            raise InvalidObservationError("Observation.finding must be non-empty.")


@dataclass(frozen=True, slots=True)
class ObservationSet:
    """An immutable collection of observations with query helpers."""

    observations: tuple[Observation, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "observations", tuple(self.observations))

    @classmethod
    def of(cls, observations: Iterable[Observation]) -> ObservationSet:
        return cls(observations=tuple(observations))

    def __len__(self) -> int:
        return len(self.observations)

    def __iter__(self):
        return iter(self.observations)

    def for_competitor(self, competitor_id: CompetitorId) -> tuple[Observation, ...]:
        return tuple(o for o in self.observations if o.competitor_id == competitor_id)

    def for_dimension(self, dimension: CompetitorDimension) -> tuple[Observation, ...]:
        return tuple(o for o in self.observations if o.dimension is dimension)

    def select(
        self, competitor_id: CompetitorId, dimension: CompetitorDimension
    ) -> tuple[Observation, ...]:
        """Observations for a specific competitor and dimension."""
        return tuple(
            o
            for o in self.observations
            if o.competitor_id == competitor_id and o.dimension is dimension
        )

    def competitor_ids(self) -> tuple[CompetitorId, ...]:
        """The distinct competitor ids observed, in first-seen order."""
        seen: list[CompetitorId] = []
        for o in self.observations:
            if o.competitor_id not in seen:
                seen.append(o.competitor_id)
        return tuple(seen)
