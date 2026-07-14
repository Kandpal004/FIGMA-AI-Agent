"""Neutral application contracts — the data that crosses the engine's ports.

These are the vocabulary the pipeline speaks in, independent of any upstream engine or
downstream consumer:

* :class:`RawInsight` — one neutral fact an input adapter supplies (from Research,
  Knowledge, Competitor, Reasoning, or a future source). The evidence consolidator
  turns these into cited :class:`~strategy.domain.evidence.evidence.StrategyEvidence`.
* :class:`StrategyInput` — the assembled input to a strategy run: the brand, project,
  and goal context plus every raw insight gathered.
* :class:`StrategyDraft` — the strategist's proposed *content* (the eight pillars plus
  risks and opportunities), already citing evidence by id. The engine validates,
  lifts it into decisions and graphs, prioritises, scores, and assembles the report.

Pure application: standard library, and the domain models the draft carries.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from strategy.domain.analysis.opportunity import (
    BusinessOpportunity,
    RevenueOpportunity,
)
from strategy.domain.analysis.risk import BusinessRisk
from strategy.domain.context.context import BrandContext, GoalContext, ProjectContext
from strategy.domain.customer.model import CustomerModel
from strategy.domain.goals.business_goal import GoalSet
from strategy.domain.messaging.brand_voice import BrandPersonality, BrandVoice
from strategy.domain.messaging.messaging import MessagingFramework
from strategy.domain.positioning.positioning import PositioningStrategy
from strategy.domain.pricing.pricing import PricingStrategy
from strategy.domain.retention.retention import RetentionStrategy
from strategy.domain.shared.value_objects import ProvenanceKind
from strategy.domain.trust.trust import TrustStrategy
from strategy.domain.value.usp import UniqueSellingProposition
from strategy.domain.value.value_proposition import ValueProposition

__all__ = ["RawInsight", "StrategyDraft", "StrategyInput"]


@dataclass(frozen=True, slots=True)
class RawInsight:
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
class StrategyInput:
    """The assembled input to a strategy run."""

    brand: BrandContext
    project: ProjectContext
    goals: GoalContext
    insights: tuple[RawInsight, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "insights", tuple(self.insights))

    def insights_by(self, provenance: ProvenanceKind) -> tuple[RawInsight, ...]:
        return tuple(i for i in self.insights if i.provenance is provenance)


@dataclass(frozen=True, slots=True)
class StrategyDraft:
    """The strategist's proposed content — cited, awaiting validation and assembly."""

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
    risks: tuple[BusinessRisk, ...] = ()
    business_opportunities: tuple[BusinessOpportunity, ...] = ()
    revenue_opportunities: tuple[RevenueOpportunity, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "risks", tuple(self.risks))
        object.__setattr__(
            self, "business_opportunities", tuple(self.business_opportunities)
        )
        object.__setattr__(
            self, "revenue_opportunities", tuple(self.revenue_opportunities)
        )
