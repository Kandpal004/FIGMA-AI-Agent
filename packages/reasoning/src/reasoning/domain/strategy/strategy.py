"""DesignStrategy — the aggregate the whole engine exists to produce.

A :class:`DesignStrategy` is the structured, cited answer to every strategic
question, together with the reason/decision/evidence graphs that justify it, the
risks it carries, its confidence, its trade-offs and alternatives, and any explicit
knowledge gaps. It is **directions, never designs**.

The aggregate enforces the platform's central promise at construction: **every
piece of evidence referenced anywhere in the strategy must exist in the evidence
graph, and every reason a decision cites must exist in the reason graph.** A
strategy that references a citation it does not carry cannot be built — so an
orphaned or fabricated claim is impossible by construction, not merely by
convention.

Pure domain: it composes the other domain models and performs no I/O. The
``created_at`` timestamp is supplied by the caller (the engine, via its clock).

Testing considerations
----------------------
* Constructing a strategy whose statement/decision/section/tradeoff/risk cites an
  evidence id absent from the evidence graph raises :class:`InvalidStrategyError`.
* Constructing a strategy whose decision cites a reason absent from the reason
  graph raises :class:`InvalidStrategyError`.
* :attr:`is_actionable` reflects confidence and the absence of critical risk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from core.errors import DesignDirectorError

from reasoning.domain.alternative.alternative import AlternativeStrategy
from reasoning.domain.confidence.confidence import StrategyConfidence
from reasoning.domain.evidence.evidence import EvidenceGraph
from reasoning.domain.graph.decision import DecisionGraph
from reasoning.domain.graph.reason import ReasonGraph
from reasoning.domain.risk.risk import RiskAssessment
from reasoning.domain.shared.ids import EvidenceId, ReasonNodeId, StrategyId, ReasoningRunId
from reasoning.domain.shared.value_objects import StrategyStance
from reasoning.domain.strategy.gap import KnowledgeGap
from reasoning.domain.strategy.sections import (
    BusinessObjective,
    CompetitiveStrategy,
    ConversionStrategy,
    CustomerProfile,
    ExperienceStrategy,
    PlatformStrategy,
    ReviewStrategy,
    VisualStrategy,
)
from reasoning.domain.strategy.statement import EvidencedStatement
from reasoning.domain.strategy.structure import StructureStrategy
from reasoning.domain.tradeoff.tradeoff import TradeOff

__all__ = ["DesignStrategy", "InvalidStrategyError"]


class InvalidStrategyError(DesignDirectorError):
    """Raised when a strategy violates an integrity invariant (a dangling
    evidence or reason reference)."""

    code = "invalid_strategy"
    http_status = 422


@dataclass(frozen=True, slots=True)
class DesignStrategy:
    """The complete, cited design strategy the engine produces."""

    id: StrategyId
    run_id: ReasoningRunId
    project_id: str
    section_id: str
    page_type: str
    stance: StrategyStance
    business: BusinessObjective
    customer: CustomerProfile
    conversion: ConversionStrategy
    experience: ExperienceStrategy
    platform: PlatformStrategy
    competitive: CompetitiveStrategy
    visual: VisualStrategy
    structure: StructureStrategy
    review: ReviewStrategy
    reason_graph: ReasonGraph
    decision_graph: DecisionGraph
    evidence_graph: EvidenceGraph
    risk_assessment: RiskAssessment
    confidence: StrategyConfidence
    created_at: datetime
    tradeoffs: tuple[TradeOff, ...] = ()
    alternatives: tuple[AlternativeStrategy, ...] = ()
    gaps: tuple[KnowledgeGap, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "tradeoffs", tuple(self.tradeoffs))
        object.__setattr__(self, "alternatives", tuple(self.alternatives))
        object.__setattr__(self, "gaps", tuple(self.gaps))
        self._validate_integrity()

    # -- integrity --------------------------------------------------------- #
    def _validate_integrity(self) -> None:
        """Enforce that every citation resolves within this strategy."""
        referenced_evidence: set[EvidenceId] = set()
        referenced_reasons: set[ReasonNodeId] = set()

        for statement in self.all_statements():
            referenced_evidence.update(statement.evidence_ids)
            if statement.reason_id is not None:
                referenced_reasons.add(statement.reason_id)
        referenced_evidence.update(self.structure.evidence_ids())
        for reason in self.reason_graph:
            referenced_evidence.update(reason.evidence_ids)
        for decision in self.decision_graph:
            referenced_evidence.update(decision.evidence_ids)
            referenced_reasons.update(decision.reason_ids)
        for tradeoff in self.tradeoffs:
            referenced_evidence.update(tradeoff.evidence_ids)
        for risk in self.risk_assessment.risks:
            referenced_evidence.update(risk.evidence_ids)

        missing_evidence = [e for e in referenced_evidence if not self.evidence_graph.has(e)]
        if missing_evidence:
            raise InvalidStrategyError(
                "Strategy references evidence absent from its evidence graph "
                "(no fabricated citations).",
                details={"missing_evidence": [str(e) for e in missing_evidence]},
            )
        missing_reasons = [r for r in referenced_reasons if not self.reason_graph.has(r)]
        if missing_reasons:
            raise InvalidStrategyError(
                "Strategy references reasons absent from its reason graph.",
                details={"missing_reasons": [str(r) for r in missing_reasons]},
            )

    # -- queries ----------------------------------------------------------- #
    def thematic_sections(self) -> tuple[object, ...]:
        """The eight statement-bearing sections (structure is handled separately)."""
        return (
            self.business,
            self.customer,
            self.conversion,
            self.experience,
            self.platform,
            self.competitive,
            self.visual,
            self.review,
        )

    def all_statements(self) -> tuple[EvidencedStatement, ...]:
        """Every evidenced statement across all thematic sections."""
        out: list[EvidencedStatement] = []
        for section in self.thematic_sections():
            out.extend(section.statements())  # type: ignore[attr-defined]
        return tuple(out)

    def evidence_count(self) -> int:
        """The number of distinct citations underpinning the strategy."""
        return len(self.evidence_graph)

    def decision_count(self) -> int:
        return len(self.decision_graph)

    @property
    def has_gaps(self) -> bool:
        """Whether any dimension was left ungrounded."""
        return bool(self.gaps)

    @property
    def is_actionable(self) -> bool:
        """Whether the strategy is sound enough to proceed to design.

        Requires at least moderate overall confidence and no critical, unaddressed
        risk. Design work must not begin on a strategy that fails this.
        """
        return self.confidence.overall.value >= 0.5 and not self.risk_assessment.has_critical
