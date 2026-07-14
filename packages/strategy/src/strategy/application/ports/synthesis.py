"""The Strategy synthesis port — the strategist brain.

This is the seam where judgment lives. Given the assembled :class:`StrategyInput` and
the consolidated :class:`EvidenceGraph`, an implementation proposes the strategy's
*content* — the eight pillars plus risks and opportunities — as a
:class:`StrategyDraft`, **with every claim already citing evidence by id**.

The engine treats the draft as a proposal, not gospel: it validates that citations
resolve, drops what is ungrounded, and only then lifts the draft into decisions,
graphs, priorities, and a scored report. That division — *the port proposes, the domain
disposes* — is what keeps the engine free of hallucination regardless of whether the
implementation is the deterministic rule-based strategist or a future reasoning/LLM
adapter.

Implementations MUST only cite evidence ids present in the supplied graph; any other
citation is dropped downstream and lowers the report's grounding score.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from strategy.application.contracts import StrategyDraft, StrategyInput
from strategy.domain.evidence.evidence import EvidenceGraph

__all__ = ["StrategySynthesisPort"]


@runtime_checkable
class StrategySynthesisPort(Protocol):
    """Proposes grounded strategy content from input and consolidated evidence."""

    async def draft(
        self, strategy_input: StrategyInput, evidence: EvidenceGraph
    ) -> StrategyDraft:
        """Propose the strategy's content, citing only evidence in ``evidence``."""
        ...
