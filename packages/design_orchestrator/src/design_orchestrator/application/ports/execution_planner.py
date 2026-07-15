"""The Execution Planner port — the orchestrator brain.

Given the assembled input and the consolidated evidence, an implementation *plans* the design
execution: for each page in scope it decides the ordered :class:`SectionPlan` s — the section
role, the component and variant chosen (from what Component Intelligence and the Design System
already produced), the layout/spacing/typography/visual choices, the token bindings, and the
responsive/animation/accessibility/performance directives — each grounded by citing evidence
ids. The engine owns everything downstream — validating grounding, resolving the bindings against
the Design System, building the layout/tree/graphs, scheduling reviews, scoring, and assembling
the versioned plan.

The default implementation is the deterministic rule-based planner in the infrastructure layer;
this port lets it be swapped (e.g. for an LLM-assisted planner) without the engine changing. An
implementation must cite only supplied evidence and choose only from upstream-declared components
and tokens — it invents nothing; it *selects and orders* over the evidence it is given.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from design_orchestrator.application.contracts import ExecutionDraft, OrchestrationInput
from design_orchestrator.domain.evidence.evidence import EvidenceGraph

__all__ = ["ExecutionPlannerPort"]


@runtime_checkable
class ExecutionPlannerPort(Protocol):
    """Plans the ordered per-page sections from input and evidence."""

    async def plan(
        self, orchestration_input: OrchestrationInput, evidence: EvidenceGraph
    ) -> ExecutionDraft:
        """Return a cited execution draft (awaiting resolution and assembly)."""
        ...
