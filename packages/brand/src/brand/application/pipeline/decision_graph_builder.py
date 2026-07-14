"""Stage — Brand Decision Graph construction.

Lifts the validated draft's elements into a traversable :class:`BrandDecisionGraph`: one
:class:`BrandDecision` per grounded element, wired by ``DERIVES_FROM`` edges into a
coherent derivation (positioning is foundational; identity, character, emotional, and
creative direction derive from it and from the archetype) and by ``EXPRESSES`` edges
that link each creative decision to the identity/personality it gives form to. An
element with no citations produces no decision, so the graph carries only grounded
choices.

Each decision's confidence is the mean confidence of the evidence it cites — a
deterministic, explainable roll-up.
"""

from __future__ import annotations

from collections.abc import Sequence

from brand.application.contracts import BrandDraft
from brand.domain.decision.decision import BrandDecision
from brand.domain.decision.decision_graph import BrandDecisionEdge, BrandDecisionGraph
from brand.domain.evidence.evidence import EvidenceGraph
from brand.domain.shared.ids import (
    BrandDecisionEdgeId,
    BrandDecisionId,
    BrandEvidenceId,
)
from brand.domain.shared.value_objects import (
    BrandDecisionType,
    Confidence,
    ConsideredAlternative,
    DecisionRelation,
    Priority,
)

__all__ = ["DecisionGraphBuilder"]

_PRIORITY: dict[BrandDecisionType, int] = {
    BrandDecisionType.POSITIONING: 5,
    BrandDecisionType.MISSION: 5,
    BrandDecisionType.VISION: 4,
    BrandDecisionType.VALUES: 4,
    BrandDecisionType.PROMISE: 5,
    BrandDecisionType.STORY: 3,
    BrandDecisionType.ARCHETYPE: 5,
    BrandDecisionType.PERSONALITY: 4,
    BrandDecisionType.VOICE: 4,
    BrandDecisionType.EMOTIONAL: 4,
    BrandDecisionType.TRUST: 4,
    BrandDecisionType.DIFFERENTIATION: 4,
    BrandDecisionType.LOGO: 3,
    BrandDecisionType.TYPOGRAPHY: 4,
    BrandDecisionType.COLOR: 4,
    BrandDecisionType.SPACING: 3,
    BrandDecisionType.PHOTOGRAPHY: 3,
    BrandDecisionType.ILLUSTRATION: 2,
    BrandDecisionType.ICONOGRAPHY: 3,
    BrandDecisionType.MOTION: 3,
    BrandDecisionType.UI_PERSONALITY: 4,
    BrandDecisionType.COMPONENT_PERSONALITY: 4,
    BrandDecisionType.LANGUAGE: 3,
    BrandDecisionType.COPY: 3,
}

# (source role, target role, relation) — applied only when both decisions exist.
_EDGES: tuple[tuple[str, str, DecisionRelation], ...] = (
    ("mission", "positioning", DecisionRelation.DERIVES_FROM),
    ("vision", "positioning", DecisionRelation.DERIVES_FROM),
    ("values", "positioning", DecisionRelation.DERIVES_FROM),
    ("promise", "positioning", DecisionRelation.DERIVES_FROM),
    ("story", "positioning", DecisionRelation.DERIVES_FROM),
    ("archetype", "positioning", DecisionRelation.DERIVES_FROM),
    ("personality", "archetype", DecisionRelation.DERIVES_FROM),
    ("voice", "personality", DecisionRelation.DERIVES_FROM),
    ("emotional", "positioning", DecisionRelation.DERIVES_FROM),
    ("trust", "emotional", DecisionRelation.DERIVES_FROM),
    ("differentiation", "positioning", DecisionRelation.DERIVES_FROM),
    ("logo", "archetype", DecisionRelation.DERIVES_FROM),
    ("typography", "archetype", DecisionRelation.DERIVES_FROM),
    ("color", "archetype", DecisionRelation.DERIVES_FROM),
    ("spacing", "archetype", DecisionRelation.DERIVES_FROM),
    ("photography", "archetype", DecisionRelation.DERIVES_FROM),
    ("illustration", "archetype", DecisionRelation.DERIVES_FROM),
    ("iconography", "archetype", DecisionRelation.DERIVES_FROM),
    ("motion", "archetype", DecisionRelation.DERIVES_FROM),
    ("ui", "archetype", DecisionRelation.DERIVES_FROM),
    ("component", "ui", DecisionRelation.DERIVES_FROM),
    ("language", "voice", DecisionRelation.DERIVES_FROM),
    ("copy", "voice", DecisionRelation.DERIVES_FROM),
    # Creative decisions express identity/personality.
    ("typography", "personality", DecisionRelation.EXPRESSES),
    ("color", "personality", DecisionRelation.EXPRESSES),
    ("motion", "personality", DecisionRelation.EXPRESSES),
    ("ui", "personality", DecisionRelation.EXPRESSES),
    ("component", "personality", DecisionRelation.EXPRESSES),
    ("photography", "emotional", DecisionRelation.EXPRESSES),
    ("copy", "voice", DecisionRelation.EXPRESSES),
)


