"""The Brand Guidelines Bundle — the neutral brief downstream design phases consume.

The Brand Strategy Engine is the constitution every UX/UI/copy/visual decision must
obey — but it must not depend on those phases. So it emits a
:class:`BrandGuidelinesBundle`: a flat, self-contained projection of the brand that
matters to design — the classification, archetype, voice/tone, the full visual
direction (logo → motion + UI/component personality), and the machine-checkable
validation rules — which downstream engines *pull* and adapt through ports they own.
This keeps the dependency arrows pointing only into brand.

Pure domain: standard library and the report/section models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from brand.domain.governance.validation import BrandValidationRule
from brand.domain.report.report import BrandStrategyReport
from brand.domain.shared.ids import BrandReportId
from brand.domain.shared.value_objects import (
    BrandArchetype,
    BrandCategory,
    MessagingTone,
)
from brand.domain.visual.visual_direction import BrandVisualDirection

__all__ = ["BrandGuidelinesBundle"]


@dataclass(frozen=True, slots=True)
class BrandGuidelinesBundle:
    """A flat, neutral projection of a brand report for downstream design.

    Attributes:
        report_id: The report this bundle projects.
        project_id: The project the brand served.
        primary_category: The dominant brand category.
        secondary_categories: Supporting categories.
        archetype: The brand's primary archetype.
        tone: The brand's dominant tone.
        positioning_statement: The one-line brand positioning.
        visual: The full creative direction the design system must express.
        validation_rules: The machine-checkable rules downstream must satisfy.
        is_usable: Whether the brand is cleared to drive design.
        created_at: When the brand was produced.
    """

    report_id: BrandReportId
    project_id: str
    primary_category: BrandCategory
    secondary_categories: tuple[BrandCategory, ...]
    archetype: BrandArchetype
    tone: MessagingTone
    positioning_statement: str
    visual: BrandVisualDirection
    validation_rules: tuple[BrandValidationRule, ...]
    is_usable: bool
    created_at: datetime

    @classmethod
    def from_report(cls, report: BrandStrategyReport) -> BrandGuidelinesBundle:
        """Project a :class:`BrandStrategyReport` into a guidelines bundle."""
        return cls(
            report_id=report.id,
            project_id=report.project_id,
            primary_category=report.classification.primary,
            secondary_categories=report.classification.secondary,
            archetype=report.archetype,
            tone=report.character.tone.dominant,
            positioning_statement=report.identity.positioning.statement,
            visual=report.visual,
            validation_rules=tuple(report.governance.validation),
            is_usable=report.is_usable,
            created_at=report.created_at,
        )

    @property
    def is_empty(self) -> bool:
        return not self.validation_rules
