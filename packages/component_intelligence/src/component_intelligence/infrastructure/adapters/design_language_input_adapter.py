"""DesignLanguageInputAdapter — feeds the Phase-14 Design Language into the engine.

Implements :class:`DesignLanguageInputPort` over the Phase-14 design-language facade,
translating the Visual DNA and token system into :class:`RawSignal` s (provenance
``DESIGN_LANGUAGE``), so component variants, states, and token references are grounded. The
component-intelligence domain never imports Phase 14, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from design_language.domain.shared.ids import DesignLanguageSpecId
from design_language.interfaces.design_language_facade import DesignLanguageFacade

from component_intelligence.application.contracts import RawSignal
from component_intelligence.domain.context.context import ProjectContext
from component_intelligence.domain.shared.value_objects import ProvenanceKind

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
            RawSignal(provenance=ProvenanceKind.DESIGN_LANGUAGE, external_ref=f"{ref}:dna",
                claim=f"Visual DNA: {view.visual_dna.get('essence', '')} — components express this language.",
                confidence=0.85, source_name="Design Language",
                tags=("design", "language", "variant", "token", view.visual_dna.get("visual_style", ""))),
            RawSignal(provenance=ProvenanceKind.DESIGN_LANGUAGE, external_ref=f"{ref}:tokens",
                claim="Components must use the language token system and variants.", confidence=0.8,
                source_name="Design Language", tags=("token", "variant", "design", "language")),
        ]
