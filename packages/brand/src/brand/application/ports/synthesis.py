"""The Brand synthesis port — the brand-strategist brain.

This is the seam where creative judgment lives. Given the assembled :class:`BrandInput`
and the consolidated :class:`EvidenceGraph`, an implementation proposes the brand's
*content* — classification, identity, character, emotional strategy, visual direction,
and verbal system — as a :class:`BrandDraft`, **with every claim already citing evidence
by id**.

The engine treats the draft as a proposal, not gospel: it validates that citations
resolve, then lifts the draft into a decision graph, derives governance, scores
coherence, and assembles a report. That division — *the port proposes, the domain
disposes* — is what keeps the engine free of hallucination whether the implementation is
the deterministic rule-based strategist or a future reasoning/LLM adapter.

Implementations MUST only cite evidence ids present in the supplied graph; any other
citation is rejected downstream.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from brand.application.contracts import BrandDraft, BrandInput
from brand.domain.evidence.evidence import EvidenceGraph

__all__ = ["BrandSynthesisPort"]


@runtime_checkable
class BrandSynthesisPort(Protocol):
    """Proposes grounded brand content from input and consolidated evidence."""

    async def draft(self, brand_input: BrandInput, evidence: EvidenceGraph) -> BrandDraft:
        """Propose the brand's content, citing only evidence in ``evidence``."""
        ...
