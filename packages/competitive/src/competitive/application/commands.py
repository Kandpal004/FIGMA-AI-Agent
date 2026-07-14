"""Command objects — the engine's typed input contract."""

from __future__ import annotations

from dataclasses import dataclass

from competitive.domain.report.brief import CompetitiveBrief
from competitive.domain.shared.ids import ReportLineageId

__all__ = ["AnalyzeCompetitors"]


@dataclass(frozen=True, slots=True)
class AnalyzeCompetitors:
    """Produce a competitor intelligence report for a brief.

    Attributes:
        brief: What to analyse.
        lineage_id: The report lineage to append a new version to; ``None`` starts
            a fresh lineage.
    """

    brief: CompetitiveBrief
    lineage_id: ReportLineageId | None = None
