"""The dimension-reasoner foundation — the pluggable unit of reasoning.

Each strategy dimension (business, customer, conversion, …) is reasoned by a small,
independent :class:`DimensionReasoner`. The engine composes them in a fixed order.
A reasoner reads the immutable :class:`ReasoningContext`, asks the
:class:`KnowledgeAdvisorPort` for the applicable cited principles, and returns a
:class:`DimensionResult` — its contribution of evidence, reason/decision nodes,
cited statements (keyed by :class:`StrategyOutputKey` so the engine can slot them
into the right section), section verdicts, trade-offs, and any knowledge gaps.

The :class:`ReasonerToolkit` removes boilerplate: it builds the domain objects
(pinning an :class:`AdvisedPrinciple` as an :class:`EvidenceRef`, constructing
reasons/decisions/statements) with fresh ids, so every reasoner produces
consistent, valid graph pieces. It holds no state and is injected.

This module is pure application logic — no I/O, no framework.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from reasoning.application.ports.knowledge_advisor import (
    AdvisedPrinciple,
    KnowledgeAdvisorPort,
)
from reasoning.domain.evidence.evidence import EvidenceRef
from reasoning.domain.graph.decision import DecisionNode, DecisionOption
from reasoning.domain.graph.reason import ReasonNode
from reasoning.domain.request.request import ReasoningContext
from reasoning.domain.shared.ids import (
    DecisionNodeId,
    EvidenceId,
    ReasonNodeId,
)
from reasoning.domain.shared.value_objects import ReasoningDimension
from reasoning.domain.strategy.gap import KnowledgeGap
from reasoning.domain.strategy.statement import EvidencedStatement
from reasoning.domain.strategy.structure import SectionRecommendation, SectionStatus
from reasoning.domain.tradeoff.tradeoff import TradeOff

__all__ = [
    "DimensionReasoner",
    "DimensionResult",
    "ReasonerToolkit",
    "StrategyOutputKey",
    "gather",
]


class StrategyOutputKey(str, Enum):
    """Keys under which a reasoner's cited statements are slotted into sections."""

    BUSINESS_OBJECTIVE = "business_objective"
    BUSINESS_SECONDARY = "business_secondary"
    CUSTOMER_WHO = "customer_who"
    TARGET_MARKET = "target_market"
    PROBLEMS = "problems"
    OBJECTIONS = "objections"
    EMOTIONAL_TRIGGERS = "emotional_triggers"
    TRUST_MECHANISMS = "trust_mechanisms"
    CRO_PRINCIPLES = "cro_principles"
    UX_PRINCIPLES = "ux_principles"
    ACCESSIBILITY_RULES = "accessibility_rules"
    SHOPIFY_CONSTRAINTS = "shopify_constraints"
    MAGENTO_CONSTRAINTS = "magento_constraints"
    COMPETITORS = "competitors"
    DESIGN_SYSTEM = "design_system"
    TYPOGRAPHY = "typography"
    SPACING = "spacing"
    VISUAL_HIERARCHY = "visual_hierarchy"
    REVIEW_POINTS = "review_points"