class DecisionGraphBuilder:
    """Builds the brand decision graph from a validated draft."""

    def build(self, draft: BrandDraft, evidence: EvidenceGraph) -> BrandDecisionGraph:
        decisions: list[BrandDecision] = []
        role_ids: dict[str, BrandDecisionId] = {}

        def add(
            role: str,
            decision_type: BrandDecisionType,
            title: str,
            statement: str,
            rationale: str,
            evidence_ids: Sequence[BrandEvidenceId],
            considered: Sequence[ConsideredAlternative] = (),
        ) -> None:
            ids = tuple(evidence_ids)
            if not ids:  # no citation ⇒ no decision
                return
            decision = BrandDecision(
                id=BrandDecisionId.new(),
                type=decision_type,
                title=title,
                statement=statement or title,
                rationale=rationale,
                confidence=self._confidence(ids, evidence),
                priority=Priority(_PRIORITY[decision_type]),
                considered=tuple(considered),
                evidence_ids=ids,
            )
            decisions.append(decision)
            role_ids[role] = decision.id

        self._add_identity(draft, add)
        self._add_character(draft, add)
        self._add_emotional(draft, add)
        self._add_visual(draft, add)
        self._add_verbal(draft, add)

        edges = self._edges(role_ids)
        return BrandDecisionGraph.of(decisions, edges)

    # ------------------------------------------------------------------ #
    def _add_identity(self, draft: BrandDraft, add) -> None:
        i = draft.identity
        add("positioning", BrandDecisionType.POSITIONING, "Own the brand position",
            i.positioning.statement, i.positioning.point_of_difference,
            i.positioning.evidence_ids, i.positioning.considered)
        add("mission", BrandDecisionType.MISSION, "Commit to the mission",
            i.mission.statement, "Why the brand exists.", i.mission.evidence_ids)
        add("vision", BrandDecisionType.VISION, "Pursue the vision",
            i.vision.statement, "The future the brand builds toward.", i.vision.evidence_ids)
        add("values", BrandDecisionType.VALUES, "Hold the brand values",
            "; ".join(v.name for v in i.values) or "Brand values", "The principles the brand acts on.",
            i.values.evidence_ids())
        add("promise", BrandDecisionType.PROMISE, "Keep the brand promise",
            i.promise.statement, "What customers can always count on.", i.promise.evidence_ids)
        add("story", BrandDecisionType.STORY, "Tell the brand story",
            i.story.headline, i.story.resolution, i.story.evidence_ids)

    def _add_character(self, draft: BrandDraft, add) -> None:
        c = draft.character
        add("archetype", BrandDecisionType.ARCHETYPE, f"Embody the {c.archetype.primary.value}",
            f"Lead with the {c.archetype.primary.value} archetype.", c.archetype.rationale,
            c.archetype.evidence_ids, c.archetype.considered)
        add("personality", BrandDecisionType.PERSONALITY, "Express the brand personality",
            c.personality.summary or ", ".join(c.personality.traits) or "Brand personality",
            "The human character the brand carries.", c.personality.all_evidence_ids())
        add("voice", BrandDecisionType.VOICE, f"Speak in a {c.tone.dominant.value} voice",
            f"Adopt a {c.tone.dominant.value} voice.", "How the brand consistently sounds.",
            c.voice.evidence_ids)

    def _add_emotional(self, draft: BrandDraft, add) -> None:
        e = draft.emotional
        add("emotional", BrandDecisionType.EMOTIONAL,
            f"Own the feeling of {e.positioning.primary_emotion.value}",
            e.positioning.emotional_benefit, "The emotion the brand owns.",
            e.positioning.evidence_ids)
        add("trust", BrandDecisionType.TRUST, "Project the required trust",
            "Carry the brand's trust signals where they matter.",
            "Trust is the brand's licence to operate.",
            tuple(eid for t in e.trust_signals for eid in t.evidence_ids))
        add("differentiation", BrandDecisionType.DIFFERENTIATION, "Lead with the differentiators",
            "; ".join(d.claim for d in e.differentiators) or "Brand differentiators",
            "The defensible reasons to choose the brand.",
            tuple(eid for d in e.differentiators for eid in d.evidence_ids))

    def _add_visual(self, draft: BrandDraft, add) -> None:
        v = draft.visual
        add("logo", BrandDecisionType.LOGO, "Direct the brand mark",
            v.logo.intent, "What the mark must express.", v.logo.evidence_ids)
        add("typography", BrandDecisionType.TYPOGRAPHY, "Set the typographic voice",
            f"Display {v.typography.display_voice.value}, body {v.typography.body_voice.value}.",
            v.typography.rationale, v.typography.evidence_ids)
        add("color", BrandDecisionType.COLOR, "Set the colour philosophy",
            f"{v.color.temperament.value} temperament, {v.color.contrast.value} contrast.",
            v.color.meaning, v.color.evidence_ids)
        add("spacing", BrandDecisionType.SPACING, "Set the spacing philosophy",
            f"{v.spacing.density.value} density.", v.spacing.rhythm_intent, v.spacing.evidence_ids)
        add("photography", BrandDecisionType.PHOTOGRAPHY, "Direct photography",
            f"{v.photography.treatment.value} treatment.", v.photography.mood,
            v.photography.evidence_ids)
        add("illustration", BrandDecisionType.ILLUSTRATION, "Direct illustration",
            f"{v.illustration.style.value} style.", v.illustration.role,
            v.illustration.evidence_ids)
        add("iconography", BrandDecisionType.ICONOGRAPHY, "Direct iconography",
            f"{v.iconography.style.value} icons.", v.iconography.weight_intent,
            v.iconography.evidence_ids)
        add("motion", BrandDecisionType.MOTION, "Set motion principles",
            f"{v.motion.character.value} motion.", v.motion.purpose, v.motion.evidence_ids)
        add("ui", BrandDecisionType.UI_PERSONALITY, "Set the UI personality",
            v.ui.feel or f"{v.ui.corner_language.value}, {v.ui.weight.value}, {v.ui.texture.value}.",
            "How the interface should feel.", v.ui.evidence_ids)
        add("component", BrandDecisionType.COMPONENT_PERSONALITY, "Set the component personality",
            v.component.interaction_feel or "How components should feel.",
            v.component.emphasis, v.component.evidence_ids)

    def _add_verbal(self, draft: BrandDraft, add) -> None:
        v = draft.verbal
        add("language", BrandDecisionType.LANGUAGE, "Set the language rules",
            v.language_rules.person or "Brand language rules",
            "The grammar the brand writes by.", v.language_rules.evidence_ids)
        add("copy", BrandDecisionType.COPY, "Set the copy guidelines",
            v.copy_guidelines.cta_style or "Brand copy guidelines",
            "How the brand writes.", v.copy_guidelines.evidence_ids)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _confidence(
        evidence_ids: Sequence[BrandEvidenceId], evidence: EvidenceGraph
    ) -> Confidence:
        values = [evidence.get(eid).confidence.value for eid in evidence_ids]
        return Confidence.clamp(sum(values) / len(values)) if values else Confidence.of(0.5)

    @staticmethod
    def _edges(role_ids: dict[str, BrandDecisionId]) -> list[BrandDecisionEdge]:
        edges: list[BrandDecisionEdge] = []
        for source_role, target_role, relation in _EDGES:
            source = role_ids.get(source_role)
            target = role_ids.get(target_role)
            if source is not None and target is not None:
                edges.append(
                    BrandDecisionEdge(
                        id=BrandDecisionEdgeId.new(),
                        source=source,
                        target=target,
                        relation=relation,
                    )
                )
        return edges
