"""Stage 2 — Evidence Consolidation.

Normalises the raw signals gathered from every source into one cited :class:`EvidenceGraph`,
minting a :class:`CIEvidence` per distinct signal and de-duplicating on ``(provenance,
external_ref, normalised claim)`` so the same fact surfaced by two sources is not
double-counted. The resulting graph is what the brain cites from and what the specification
validates against.
"""

from __future__ import annotations

from collections.abc import Sequence

from component_intelligence.application.contracts import RawSignal
from component_intelligence.domain.evidence.evidence import CIEvidence, EvidenceGraph
from component_intelligence.domain.shared.ids import CIEvidenceId
from component_intelligence.domain.shared.value_objects import Confidence, Tag

__all__ = ["EvidenceConsolidator"]


class EvidenceConsolidator:
    """Turns neutral signals into a de-duplicated, cited evidence graph."""

    def consolidate(self, signals: Sequence[RawSignal]) -> EvidenceGraph:
        seen: set[tuple[str, str, str]] = set()
        evidence: list[CIEvidence] = []
        for signal in signals:
            claim = signal.claim.strip()
            if not claim:
                continue
            key = (signal.provenance.value, signal.external_ref, claim.lower())
            if key in seen:
                continue
            seen.add(key)
            evidence.append(
                CIEvidence(
                    id=CIEvidenceId.new(),
                    provenance=signal.provenance,
                    external_ref=signal.external_ref,
                    claim=claim,
                    confidence=Confidence.clamp(signal.confidence),
                    statement=signal.statement,
                    source_name=signal.source_name,
                    tags=frozenset(Tag.of(t) for t in signal.tags if t.strip()),
                )
            )
        return EvidenceGraph.of(evidence)
