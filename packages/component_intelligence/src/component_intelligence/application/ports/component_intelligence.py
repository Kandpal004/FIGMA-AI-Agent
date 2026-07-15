"""The Component Intelligence port — the component brain.

Given the assembled input and the consolidated evidence, an implementation decides the
component composition: for each component it reasons about, a full :class:`ComponentDecision`
(purposes, impacts, behaviours, contracts, usage guidance, variants, states, token references,
inclusion), plus the :class:`CompatibilitySet` of typed relationships between components —
grounded by citing evidence ids. The engine owns everything downstream — validating grounding,
resolving coherence (conflicts + dependency closure), deriving the rules and graphs, scoring,
and assembling the versioned specification.

The default implementation is the deterministic rule-based intelligence in the infrastructure
layer; this port lets it be swapped (e.g. for an LLM-backed brain) without the engine changing.
An implementation must cite only supplied evidence — it invents no facts; it *reasons* about
components over the evidence it is given.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from component_intelligence.application.contracts import ComponentInput, CompositionDraft
from component_intelligence.domain.evidence.evidence import EvidenceGraph

__all__ = ["ComponentIntelligencePort"]


@runtime_checkable
class ComponentIntelligencePort(Protocol):
    """Decides the component composition from input and evidence."""

    async def decide(
        self, component_input: ComponentInput, evidence: EvidenceGraph
    ) -> CompositionDraft:
        """Return a cited composition draft (awaiting coherence resolution and assembly)."""
        ...
