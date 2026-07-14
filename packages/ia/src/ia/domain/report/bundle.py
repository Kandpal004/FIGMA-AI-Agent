"""The Wireframe Brief Bundle — the neutral brief downstream wireframe phases consume.

The Information Architecture Engine is the structural source of truth every wireframe and
screen must derive from — but it must not depend on those phases. So it emits a
:class:`WireframeBriefBundle`: a flat, self-contained projection of the IA that matters to
wireframing — the page blueprints (sections by priority + placement, primary/secondary
actions, trust/conversion placement), the navigation structure, the page relationships, and
the product-discovery strategy — which downstream engines *pull* and adapt through ports
they own. This keeps the dependency arrows pointing only into ia.

Pure domain: standard library and the report/section models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ia.domain.discovery.discovery import Discovery
from ia.domain.navigation.navigation import Navigation
from ia.domain.page.page_blueprint import PageBlueprint
from ia.domain.relationship.relationship import PageRelationship
from ia.domain.report.report import IAReport
from ia.domain.shared.ids import IAReportId

__all__ = ["WireframeBriefBundle"]


@dataclass(frozen=True, slots=True)
class WireframeBriefBundle:
    """A flat, neutral projection of an IA report for downstream wireframing.

    Attributes:
        report_id: The report this bundle projects.
        project_id: The project the IA served.
        pages: The page blueprints to wireframe (required first).
        navigation: The navigation structure.
        relationships: The page relationships (cross-sell / upsell / related / linking).
        discovery: The product-discovery strategy.
        is_usable: Whether the IA is cleared to drive wireframing.
        created_at: When the IA was produced.
    """

    report_id: IAReportId
    project_id: str
    pages: tuple[PageBlueprint, ...]
    navigation: Navigation
    relationships: tuple[PageRelationship, ...]
    discovery: Discovery
    is_usable: bool
    created_at: datetime

    @classmethod
    def from_report(cls, report: IAReport) -> WireframeBriefBundle:
        """Project an :class:`IAReport` into a wireframe brief bundle."""
        return cls(
            report_id=report.id,
            project_id=report.project_id,
            pages=(*report.sitemap.required(), *report.sitemap.optional()),
            navigation=report.navigation,
            relationships=tuple(report.relationships),
            discovery=report.discovery,
            is_usable=report.is_usable,
            created_at=report.created_at,
        )

    @property
    def is_empty(self) -> bool:
        return not self.pages
