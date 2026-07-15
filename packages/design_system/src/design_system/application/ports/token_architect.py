"""The Token Architect port — the design-system brain.

Given the assembled input and the consolidated evidence, an implementation architects the
design system: the three-tier :class:`TokenSet` (primitives, semantics, component tokens), the
scales (typography/spacing/radius/elevation/shadow/border) and systems (breakpoints/grid/
container/motion/interaction), the state definitions, the per-component :class:`ComponentSpec`
set (variants, states, responsive, accessibility, performance, and the developer/Shopify/Magento
mappings), the light/dark :class:`ThemeSet`, and the :class:`Localization` contract — all
grounded by citing evidence ids. The engine owns everything downstream — validating grounding
and token integrity, deriving the constraints and the six graphs, scoring, and assembling the
versioned specification.

The default implementation is the deterministic rule-based architect in the infrastructure
layer; this port lets it be swapped (e.g. for an LLM-backed architect) without the engine
changing. An implementation must cite only supplied evidence — it invents no facts; it
*architects* a token system over the evidence it is given.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from design_system.application.contracts import DesignSystemDraft, DesignSystemInput
from design_system.domain.evidence.evidence import EvidenceGraph

__all__ = ["TokenArchitectPort"]


@runtime_checkable
class TokenArchitectPort(Protocol):
    """Architects the design system from input and evidence."""

    async def architect(
        self, design_input: DesignSystemInput, evidence: EvidenceGraph
    ) -> DesignSystemDraft:
        """Return a cited design-system draft (awaiting assembly)."""
        ...
