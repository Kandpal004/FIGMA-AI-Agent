"""The Psychology synthesis port — the consumer-psychologist brain.

This is the seam where behavioral judgment lives. Given the assembled
:class:`PsychologyInput` and the consolidated :class:`EvidenceGraph`, an implementation
proposes the psychology's *content* — the profile, personas, jobs, journeys, the
judgement-bearing matrix inputs (objections, behaviors, value, retention), and the
framework applications (Maslow, Hook, behavioral principles) — as a
:class:`PsychologyDraft`, **with every claim already citing evidence by id**.

The engine treats the draft as a proposal, not gospel: it validates that citations
resolve, then builds the matrices, applies the frameworks, constructs the graphs, scores,
and assembles a report. That division — *the port proposes, the domain disposes* — is
what keeps the engine free of hallucination whether the implementation is the
deterministic rule-based psychologist or a future reasoning/LLM adapter.

Implementations MUST only cite evidence ids present in the supplied graph; any other
citation is rejected downstream.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from psychology.application.contracts import PsychologyDraft, PsychologyInput
from psychology.domain.evidence.evidence import EvidenceGraph

__all__ = ["PsychologySynthesisPort"]


@runtime_checkable
class PsychologySynthesisPort(Protocol):
    """Proposes grounded psychology content from input and consolidated evidence."""

    async def draft(
        self, psychology_input: PsychologyInput, evidence: EvidenceGraph
    ) -> PsychologyDraft:
        """Propose the psychology's content, citing only evidence in ``evidence``."""
        ...
