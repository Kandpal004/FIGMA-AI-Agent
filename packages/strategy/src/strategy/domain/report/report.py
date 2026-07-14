"""BusinessStrategyReport — the aggregate the whole engine produces.

An immutable, versioned report: the business goals, the customer model, the eight
positioning pillars (positioning, value, USP, messaging, brand voice/personality,
trust, pricing, retention), the decision and strategy graphs, the priority matrix, the
risk and opportunity registers, and an overall quality picture.

It enforces the platform's anti-hallucination promise at construction:

1. **Provenance integrity** — every evidence id referenced by any section, decision,
   graph edge, prioritized item, risk, or opportunity must resolve in the report's
   :class:`EvidenceGraph`. A strategy that references something it cannot cite cannot
   be built — so an ungrounded decision is impossible by construction.
2. **Decision reference integrity** — every prioritized item references a decision that
   exists in the decision graph.

Versioning is lineage-based (``lineage_id`` + ``version``), consistent with Phases
3–6: re-running strategy mints a new version under the same lineage, and history is
retained. Pure domain — it composes the other models and performs no I/O;
``created_at`` is supplied by the caller.

Testing considerations
----------------------
* A report whose any part references an evidence id absent from the evidence graph
  raises :class:`InvalidStrategyReportError`.
* A report whose priority matrix references a decision absent from the decision graph
  raises :class:`InvalidStrategyReportError`.
* Version ``< 1`` is rejected; convenience queries work.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.errors import DesignDirectorError

from strategy.domain.analysis.opportunity import OpportunityRegister
from strategy.domain.analysis.risk import RiskRegister
from strategy.domain.customer.model import CustomerModel
from strategy.domain.decision.decision_graph import DecisionGraph
from strategy.domain.decision.strategy_graph import StrategyGraph
from strategy.domain.evidence.evidence import EvidenceGraph
from strategy.domain.goals.business_goal import GoalSet
from strategy.domain.messaging.brand_voice import BrandPersonality, BrandVoice
from strategy.domain.messaging.messaging import MessagingFramework
from strategy.domain.positioning.positioning import PositioningStrategy
from strategy.domain.pricing.pricing import PricingStrategy
from strategy.domain.prioritization.priority_matrix import PriorityMatrix
from strategy.domain.quality.quality import StrategyQualityMetrics
from strategy.domain.retention.retention import RetentionStrategy
from strategy.domain.shared.ids import (
    StrategyEvidenceId,
    StrategyReportId,
    StrategyReportLineageId,
)
from strategy.domain.shared.value_objects import StrategyTier
from strategy.domain.trust.trust import TrustStrategy
from strategy.domain.value.usp import UniqueSellingProposition
from strategy.domain.value.value_proposition import ValueProposition

__all__ = ["InvalidStrategyReportError", "ReportThresholds", "BusinessStrategyReport"]


class InvalidStrategyReportError(DesignDirectorError):
    """Raised when a report violates an integrity invariant (ungrounded or dangling)."""

    code = "invalid_strategy_report"
    http_status = 422


class ReportThresholds:
    """Named thresholds used by :attr:`BusinessStrategyReport.is_usable`."""

    MIN_OVERALL = 40.0


@dataclass(frozen=True, slots=True)
class BusinessStrategyReport:
    """The complete, provenance-tracked, versioned business strategy report."""

    id: StrategyReportId
    lineage_id: StrategyReportLineageId
    version: int
    project_id: str
    goals: GoalSet
    customer: CustomerModel
    positioning: PositioningStrategy
    value_proposition: ValueProposition
    usp: UniqueSellingProposition
    messaging: MessagingFramework
    brand_voice: BrandVoice
    brand_personality: BrandPersonality
    trust: TrustStrategy
    pricing: PricingStrategy
    retention: RetentionStrategy
    decision_graph: DecisionGraph
    strategy_graph: StrategyGraph
    priority_matrix: PriorityMatrix
    risk_register: RiskRegister
    opportunity_register: OpportunityRegister
    evidence_graph: EvidenceGraph
    quality: StrategyQualityMetrics
    created_at: datetime

    def __post_init__(self) -> None:
        if self.version < 1:
            raise InvalidStrategyReportError(
                "BusinessStrategyReport.version must be >= 1.",
                details={"version": self.version},
            )
        self._validate_provenance()
        self._validate_decision_references()

    # -- invariants -------------------------------------------------------- #
    def _referenced_evidence(self) -> set[StrategyEvidenceId]:
        referenced: set[StrategyEvidenceId] = set()
        referenced.update(self.goals.evidence_ids())
        referenced.update(self.customer.evidence_ids())
        referenced.update(self.positioning.evidence_ids())
        referenced.update(self.value_proposition.evidence_ids)
        referenced.update(self.usp.evidence_ids)
        referenced.update(self.messaging.all_evidence_ids())
        referenced.update(self.brand_voice.evidence_ids)
        referenced.update(self.brand_personality.evidence_ids)
        referenced.update(self.trust.all_evidence_ids())
        referenced.update(self.pricing.all_evidence_ids())
        referenced.update(self.retention.all_evidence_ids())
        for decision in self.decision_graph:
            referenced.update(decision.evidence_ids)
        for edge in self.decision_graph.edges:
            referenced.update(edge.evidence_ids)
        referenced.update(self.priority_matrix.evidence_ids())
        referenced.update(self.risk_register.evidence_ids())
        referenced.update(self.opportunity_register.evidence_ids())
        return referenced

    def _validate_provenance(self) -> None:
        missing = self.evidence_graph.missing(self._referenced_evidence())
        if missing:
            raise InvalidStrategyReportError(
                "Report references evidence absent from its evidence graph "
                "(no ungrounded decisions).",
                details={"missing_evidence": [str(e) for e in missing]},
            )

    def _validate_decision_references(self) -> None:
        dangling = [
            str(did)
            for did in self.priority_matrix.decision_ids()
            if not self.decision_graph.has(did)
        ]
        if dangling:
            raise InvalidStrategyReportError(
                "Priority matrix references decisions absent from the decision graph.",
                details={"missing_decisions": dangling},
            )

    # -- queries ----------------------------------------------------------- #
    @property
    def tier(self) -> StrategyTier:
        return self.positioning.tier

    def decision_count(self) -> int:
        return len(self.decision_graph)

    def evidence_count(self) -> int:
        return len(self.evidence_graph)

    @property
    def is_usable(self) -> bool:
        """Whether the strategy is good enough to drive downstream design.

        Requires a passing overall score, full grounding, and — since positioning is
        the keystone every design decision derives from — a committed positioning.
        """
        return (
            self.quality.overall_score.value >= ReportThresholds.MIN_OVERALL
            and self.quality.is_fully_grounded
            and self.evidence_count() > 0
        )
