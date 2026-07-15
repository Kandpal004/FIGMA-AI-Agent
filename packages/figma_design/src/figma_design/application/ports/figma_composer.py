"""The Figma Composer port — the file-craft brain.

Given the assembled input and the consolidated evidence, an implementation *composes* the Figma
file the way a senior designer would: the organized pages (Cover, Design System, Components, and
one per storefront page), each page's layer tree of auto-layout frames and instances, the variable
collections with their modes (theme light/dark, device desktop/tablet/mobile), the published
styles, and the component-set catalog — all grounded by citing evidence ids. The engine owns
everything downstream — resolving the variable/style/instance bindings, building the five graphs,
scoring, and assembling the versioned model.

The default implementation is the deterministic rule-based composer in the infrastructure layer;
this port lets it be swapped (e.g. for an LLM-assisted composer) without the engine changing. An
implementation must cite only supplied evidence and reference only declared variables, styles, and
component sets — it invents nothing; it *structures* a file over the evidence it is given. It, too,
imports no Figma SDK, MCP client, or HTTP library.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from figma_design.application.contracts import FigmaDraft, FigmaInput
from figma_design.domain.evidence.evidence import EvidenceGraph

__all__ = ["FigmaComposerPort"]


@runtime_checkable
class FigmaComposerPort(Protocol):
    """Composes the Figma pages, variables, styles, and component sets from input and evidence."""

    async def compose(
        self, figma_input: FigmaInput, evidence: EvidenceGraph
    ) -> FigmaDraft:
        """Return a cited Figma draft (awaiting resolution and assembly)."""
        ...
