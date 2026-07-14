"""Page objectives and success metrics — why a page exists, and how it is measured.

A :class:`PageObjective` states the single reason a page exists and the user + business
goals it serves. A :class:`SuccessMetric` names how the page's success is measured. Both
cited — every page's purpose and measurability trace to evidence.

Pure domain: standard library, the shared-kernel error base, UX ids, and shared value
objects.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.errors import DesignDirectorError

from ux.domain.shared.ids import SuccessMetricId, UXEvidenceId
from ux.domain.shared.value_objects import MetricKind, Priority

__all__ = ["InvalidObjectiveError", "PageObjective", "SuccessMetric"]


class InvalidObjectiveError(DesignDirectorError):
    """Raised when a page objective/metric is constructed with invalid data."""

    code = "invalid_page_objective"
    http_status = 422


@dataclass(frozen=True, slots=True)
class PageObjective:
    """The cited reason a page exists.

    Attributes:
        statement: The page's single objective.
        why_it_exists: Why the page exists at all (its reason to be).
        serves_user_goal: The user goal it serves.
        serves_business_goal: The business goal it serves.
        evidence_ids: The evidence supporting it.
    """

    statement: str
    why_it_exists: str
    serves_user_goal: str = ""
    serves_business_goal: str = ""
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.statement or not self.statement.strip():
            raise InvalidObjectiveError("PageObjective.statement must be non-empty.")
        if not self.why_it_exists or not self.why_it_exists.strip():
            raise InvalidObjectiveError("PageObjective.why_it_exists must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class SuccessMetric:
    """A cited metric by which a page's success is measured.

    Attributes:
        id: Metric identity.
        kind: The kind of metric.
        target: The target/direction (e.g. "increase", "> 3%").
        priority: Its priority among the page's metrics.
        evidence_ids: The evidence supporting it.
    """

    id: SuccessMetricId
    kind: MetricKind
    target: str = ""
    priority: Priority = Priority(3)
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
