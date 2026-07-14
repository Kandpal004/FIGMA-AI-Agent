"""The IA synthesis port — the information-architect brain.

This is the seam where IA judgment lives. Given the assembled :class:`IAInput` and the
consolidated :class:`EvidenceGraph`, an implementation proposes the architecture's *content*
— the site map (page blueprints with sections, goals, priorities, actions), the navigation,
the page relationships, and the product discovery — as an :class:`IADraft`, **with every
claim already citing evidence by id**.

The engine treats the draft as a proposal, not gospel: it validates that citations resolve,
then builds the six graphs, scores, and assembles a report. That division — *the port
proposes, the domain disposes* — is what keeps the engine free of hallucination whether the
implementation is the deterministic rule-based architect or a future reasoning/LLM adapter.

Implementations MUST only cite evidence ids present in the supplied graph; any other citation
is rejected downstream.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ia.application.contracts import IADraft, IAInput
from ia.domain.evidence.evidence import EvidenceGraph

__all__ = ["IASynthesisPort"]


@runtime_checkable
class IASynthesisPort(Protocol):
    """Proposes grounded IA content from input and consolidated evidence."""

    async def draft(self, ia_input: IAInput, evidence: EvidenceGraph) -> IADraft:
        """Propose the information architecture's content, citing only supplied evidence."""
        ...
