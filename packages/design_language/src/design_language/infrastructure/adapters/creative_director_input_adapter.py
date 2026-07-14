"""CreativeDirectorInputAdapter — feeds the Phase-13 Creative Director into the language.

Implements :class:`CreativeDirectorInputPort` over the Phase-13 Creative Director facade: it
pulls a review's approval status and category scores and translates them into :class:`RawSignal`
s (provenance ``CREATIVE_DIRECTOR``), so the visual language is grounded in the approved quality
direction — the standard the design language must live up to. The design-language domain never
imports Phase 13, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from creative_director.domain.shared.ids import CreativeDirectorReviewId
from creative_director.interfaces.creative_director_facade import CreativeDirectorFacade

from design_language.application.contracts import RawSignal
from design_language.domain.context.context import ProjectContext
from design_language.domain.shared.value_objects import ProvenanceKind

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
        signals: list[RawSignal] = [
            RawSignal(
                provenance=ProvenanceKind.CREATIVE_DIRECTOR, external_ref=f"{ref}:approval",
                claim=f"Creative Director ruling: {view.approval['status']}. "
                      "The visual language must uphold the approved premium quality bar.",
                confidence=0.9, source_name="Creative Director",
                tags=("quality", "approved", "review", "premium", "restraint"),
            ),
        ]
        for category, score in view.scorecard.items():
            if isinstance(score, dict) and score.get("band") in ("excellent", "good"):
                signals.append(
                    RawSignal(
                        provenance=ProvenanceKind.CREATIVE_DIRECTOR,
                        external_ref=f"{ref}:score:{category}",
                        claim=f"{category} is at a {score['band']} standard to preserve.",
                        confidence=0.8, source_name="Creative Director",
                        tags=(category, "quality", "premium"),
                    )
                )
        return signals
