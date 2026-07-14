"""The Reasoning Bundle — the neutral projection downstream engines consume.

The Research Engine is upstream-independent: it imports nothing from the Reasoning
(P4) or Competitor (P5) engines. Instead it emits a :class:`ReasoningBundle` — a
flat, self-contained projection of a report's evidence, entities, relationships, and
quality — which those engines *pull* and adapt through ports they own. This keeps the
dependency arrows pointing only into research.

Pure domain: standard library and the report/evidence/entity models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from research.domain.entity.entity import Entity
from research.domain.entity.relationship import Relationship
from research.domain.evidence.evidence import Evidence
from research.domain.report.report import ResearchReport
from research.domain.result.quality import QualityMetrics
from research.domain.shared.ids import ResearchReportId

__all__ = ["ReasoningBundle"]


@dataclass(frozen=True, slots=True)
class ReasoningBundle:
    """A flat, neutral projection of a research report for downstream consumers.

    Attributes:
        report_id: The report this bundle projects.
        project_id: The project the research served.
        goal: The research goal.
        evidence: All evidence, flattened.
        entities: All entities, flattened.
        relationships: All relationships, flattened.
        quality: The report's overall quality.
        created_at: When the report was produced.
    """

    report_id: ResearchReportId
    project_id: str
    goal: str
    evidence: tuple[Evidence, ...]
    entities: tuple[Entity, ...]
    relationships: tuple[Relationship, ...]
    quality: QualityMetrics
    created_at: datetime

    @classmethod
    def from_report(cls, report: ResearchReport) -> ReasoningBundle:
        """Project a :class:`ResearchReport` into a bundle."""
        return cls(
            report_id=report.id,
            project_id=report.project_id,
            goal=report.goal,
            evidence=report.all_evidence(),
            entities=report.all_entities(),
            relationships=report.all_relationships(),
            quality=report.quality,
            created_at=report.created_at,
        )

    @property
    def is_empty(self) -> bool:
        return not (self.evidence or self.entities)
