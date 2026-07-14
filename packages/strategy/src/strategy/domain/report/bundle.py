"""The Design Directive Bundle — the neutral brief downstream design phases consume.

The Business Strategy Engine is the source of truth every UX/UI/Figma decision must
derive from — but it must not depend on those phases. So it emits a
:class:`DesignDirectiveBundle`: a flat, self-contained projection of the strategy that
matters to design — the tier, the positioning statement, the emotions to evoke, the
required trust elements, the messaging spine, the visual-positioning intent, and the
prioritized decisions — which downstream engines *pull* and adapt through ports they
own. This keeps the dependency arrows pointing only into strategy.

Pure domain: standard library and the report/section models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from strategy.domain.decision.decision import StrategicDecision
from strategy.domain.report.report import BusinessStrategyReport
from strategy.domain.shared.ids import StrategyReportId
from strategy.domain.shared.value_objects import (
    EmotionKind,
    MessagingTone,
    StrategyTier,
    TrustElementKind,
)

__all__ = ["DesignDirectiveBundle"]


@dataclass(frozen=True, slots=True)
class DesignDirectiveBundle:
    """A flat, neutral projection of a strategy report for downstream design.

    Attributes:
        report_id: The report this bundle projects.
        project_id: The project the strategy served.
        tier: The committed positioning tier.
        positioning_statement: The canonical positioning statement.
        primary_message: The spine of the messaging framework.
        tone: The brand voice tone.
        visual_adjectives: The adjectives the visual system must evoke.
        design_principles: The strategic design principles to honour.
        references_to_avoid: The visual anti-patterns to avoid.
        emotions: The emotions the experience should evoke.
        required_trust: The trust elements the experience must carry.
        prioritized_decisions: The decisions in priority order (highest first).
        is_usable: Whether the strategy is cleared to drive design.
        created_at: When the strategy was produced.
    """

    report_id: StrategyReportId
    project_id: str
    tier: StrategyTier
    positioning_statement: str
    primary_message: str
    tone: MessagingTone
    visual_adjectives: tuple[str, ...]
    design_principles: tuple[str, ...]
    references_to_avoid: tuple[str, ...]
    emotions: tuple[EmotionKind, ...]
    required_trust: tuple[TrustElementKind, ...]
    prioritized_decisions: tuple[StrategicDecision, ...]
    is_usable: bool
    created_at: datetime

    @classmethod
    def from_report(cls, report: BusinessStrategyReport) -> DesignDirectiveBundle:
        """Project a :class:`BusinessStrategyReport` into a design directive bundle."""
        ranked = report.priority_matrix.ranked()
        prioritized = tuple(
            report.decision_graph.get(item.decision_id)
            for item in ranked
            if report.decision_graph.has(item.decision_id)
        )
        emotions = tuple(
            dict.fromkeys(e.emotion for e in report.customer.emotions)
        )
        return cls(
            report_id=report.id,
            project_id=report.project_id,
            tier=report.tier,
            positioning_statement=report.positioning.statement.statement,
            primary_message=report.messaging.primary_message,
            tone=report.brand_voice.tone,
            visual_adjectives=report.positioning.visual.adjectives,
            design_principles=report.positioning.visual.design_principles,
            references_to_avoid=report.positioning.visual.references_to_avoid,
            emotions=emotions,
            required_trust=tuple(e.kind for e in report.trust.by_priority()),
            prioritized_decisions=prioritized,
            is_usable=report.is_usable,
            created_at=report.created_at,
        )

    @property
    def is_empty(self) -> bool:
        return not self.prioritized_decisions
