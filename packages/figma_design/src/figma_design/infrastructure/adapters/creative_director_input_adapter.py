"""CreativeDirectorInputAdapter — feeds the Phase-13 Creative Director into the engine.

Implements :class:`CreativeDirectorInputPort` over the Phase-13 facade, translating the approved
review into :class:`RawSignal` s (provenance ``CREATIVE_DIRECTOR``), so the file upholds the
approved quality bar and its dev-mode handoff expectations. The figma-design domain never imports
Phase 13 — nor any Figma SDK — so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from creative_director.domain.shared.ids import CreativeDirectorReviewId
from creative_director.interfaces.creative_director_facade import CreativeDirectorFacade

from figma_design.application.contracts import RawSignal
from figma_design.domain.context.context import ProjectContext
from figma_design.domain.shared.value_objects import ProvenanceKind

__all__ = ["CreativeDirectorInputAdapter"]


class CreativeDirectorInputAdapter:
    """Implements :class:`CreativeDirectorInputPort` over a Phase-13 review."""

    def __init__(
        self, facade: CreativeDirectorFacade, review_id: CreativeDirectorReviewId
    ) -> None:
        self._facade = facade
        self._review_id = review_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        view = await self._facade.get(self._review_id)
        ref = str(self._review_id)
        return [
            RawSignal(
                provenance=ProvenanceKind.CREATIVE_DIRECTOR,
                external_ref=f"{ref}:approval",
                claim=f"Creative Director ruling {view.approval['status']}: the file must be "
                "library-grade — variables, styles, component sets, and clean auto-layout.",
                confidence=0.9,
                source_name="Creative Director",
                tags=("quality", "library", "handoff", "dev-mode", "approved"),
            )
        ]
