"""EvidenceExtractor — stage 6: turn extraction candidates into cited evidence.

Maps each :class:`CandidateEvidence` from the extractor into a domain
:class:`Evidence` with a full :class:`SourceRef` (the source, provider, and locator)
— so every finding is provenance-tracked from the moment it enters the domain.
Deterministic.
"""

from __future__ import annotations

from research.domain.collection.artifact import RawArtifact
from research.domain.collection.extraction import RawExtraction
from research.domain.evidence.evidence import Evidence, SourceRef
from research.domain.shared.ids import EvidenceId
from research.domain.source.source import ResearchSource

__all__ = ["EvidenceExtractor"]


class EvidenceExtractor:
    """Builds provenance-tracked evidence from extraction candidates."""

    def extract(
        self,
        artifact: RawArtifact,
        source: ResearchSource,
        extraction: RawExtraction,
    ) -> tuple[Evidence, ...]:
        evidence: list[Evidence] = []
        for candidate in extraction.evidence:
            locator = candidate.locator or artifact.locator
            source_ref = SourceRef(
                source_id=source.id, locator=locator, provider=source.provider
            )
            evidence.append(
                Evidence(
                    id=EvidenceId.new(),
                    claim=candidate.claim,
                    source_ref=source_ref,
                    confidence=candidate.confidence,
                    category=candidate.category,
                    snippet=candidate.snippet,
                )
            )
        return tuple(evidence)
