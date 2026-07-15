"""Stage 2 — Evidence Consolidation.

Normalises the raw signals gathered from every source into one cited :class:`EvidenceGraph`,
minting a :class:`DSEvidence` per distinct signal and de-duplicating on ``(provenance,
external_ref, normalised claim)`` so the same fact surfaced by two sources is not
double-counted. The resulting graph is what the token architect cites from and what the
specification validates against.
"""

from __future__ import annotations

from collections.abc import Sequence

from design_system.application.contracts import RawSignal
from design_system.domain.evidence.evidence import DSEvidence, EvidenceGraph
from design_system.domain.shared.ids import DSEvidenceId
from design_system.domain.shared.value_objects import Confidence, Tag

__all__ = ["EvidenceConsolidator"]


class EvidenceConsolidator:
    """Turns neutral signals into a de-duplicated, cited evidence graph."""

    def consolidate(self, signals: Sequence[RawSignal]) -> EvidenceGraph:
        seen: set[tuple[str, str, str]] = set()
        evidence: list[DSEvidence] = []
        for signal in signals:
            claim = signal.claim.strip()
            if not claim:
                continue
            key = (signal.provenance.value, signal.external_ref, claim.lower())
            if key in seen:
                continue
            seen.add(key)
            evidence.append(
                DSEvidence(
                    id=DSEvidenceId.new(),
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