@dataclass(frozen=True, slots=True)
class DimensionResult:
    """One dimension reasoner's contribution to the strategy.

    Attributes:
        evidence: The evidence refs this reasoner pinned.
        reasons: The reason nodes it produced (premises must precede in order).
        decisions: The decision nodes it produced.
        outputs: Cited statements keyed by :class:`StrategyOutputKey`.
        sections: Section verdicts (used by the structure reasoner).
        tradeoffs: Any trade-offs it recorded.
        gaps: Any knowledge gaps it found.
    """

    evidence: tuple[EvidenceRef, ...] = ()
    reasons: tuple[ReasonNode, ...] = ()
    decisions: tuple[DecisionNode, ...] = ()
    outputs: Mapping[StrategyOutputKey, tuple[EvidencedStatement, ...]] = field(
        default_factory=lambda: MappingProxyType({})
    )
    sections: tuple[SectionRecommendation, ...] = ()
    tradeoffs: tuple[TradeOff, ...] = ()
    gaps: tuple[KnowledgeGap, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "reasons", tuple(self.reasons))
        object.__setattr__(self, "decisions", tuple(self.decisions))
        object.__setattr__(self, "sections", tuple(self.sections))
        object.__setattr__(self, "tradeoffs", tuple(self.tradeoffs))
        object.__setattr__(self, "gaps", tuple(self.gaps))
        if not isinstance(self.outputs, MappingProxyType):
            object.__setattr__(self, "outputs", MappingProxyType(dict(self.outputs)))

    def get(self, key: StrategyOutputKey) -> tuple[EvidencedStatement, ...]:
        """All statements under ``key`` (empty if none)."""
        return self.outputs.get(key, ())

    def first(self, key: StrategyOutputKey) -> EvidencedStatement | None:
        """The first statement under ``key``, or ``None``."""
        statements = self.outputs.get(key, ())
        return statements[0] if statements else None

    @classmethod
    def merge(cls, *results: "DimensionResult") -> "DimensionResult":
        """Concatenate several results into one (evidence, graphs, outputs, …)."""
        evidence: tuple[EvidenceRef, ...] = ()
        reasons: tuple[ReasonNode, ...] = ()
        decisions: tuple[DecisionNode, ...] = ()
        sections: tuple[SectionRecommendation, ...] = ()
        tradeoffs: tuple[TradeOff, ...] = ()
        gaps: tuple[KnowledgeGap, ...] = ()
        outputs: dict[StrategyOutputKey, tuple[EvidencedStatement, ...]] = {}
        for result in results:
            evidence += result.evidence
            reasons += result.reasons
            decisions += result.decisions
            sections += result.sections
            tradeoffs += result.tradeoffs
            gaps += result.gaps
            for key, statements in result.outputs.items():
                outputs[key] = outputs.get(key, ()) + statements
        return cls(
            evidence=evidence,
            reasons=reasons,
            decisions=decisions,
            outputs=outputs,
            sections=sections,
            tradeoffs=tradeoffs,
            gaps=gaps,
        )


class ReasonerToolkit:
    """Stateless helper that builds valid domain objects with fresh ids.

    Injected into every reasoner so graph pieces are constructed consistently.
    """

    def evidence(
        self, advised: AdvisedPrinciple, dimension: ReasoningDimension
    ) -> EvidenceRef:
        """Pin an advised principle as an :class:`EvidenceRef` for a dimension."""
        return EvidenceRef(
            id=EvidenceId.new(),
            knowledge_id=advised.knowledge_id,
            entry_version_id=advised.entry_version_id,
            dimension=dimension,
            category=advised.category,
            title=advised.title,
            statement=advised.statement,
            source_name=advised.source_name,
            confidence=advised.confidence,
            relevance=advised.relevance,
        )

    def reason(
        self,
        dimension: ReasoningDimension,
        question: str,
        conclusion: str,
        *,
        confidence: float,
        evidence_ids: Sequence[EvidenceId] = (),
        premise_ids: Sequence[ReasonNodeId] = (),
    ) -> ReasonNode:
        return ReasonNode(
            id=ReasonNodeId.new(),
            dimension=dimension,
            question=question,
            conclusion=conclusion,
            confidence=confidence,
            evidence_ids=tuple(evidence_ids),
            premise_ids=tuple(premise_ids),
        )

    def option(
        self,
        label: str,
        *,
        evidence_ids: Sequence[EvidenceId] = (),
        score: float = 0.0,
        note: str = "",
    ) -> DecisionOption:
        return DecisionOption(
            label=label, evidence_ids=tuple(evidence_ids), score=score, note=note
        )

    def decision(
        self,
        dimension: ReasoningDimension,
        question: str,
        chosen: DecisionOption,
        *,
        confidence: float,
        considered: Sequence[DecisionOption] = (),
        reason_ids: Sequence[ReasonNodeId] = (),
        depends_on: Sequence[DecisionNodeId] = (),
    ) -> DecisionNode:
        return DecisionNode(
            id=DecisionNodeId.new(),
            dimension=dimension,
            question=question,
            chosen=chosen,
            confidence=confidence,
            considered=tuple(considered),
            reason_ids=tuple(reason_ids),
            depends_on=tuple(depends_on),
        )

    def statement(
        self,
        dimension: ReasoningDimension,
        text: str,
        *,
        evidence_ids: Sequence[EvidenceId],
        confidence: float,
        reason_id: ReasonNodeId | None = None,
    ) -> EvidencedStatement:
        return EvidencedStatement(
            dimension=dimension,
            statement=text,
            evidence_ids=tuple(evidence_ids),
            confidence=confidence,
            reason_id=reason_id,
        )

    def section(
        self,
        name: str,
        status: SectionStatus,
        rationale: str,
        *,
        evidence_ids: Sequence[EvidenceId],
        confidence: float,
        order: int = 0,
    ) -> SectionRecommendation:
        return SectionRecommendation(
            name=name,
            status=status,
            rationale=rationale,
            evidence_ids=tuple(evidence_ids),
            confidence=confidence,
            order=order,
        )

    def gap(
        self,
        dimension: ReasoningDimension,
        question: str,
        *,
        detail: str = "",
        suggested_action: str = "Escalate to the Creative Director for authoring.",
    ) -> KnowledgeGap:
        return KnowledgeGap(
            dimension=dimension,
            question=question,
            detail=detail,
            suggested_action=suggested_action,
        )


