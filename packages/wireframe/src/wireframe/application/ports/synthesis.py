"""The Synthesis port — the planner brain.

Given the assembled input and the consolidated evidence, an implementation drafts the
wireframe structure: the page/section blueprint, with each section carrying its blocks,
components, requirements, criteria, review checklist, and per-section approval requirement,
grounded by citing evidence ids. The engine owns everything downstream — validating
grounding, resolving execution order, wiring approvals, building the six graphs, scoring, and
assembling the versioned plan.

The default implementation is the deterministic rule-based planner in the infrastructure
layer; this port lets it be swapped (e.g. for an LLM-backed planner) without the engine
changing. An implementation must cite only supplied evidence — it invents no facts; it
*structures* the plan over the evidence it is given.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from wireframe.application.contracts import WireframeDraft, WireframeInput
from wireframe.domain.evidence.evidence import EvidenceGraph

__all__ = ["WireframeSynthesisPort"]


@runtime_checkable
class WireframeSynthesisPort(Protocol):
    """Drafts the wireframe structure from input and evidence."""

    async def draft(
        self, wf_input: WireframeInput, evidence: EvidenceGraph
    ) -> WireframeDraft:
        """Return a cited draft blueprint (awaiting validation and assembly)."""
        ...
