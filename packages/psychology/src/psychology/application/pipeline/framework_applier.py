"""Stage — Framework application.

Assembles the behavioral-science lens: it carries the Maslow mapping and Hook loop the
psychologist proposed (deriving sensible defaults from the matrices when absent), and it
computes the :class:`FoggAnalysis` deterministically from the behavior matrix — when
target behaviors are infeasible, it names whether the lever is ability, motivation, or
prompt. The behavioral-economics principles are carried through from the draft.
"""

from __future__ import annotations

from collections import Counter

from psychology.application.contracts import PsychologyDraft
from psychology.domain.frameworks.fogg import FoggAnalysis, FoggLever
from psychology.domain.frameworks.hook import HookLoop
from psychology.domain.frameworks.lens import FrameworkLens
from psychology.domain.frameworks.maslow import MaslowMapping
from psychology.domain.matrices.matrices import PsychologyMatrices
from psychology.domain.shared.value_objects import FeasibilityBand, MaslowNeed

__all__ = ["FrameworkApplier"]


class FrameworkApplier:
    """Builds the framework lens from the draft and the built matrices."""

    def apply(
        self, draft: PsychologyDraft, matrices: PsychologyMatrices
    ) -> FrameworkLens:
        maslow = draft.maslow or self._derive_maslow(matrices)
        hook = draft.hook or HookLoop(
            trigger="a reminder to return",
            action="revisit the offer",
            variable_reward="find something newly relevant",
            investment="save items or preferences",
        )
        return FrameworkLens(
            maslow=maslow,
            fogg=self._fogg(matrices),
            hook=hook,
            principles=draft.principles,
        )

    @staticmethod
    def _derive_maslow(matrices: PsychologyMatrices) -> MaslowMapping:
        needs = [c.maslow_need for c in matrices.motivation]
        if not needs:
            return MaslowMapping(dominant_need=MaslowNeed.SAFETY)
        counts = Counter(needs)
        dominant = counts.most_common(1)[0][0]
        return MaslowMapping(
            dominant_need=dominant,
            active_needs=tuple(n for n in dict.fromkeys(needs) if n is not dominant),
            rationale="Derived from the dominant Maslow need across the motivation matrix.",
        )

    @staticmethod
    def _fogg(matrices: PsychologyMatrices) -> FoggAnalysis:
        behaviors = tuple(matrices.behavior)
        evidence_ids = tuple(eid for c in behaviors for eid in c.evidence_ids)
        if not behaviors:
            return FoggAnalysis(
                primary_lever=FoggLever.INCREASE_ABILITY,
                conclusion="No target behaviors modelled; default to reducing friction.",
                evidence_ids=evidence_ids,
            )
        missing_prompt = [c for c in behaviors if not c.has_prompt]
        if missing_prompt:
            return FoggAnalysis(
                primary_lever=FoggLever.FIX_PROMPT,
                conclusion="Some target behaviors lack a clear prompt; add timely, visible prompts.",
                prompt_strategy="Place prompts at the moment of highest motivation.",
                evidence_ids=evidence_ids,
            )
        avg_motivation = sum(int(c.motivation) for c in behaviors) / len(behaviors)
        avg_ability = sum(int(c.ability) for c in behaviors) / len(behaviors)
        infeasible = [c for c in behaviors if c.feasibility is not FeasibilityBand.LIKELY]
        barriers = tuple(f"friction on: {c.target_behavior}" for c in infeasible)
        if avg_ability <= avg_motivation:
            return FoggAnalysis(
                primary_lever=FoggLever.INCREASE_ABILITY,
                conclusion="Motivation exceeds ability; make the behaviors easier (reduce friction).",
                ability_barriers=barriers,
                evidence_ids=evidence_ids,
            )
        return FoggAnalysis(
            primary_lever=FoggLever.INCREASE_MOTIVATION,
            conclusion="Ability is adequate; raise motivation at the point of action.",
            ability_barriers=barriers,
            evidence_ids=evidence_ids,
        )