@runtime_checkable
class DimensionReasoner(Protocol):
    """A pluggable reasoner for one (or a few) strategy dimensions."""

    @property
    def name(self) -> str:
        """A stable name for logging and ordering."""
        ...

    async def reason(
        self,
        context: ReasoningContext,
        advisor: KnowledgeAdvisorPort,
        toolkit: ReasonerToolkit,
    ) -> DimensionResult:
        """Produce this dimension's contribution to the strategy."""
        ...


async def gather(
    advisor: KnowledgeAdvisorPort,
    toolkit: ReasonerToolkit,
    context: ReasoningContext,
    dimension: ReasoningDimension,
    output_key: StrategyOutputKey,
    question: str,
    *,
    limit: int = 3,
) -> DimensionResult:
    """The standard single-dimension reasoning step.

    Asks the advisor for the applicable cited principles; for each, pins an
    :class:`EvidenceRef`, records a grounded :class:`ReasonNode`, and emits a cited
    :class:`EvidencedStatement` under ``output_key``. If the corpus is silent, it
    records a :class:`KnowledgeGap` instead of inventing an answer.
    """
    req = context.request
    principles = await advisor.advise(
        dimension,
        page_type=req.page_type,
        component_type=req.component_type,
        platform=req.platform,
        contexts=req.contexts,
        tenant_id=context.tenant_id,
        limit=limit,
    )
    if not principles:
        return DimensionResult(gaps=(toolkit.gap(dimension, question),))

    evidence: list[EvidenceRef] = []
    reasons: list[ReasonNode] = []
    statements: list[EvidencedStatement] = []
    for principle in principles:
        ref = toolkit.evidence(principle, dimension)
        reason = toolkit.reason(
            dimension, question, principle.statement,
            confidence=principle.confidence, evidence_ids=(ref.id,),
        )
        statement = toolkit.statement(
            dimension, principle.statement,
            evidence_ids=(ref.id,), confidence=principle.confidence, reason_id=reason.id,
        )
        evidence.append(ref)
        reasons.append(reason)
        statements.append(statement)

    return DimensionResult(
        evidence=tuple(evidence),
        reasons=tuple(reasons),
        outputs={output_key: tuple(statements)},
    )
