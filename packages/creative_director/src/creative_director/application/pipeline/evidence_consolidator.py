"""Stage 2 — Evidence Consolidation.

Normalises the raw signals gathered from every source into one cited :class:`EvidenceGraph`,
minting a :class:`CDEvidence` per distinct signal and de-duplicating on ``(provenance,
external_ref, normalised claim)`` so the same fact surfaced by two sources is not
double-counted. The resulting graph is what the critic panel cites from and what the review
validates against.
"""

from __future__ import annotations

from collections.abc import Sequence

from creative_director.application.contracts import RawSignal
from creative_director.domain.evidence.evidence import CDEvidence, EvidenceGraph
from creative_director.domain.shared.ids import CDEvidenceId
from creative_director.domain.shared.value_objects import Confidence, Tag

__all__ = ["EvidenceConsolidator"]


class EvidenceConsolidator:
    """Turns neutral signals into a de-duplicated, cited evidence graph."""

    def consolidate(self, signals: Sequence[RawSignal]) -> EvidenceGraph:
        seen: set[tuple[str, str, str]] = set()
        evidence: list[CDEvidence] = []
        for signal in signals:
            claim = signal.claim.strip()
            if not claim:
                continue
            key = (signal.provenance.value, signal.external_ref, claim.lower())
            if key in seen:
                continue
            seen.add(key)
            evidence.append(
                CDEvidence(
                    id=CDEvidenceId.new(),
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
