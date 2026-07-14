"""The UX synthesis port — the UX-strategist brain.

This is the seam where UX judgment lives. Given the assembled :class:`UXInput` and the
consolidated :class:`EvidenceGraph`, an implementation proposes the strategy's *content* —
goals, mental model, page strategies, journeys, flows, and the six strategies — as a
:class:`UXDraft`, **with every claim already citing evidence by id**.

The engine treats the draft as a proposal, not gospel: it validates that citations
resolve, then builds the friction/drop-off analyses, applies the UX laws, constructs the
graphs, scores, and assembles a report. That division — *the port proposes, the domain
disposes* — is what keeps the engine free of hallucination whether the implementation is
the deterministic rule-based strategist or a future reasoning/LLM adapter.

Implementations MUST only cite evidence ids present in the supplied graph; any other
citation is rejected downstream.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ux.application.contracts import UXDraft, UXInput
from ux.domain.evidence.evidence import EvidenceGraph

__all__ = ["UXSynthesisPort"]


@runtime_checkable
class UXSynthesisPort(Protocol):
    """Proposes grounded UX content from input and consolidated evidence."""

    async def draft(self, ux_input: UXInput, evidence: EvidenceGraph) -> UXDraft:
        """Propose the UX strategy's content, citing only evidence in ``evidence``."""
        ...
