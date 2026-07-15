"""DesignLanguageInputAdapter — feeds the Phase-14 Design Language into the engine.

Implements :class:`DesignLanguageInputPort` over the Phase-14 facade, translating the Visual DNA
into :class:`RawSignal` s (provenance ``DESIGN_LANGUAGE``), so the file's visual language and
typography styles are grounded. The figma-design domain never imports Phase 14 — nor any Figma SDK
— so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from design_language.domain.shared.ids import DesignLanguageSpecId
from design_language.interfaces.design_language_facade import DesignLanguageFacade

from figma_design.application.contracts import RawSignal
from figma_design.domain.context.context import ProjectContext
from figma_design.domain.shared.value_objects import ProvenanceKind

__all__ = ["DesignLanguageInputAdapter"]


class DesignLanguageInputAdapter:
    """Implements :class:`DesignLanguageInputPort` over a Phase-14 design-language spec."""

    def __init__(self, facade: DesignLanguageFacade, spec_id: DesignLanguageSpecId) -> None:
        self._facade = facade
        self._spec_id = spec_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        view = await self._facade.get(self._spec_id)
        ref = str(self._spec_id)
        return [
            RawSignal(
                provenance=ProvenanceKind.DESIGN_LANGUAGE,
                external_ref=f"{ref}:dna",
                claim=f"Visual DNA: {view.visual_dna.get('essence', '')} — the file's typography "
                "styles and visual language express it.",
                confidence=0.85,
                source_name="Design Language",
                tags=("style", "typography", "visual", "language",
                      view.visual_dna.get("visual_style", "")),
            )
        ]
