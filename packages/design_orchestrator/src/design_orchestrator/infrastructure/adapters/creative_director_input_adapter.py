"""CreativeDirectorInputAdapter — feeds the Phase-13 Creative Director into the engine.

Implements :class:`CreativeDirectorInputPort` over the Phase-13 facade, translating the approved
review into :class:`RawSignal` s (provenance ``CREATIVE_DIRECTOR``), so the review checkpoints and
quality bar are grounded. The orchestrator domain never imports Phase 13, so this adapter is the
seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from creative_director.domain.shared.ids import CreativeDirectorReviewId
from creative_director.interfaces.creative_director_facade import CreativeDirectorFacade

from design_orchestrator.application.contracts import RawSignal
from design_orchestrator.domain.context.context import ProjectContext
from design_orchestrator.domain.shared.value_objects import ProvenanceKind

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
                claim=f"Creative Director ruling {view.approval['status']}: the plan must pass "
                "token, layout, accessibility, and performance gates before generation.",
                confidence=0.9,
                source_name="Creative Director",
                tags=("review", "gate", "quality", "approved", "checkpoint"),
            )
        ]
