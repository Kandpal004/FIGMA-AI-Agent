"""RiskAnalyzer — derives competitive risks deterministically.

Risks come from the analysis, not opinion: a material high/critical gap is a risk,
and a conversion leader in the set is a risk. Each scores itself from a severity ×
likelihood matrix.
"""

from __future__ import annotations

from collections.abc import Mapping

from competitive.domain.competitor.competitor import Competitor
from competitive.domain.evidence.evidence import EvidenceRef
from competitive.domain.matrix.gap import GapAnalysis
from competitive.domain.matrix.risk import CompetitiveRisk, RiskMatrix
from competitive.domain.shared.ids import RiskId
from competitive.domain.shared.value_objects import (
    CompetitorDimension as Dim,
    CompetitorTier,
    Likelihood,
    Severity,
)

__all__ = ["RiskAnalyzer"]


class RiskAnalyzer:
    """Builds a :class:`RiskMatrix` from the gap analysis and competitor tiers."""

    def analyze(
        self,
        gap_analysis: GapAnalysis,
        competitors: tuple[Competitor, ...],
        evidence_by_dimension: Mapping[Dim, tuple[EvidenceRef, ...]],
    ) -> RiskMatrix:
        risks: list[CompetitiveRisk] = []

        for gap in gap_analysis.gaps:
            if gap.is_material and int(gap.severity) >= int(Severity.HIGH):
                label = gap.dimension.value.replace("_", " ")
                risks.append(
                    CompetitiveRisk(
                        id=RiskId.new(),
                        dimension=gap.dimension,
                        description=f"Client materially trails the category benchmark on {label}.",
                        severity=gap.severity,
                        likelihood=Likelihood.LIKELY,
                        threat_source="category benchmark",
                        mitigation="Close the gap per the recommendation.",
                        evidence_ids=[e.id for e in evidence_by_dimension.get(gap.dimension, ())],
                    )
                )

        for competitor in competitors:
            if competitor.tier is CompetitorTier.CONVERSION_LEADER:
                risks.append(
                    CompetitiveRisk(
                        id=RiskId.new(),
                        dimension=Dim.CONVERSION_PATTERNS,
                        description=f"Conversion leader {competitor.name} holds a measurable advantage.",
                        severity=Severity.HIGH,
                        likelihood=Likelihood.LIKELY,
                        threat_source=competitor.name,
                        mitigation="Adopt the category's proven conversion patterns.",
                    )
                )

        return RiskMatrix(risks=tuple(risks))
