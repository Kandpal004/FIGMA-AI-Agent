"""Recurring patterns — what the category does repeatedly, and whether to follow it.

A :class:`PatternInstance` records one competitor exhibiting a pattern on a
dimension. A :class:`RecurringPattern` aggregates instances into a category-wide
pattern with a measured :class:`Prevalence`, a recommended
:class:`RecommendationAction` (adopt / avoid / monitor), and — crucially — the
Knowledge-Engine citations that ground the recommendation. A pattern that
recommends an action must be evidence-backed; an ungrounded "adopt/avoid" cannot be
constructed.

Pure domain: standard library, the shared-kernel error base, competitive ids, and
shared value objects.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from core.errors import DesignDirectorError

from competitive.domain.shared.ids import CompetitorId, EvidenceId, PatternId
from competitive.domain.shared.value_objects import (
    CompetitorDimension,
    Confidence,
    PatternKind,
    Prevalence,
    RecommendationAction,
)

__all__ = ["InvalidPatternError", "PatternInstance", "RecurringPattern"]


class InvalidPatternError(DesignDirectorError):
    """Raised when a pattern is constructed with invalid data."""

    code = "invalid_pattern"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PatternInstance:
    """One competitor exhibiting a pattern on a dimension.

    Attributes:
        competitor_id: The competitor exhibiting it.
        dimension: The dimension it appears on.
        note: A short note on how it manifests.
    """

    competitor_id: CompetitorId
    dimension: CompetitorDimension
    note: str = ""


@dataclass(frozen=True, slots=True)
class RecurringPattern:
    """A pattern seen across competitors, with a grounded recommendation.

    Attributes:
        id: Pattern identity.
        kind: The category of pattern.
        dimension: The primary dimension it concerns.
        name: A short name.
        description: What the pattern is.
        prevalence: How common it is across the examined competitors.
        action: What to do about it (adopt / avoid / monitor).
        instances: The competitors exhibiting it.
        evidence_ids: Knowledge citations grounding the recommended action
            (required when the action is ADOPT or AVOID).
        confidence: Confidence in the pattern and its recommendation.
    """

    id: PatternId
    kind: PatternKind
    dimension: CompetitorDimension
    name: str
    description: str
    prevalence: Prevalence
    action: RecommendationAction
    confidence: Confidence
    instances: tuple[PatternInstance, ...] = ()
    evidence_ids: tuple[EvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidPatternError("RecurringPattern.name must be non-empty.")
        object.__setattr__(self, "instances", tuple(self.instances))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
        if (
            self.action in (RecommendationAction.ADOPT, RecommendationAction.AVOID)
            and not self.evidence_ids
        ):
            raise InvalidPatternError(
                "An ADOPT/AVOID pattern must cite Knowledge evidence (no opinions).",
                details={"pattern": self.name, "action": self.action.value},
            )

    @property
    def exemplar_competitor_ids(self) -> tuple[CompetitorId, ...]:
        """The competitors exhibiting the pattern, in order."""
        return tuple(i.competitor_id for i in self.instances)

    @property
    def is_recommended(self) -> bool:
        """Whether the pattern is recommended for adoption."""
        return self.action is RecommendationAction.ADOPT

    @classmethod
    def from_instances(
        cls,
        *,
        id: PatternId,
        kind: PatternKind,
        dimension: CompetitorDimension,
        name: str,
        description: str,
        instances: Sequence[PatternInstance],
        total_competitors: int,
        action: RecommendationAction,
        confidence: Confidence,
        evidence_ids: Sequence[EvidenceId] = (),
    ) -> RecurringPattern:
        """Build a pattern, deriving prevalence from its instances."""
        return cls(
            id=id,
            kind=kind,
            dimension=dimension,
            name=name,
            description=description,
            prevalence=Prevalence(count=len(instances), total=max(1, total_competitors)),
            action=action,
            confidence=confidence,
            instances=tuple(instances),
            evidence_ids=tuple(evidence_ids),
        )
