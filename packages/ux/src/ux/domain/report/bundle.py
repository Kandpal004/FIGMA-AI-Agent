"""The Design Brief Bundle — the neutral brief downstream design phases consume.

The UX Strategy Engine is the source of truth every wireframe and screen must derive from
— but it must not depend on those phases. So it emits a :class:`DesignBriefBundle`: a
flat, self-contained projection of the UX strategy that matters to design — the primary
user goal, the per-page objectives + CTAs + information priority, the navigation strategy,
the conversion + trust journeys, the friction points to design around, and the applicable
UX laws — which downstream engines *pull* and adapt through ports they own. This keeps the
dependency arrows pointing only into ux.

Pure domain: standard library and the report/section models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ux.domain.analysis.friction import FrictionPoint
from ux.domain.journey.journey import UXJourney
from ux.domain.laws.lens import UXLawApplication
from ux.domain.page.page_strategy import PageStrategy
from ux.domain.report.report import UXStrategyReport
from ux.domain.shared.ids import UXReportId
from ux.domain.strategy.strategies import NavigationStrategy

__all__ = ["DesignBriefBundle"]


@dataclass(frozen=True, slots=True)
class DesignBriefBundle:
    """A flat, neutral projection of a UX strategy report for downstream design.

    Attributes:
        report_id: The report this bundle projects.
        project_id: The project the UX strategy served.
        primary_user_goal: The single primary user goal every screen serves.
        pages: The page strategies (objective + CTAs + priorities) to design.
        navigation: The navigation strategy.
        conversion_journey: The conversion journey the funnel must honour.
        trust_journey: The trust journey the experience must honour.
        friction_points: The friction points the design must remove, by severity.
        applicable_laws: The UX laws the design must apply.
        is_usable: Whether the strategy is cleared to drive design.
        created_at: When the strategy was produced.
    """

    report_id: UXReportId
    project_id: str
    primary_user_goal: str
    pages: tuple[PageStrategy, ...]
    navigation: NavigationStrategy
    conversion_journey: UXJourney
    trust_journey: UXJourney
    friction_points: tuple[FrictionPoint, ...]
    applicable_laws: tuple[UXLawApplication, ...]
    is_usable: bool
    created_at: datetime

    @classmethod
    def from_report(cls, report: UXStrategyReport) -> DesignBriefBundle:
        """Project a :class:`UXStrategyReport` into a design brief bundle."""
        primary = report.goals.primary_user_goal
        return cls(
            report_id=report.id,
            project_id=report.project_id,
            primary_user_goal=primary.statement if primary else "",
            pages=tuple(report.pages),
            navigation=report.strategies.navigation,
            conversion_journey=report.journeys.conversion,
            trust_journey=report.journeys.trust,
            friction_points=report.friction.by_severity(),
            applicable_laws=tuple(report.laws),
            is_usable=report.is_usable,
            created_at=report.created_at,
        )

    @property
    def is_empty(self) -> bool:
        return not self.pages
