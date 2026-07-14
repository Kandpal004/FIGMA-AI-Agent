"""Stage 2 — Evidence Consolidation.

Normalises the raw insights gathered from every source into one cited
:class:`EvidenceGraph`, minting a :class:`StrategyEvidence` per distinct insight and
de-duplicating on ``(provenance, external_ref, normalised claim)`` so the same fact
surfaced by two sources is not double-counted. The resulting graph is what the
strategist cites from and what the report validates against.
"""

from __future__ import annotations

from collections.abc import Sequence

from strategy.application.contracts import RawInsight
from strategy.domain.evidence.evidence import EvidenceGraph, StrategyEvidence
from strategy.domain.shared.ids import StrategyEvidenceId
from strategy.domain.shared.value_objects import Confidence, Tag

__all__ = ["EvidenceConsolidator"]


class EvidenceConsolidator:
    """Turns neutral insights into a de-duplicated, cited evidence graph."""

    def consolidate(self, insights: Sequence[RawInsight]) -> EvidenceGraph:
        seen: set[tuple[str, str, str]] = set()
        evidence: list[StrategyEvidence] = []
        for insight in insights:
            claim = insight.claim.strip()
            if not claim:
                continue
            key = (insight.provenance.value, insight.external_ref, claim.lower())
            if key in seen:
                continue
            seen.add(key)
            evidence.append(
                StrategyEvidence(
                    id=StrategyEvidenceId.new(),
                    provenance=insight.provenance,
                    external_ref=insight.external_ref,
                    claim=claim,
                    confidence=Confidence.clamp(insight.confidence),
                    statement=insight.statement,
                    source_name=insight.source_name,
                    tags=frozenset(Tag.of(t) for t in insight.tags if t.strip()),
                )
            )
        return EvidenceGraph.of(evidence)
