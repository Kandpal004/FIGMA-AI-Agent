"""DesignLanguageInputAdapter — feeds the Phase-14 Design Language into the engine.

Implements :class:`DesignLanguageInputPort` over the Phase-14 design-language facade, translating
the Visual DNA and abstract token system into :class:`RawSignal` s (provenance
``DESIGN_LANGUAGE``), so the concrete design tokens are grounded in the language. The
design-system domain never imports Phase 14, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from design_language.domain.shared.ids import DesignLanguageSpecId
from design_language.interfaces.design_language_facade import DesignLanguageFacade

from design_system.application.contracts import RawSignal
from design_system.domain.context.context import ProjectContext
from design_system.domain.shared.value_objects import ProvenanceKind

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
                claim=f"Visual DNA: {view.visual_dna.get('essence', '')} — the token palette, "
                "type, and radius express this language.",
                confidence=0.85,
                source_name="Design Language",
                tags=("design", "language", "color", "typography", "token",
                      view.visual_dna.get("visual_style", "")),
            ),
            RawSignal(
                provenance=ProvenanceKind.DESIGN_LANGUAGE,
                external_ref=f"{ref}:tokens",
                claim="The design tokens must realise the language's abstract scales (type, "
                "space, radius, elevation) as concrete primitives and semantics.",
                confidence=0.8,
                source_name="Design Language",
                tags=("token", "scale", "typography", "spacing", "radius"),
            ),
        ]
