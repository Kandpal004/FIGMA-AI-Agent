"""CompetitorIntelligenceReport — the aggregate the whole engine produces.

An immutable, versioned report: the classified competitors, their profiles, the
recurring patterns, the six analytical matrices (benchmark, gap, SWOT, best
practice, risk, recommendation), the evidence graph, and an overall confidence.

The aggregate enforces the platform's central promise at construction: **every
citation referenced anywhere in the report must resolve in its evidence graph.** A
report that references evidence it does not carry cannot be built — so an
opinion-based or fabricated citation is impossible by construction, not merely by
convention. Combined with the fact that recommendations, best practices, and
adopt/avoid patterns each *require* evidence at their own construction, this makes
"no opinion-based recommendations" a structural guarantee.

Versioning is lineage-based (``lineage_id`` + ``version``), consistent with Phases
3–4: a re-analysis mints a new version under the same lineage, and history is
retained. Pure domain — it composes the other models and performs no I/O; the
``created_at`` timestamp is supplied by the caller.

Testing considerations
----------------------
* Constructing a report whose recommendation/best-practice/pattern/gap/SWOT/risk
  cites an evidence id absent from the evidence graph raises
  :class:`InvalidReportError`.
* Version ``< 1`` is rejected.
* Convenience queries (patterns to adopt/avoid, profile lookup, tier filter) work.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from competitive.domain.competitor.competitor import Competitor
from competitive.domain.competitor.profile import CompetitorProfile
from competitive.domain.evidence.evidence import EvidenceGraph
from competitive.domain.matrix.benchmark import BenchmarkMatrix
from competitive.domain.matrix.best_practice import BestPracticeMatrix
from competitive.domain.matrix.gap import GapAnalysis
from competitive.domain.matrix.recommendation import RecommendationMatrix
from competitive.domain.matrix.risk import RiskMatrix
from competitive.domain.matrix.swot import SWOTMatrix
from competitive.domain.pattern.pattern import RecurringPattern
from competitive.domain.shared.ids import (
    CompetitorId,
    EvidenceId,
    ReportId,
    ReportLineageId,
)
from competitive.domain.shared.value_objects import (
    Confidence,
    CompetitorTier,
    RecommendationAction,
)

__all__ = ["CompetitorIntelligenceReport", "InvalidReportError"]


class InvalidReportError(DesignDirectorError):
    """Raised when a report violates an integrity invariant (a dangling citation)."""

    code = "invalid_report"
    http_status = 422


@dataclass(frozen=True, slots=True)
class CompetitorIntelligenceReport:
    """The complete, cited, versioned competitor intelligence report."""

    id: ReportId
    lineage_id: ReportLineageId
    version: int
    industry: str
    market: str
    country: str
    business_goals: tuple[str, ...]
    competitors: tuple[Competitor, ...]
    profiles: tuple[CompetitorProfile, ...]
    patterns: tuple[RecurringPattern, ...]
    benchmark: BenchmarkMatrix
    swot: SWOTMatrix
    gap_analysis: GapAnalysis
    best_practices: BestPracticeMatrix
    risk_matrix: RiskMatrix
    recommendations: RecommendationMatrix
    evidence_graph: EvidenceGraph
    confidence: Confidence
    created_at: datetime

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidReportError(
                "CompetitorIntelligenceReport.version must be >= 1.",
                details={"version": self.version},
            )
        object.__setattr__(self, "business_goals", tuple(self.business_goals))
        object.__setattr__(self, "competitors", tuple(self.competitors))
        object.__setattr__(self, "profiles", tuple(self.profiles))
        object.__setattr__(self, "patterns", tuple(self.patterns))
        self._validate_evidence_integrity()

    def _validate_evidence_integrity(self) -> None:
        referenced: set[EvidenceId] = set()
        for pattern in self.patterns:
            referenced.update(pattern.evidence_ids)
        for practice in self.best_practices.practices:
            referenced.update(practice.evidence_ids)
        for recommendation in self.recommendations.recommendations:
            referenced.update(recommendation.evidence_ids)
        for gap in self.gap_analysis.gaps:
            referenced.update(gap.evidence_ids)
        for item in self.swot.items:
            referenced.update(item.evidence_ids)
        for risk in self.risk_matrix.risks:
            referenced.update(risk.evidence_ids)

        missing = [e for e in referenced if not self.evidence_graph.has(e)]
        if missing:
            raise InvalidReportError(
                "Report references evidence absent from its evidence graph "
                "(no fabricated citations).",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    # -- queries ----------------------------------------------------------- #
    def patterns_to_adopt(self) -> tuple[RecurringPattern, ...]:
        return tuple(p for p in self.patterns if p.action is RecommendationAction.ADOPT)

    def patterns_to_avoid(self) -> tuple[RecurringPattern, ...]:
        return tuple(p for p in self.patterns if p.action is RecommendationAction.AVOID)

    def competitors_by_tier(self, tier: CompetitorTier) -> tuple[Competitor, ...]:
        return tuple(c for c in self.competitors if c.tier is tier)

    def profile_for(self, competitor_id: CompetitorId) -> CompetitorProfile | None:
        for profile in self.profiles:
            if profile.competitor_id == competitor_id:
                return profile
        return None

    def evidence_count(self) -> int:
        return len(self.evidence_graph)

    @property
    def is_actionable(self) -> bool:
        """Whether the report is sound enough to drive design decisions.

        Requires at least moderate confidence and at least one grounded
        recommendation.
        """
        return self.confidence.value >= 0.5 and len(self.recommendations) > 0
