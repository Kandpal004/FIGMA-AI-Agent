"""RuleBasedLanguageDesigner — the deterministic designer brain (default synthesis).

Implements :class:`LanguageDesignerPort` by selecting a language archetype for the brief's
industry (honouring a caller hint), then composing the Visual DNA, the token system, the eleven
philosophies, the four personalities, and the grid/responsive systems from the codified
archetype descriptor over the supplied evidence. It grounds the DNA and personalities in Brand
and Psychology, the tokens and philosophies in Knowledge, and the selection in Business and the
Creative Director — so the language visibly references the upstream engines the spec requires.

It is fully deterministic (same input + evidence ⇒ same language), dependency-free, and honest
— it invents no facts; it *composes* a premium, timeless language over the evidence it is given
and records the alternatives it rejected. It is not an LLM and draws no pixels.
"""

from __future__ import annotations

from collections.abc import Sequence

from design_language.application.contracts import LanguageDraft, LanguageInput
from design_language.domain.dna.visual_dna import VisualDNA
from design_language.domain.evidence.evidence import DLEvidence, EvidenceGraph
from design_language.domain.language.selection import LanguageSelection
from design_language.domain.personality.personality import Personality, PersonalitySet
from design_language.domain.philosophy.philosophy import Philosophy, PhilosophySet
from design_language.domain.shared.ids import DLEvidenceId, PhilosophyId
from design_language.domain.shared.value_objects import (
    AlignmentApproach,
    ColorRole,
    ConsideredAlternative,
    Level,
    PersonalityKind,
    PhilosophyKind,
    ProvenanceKind,
    Ratio,
    ResponsiveApproach,
    Tag,
    VisualStyle,
)
from design_language.domain.system.grid_system import GridSystem
from design_language.domain.system.responsive import ResponsiveStrategy
from design_language.domain.tokens.color import ColorPhilosophy
from design_language.domain.tokens.scales import (
    ContrastTargets,
    ElevationScale,
    MotionTokens,
    RadiusScale,
    SpacingScale,
    TypeScale,
)
from design_language.domain.tokens.visual_tokens import VisualTokens
from design_language.infrastructure.adapters.language_archetypes import (
    ArchetypeDescriptor,
    descriptor_for,
)
from design_language.infrastructure.adapters.industry_presets import preset_for

__all__ = ["RuleBasedLanguageDesigner"]

_ALL_ROLES = tuple(ColorRole)


class RuleBasedLanguageDesigner:
    """A deterministic, evidence-grounded implementation of the designer port."""

    async def design(
        self, language_input: LanguageInput, evidence: EvidenceGraph
    ) -> LanguageDraft:
        ranked = sorted(evidence, key=lambda e: e.confidence.value, reverse=True)
        brief = language_input.brief
        preset = preset_for(brief.industry)
        archetype = brief.preferred_archetype or preset.primary
        descriptor = descriptor_for(archetype)

        luxury = min(5, max(1, descriptor.luxury + preset.luxury_bias + (1 if brief.is_luxury else 0)))

        brand_cite = self._prefer(ranked, ProvenanceKind.BRAND_STRATEGY, ("brand", "tone", "identity", "voice"))
        psych_cite = self._prefer(ranked, ProvenanceKind.PSYCHOLOGY, ("trust", "emotion", "anxiety", "confidence"))
        know_cite = self._prefer(ranked, ProvenanceKind.KNOWLEDGE, ("spacing", "type", "grid", "system", "restraint", "premium"))
        biz_cite = self._prefer(ranked, ProvenanceKind.BUSINESS_STRATEGY, ("business", "conversion", "positioning", "revenue"))
        cd_cite = self._prefer(ranked, ProvenanceKind.CREATIVE_DIRECTOR, ("quality", "approved", "review", "premium"))

        dna = VisualDNA(
            visual_style=descriptor.visual_style, luxury_level=Level(luxury),
            minimalism_level=Level(descriptor.minimalism), density=descriptor.density,
            visual_weight=descriptor.weight, contrast=descriptor.contrast, rhythm=descriptor.rhythm,
            essence=descriptor.essence, traits=tuple(Tag.of(t) for t in descriptor.traits),
            evidence_ids=self._dedup(brand_cite + psych_cite),
        )
        tokens = self._tokens(descriptor, luxury, brand_cite, know_cite)
        philosophies = self._philosophies(descriptor, dna, know_cite, cd_cite)
        personalities = self._personalities(descriptor, brand_cite)
        grid = GridSystem(columns=12, alignment=AlignmentApproach.BASELINE, evidence_ids=know_cite)
        responsive = ResponsiveStrategy(
            approach=ResponsiveApproach.FLUID, breakpoint_tiers=4, scales_fluidly=True,
            principles=("Type and spacing scale fluidly.", "Mobile-first, content-out."),
            evidence_ids=know_cite,
        )
        selection = LanguageSelection(
            archetype=archetype,
            rationale=f"{archetype.value} best expresses the {brief.industry.value} brand: "
                      f"{descriptor.essence}",
            business_alignment=f"Its {', '.join(descriptor.traits[:2])} character advances the "
                               f"positioning and conversion goals for the {brief.tier} tier.",
            influences=tuple(Tag.of(i) for i in descriptor.influences),
            considered=tuple(
                ConsideredAlternative(option=alt.value, reason_rejected=reason)
                for alt, reason in preset.alternatives
            ),
            evidence_ids=self._dedup(biz_cite + cd_cite) or brand_cite,
        )
        return LanguageDraft(
            visual_dna=dna, tokens=tokens, philosophies=philosophies, personalities=personalities,
            grid_system=grid, responsive_strategy=responsive, language_selection=selection,
        )

    # ------------------------------------------------------------------ #
    def _tokens(
        self, descriptor: ArchetypeDescriptor, luxury: int,
        brand_cite: tuple[DLEvidenceId, ...], know_cite: tuple[DLEvidenceId, ...],
    ) -> VisualTokens:
        elevation_posture = "flat" if descriptor.minimalism >= 5 else ("subtle" if descriptor.minimalism >= 3 else "layered")
        elevation_levels = 1 if descriptor.minimalism >= 5 else (2 if descriptor.minimalism >= 3 else 3)
        radius_sharpness = "sharp" if descriptor.visual_style in (VisualStyle.TECHNICAL, VisualStyle.MINIMAL) else "rounded"
        easing = "restrained" if luxury >= 4 else ("expressive" if descriptor.visual_style is VisualStyle.BOLD else "standard")
        color = ColorPhilosophy(
            strategy=descriptor.color_strategy, roles=_ALL_ROLES,
            accent_count=descriptor.accent_count, contrast=ContrastTargets(), evidence_ids=brand_cite,
        )
        return VisualTokens(
            spacing=SpacingScale(base_unit=descriptor.spacing_base, ratio=Ratio(1.5), steps=8),
            type_scale=TypeScale(ratio=Ratio(descriptor.type_ratio), steps=7),
            radius=RadiusScale(steps=4, sharpness=radius_sharpness),
            elevation=ElevationScale(levels=elevation_levels, posture=elevation_posture),
            motion=MotionTokens(duration_tiers=3, easing=easing),
            color=color, contrast=ContrastTargets(), evidence_ids=know_cite,
        )

    def _philosophies(
        self, descriptor: ArchetypeDescriptor, dna: VisualDNA,
        know_cite: tuple[DLEvidenceId, ...], cd_cite: tuple[DLEvidenceId, ...],
    ) -> PhilosophySet:
        approaches: dict[PhilosophyKind, str] = {
            PhilosophyKind.SPACING: f"{dna.rhythm.value} rhythm on a {descriptor.spacing_base}-unit base.",
            PhilosophyKind.GRID: "A 12-column baseline grid governs all composition.",
            PhilosophyKind.ALIGNMENT: "Optical alignment on the baseline grid.",
            PhilosophyKind.CONTAINER: f"{dna.density.value} containers with generous margins.",
            PhilosophyKind.ELEVATION: f"{descriptor.minimalism}-minimal elevation; depth used sparingly.",
            PhilosophyKind.SURFACE: "Calm, matte surfaces; the content is the surface.",
            PhilosophyKind.MOTION: "Motion is restrained, purposeful, and physical.",
            PhilosophyKind.INTERACTION: "Interactions are immediate, legible, and forgiving.",
            PhilosophyKind.ANIMATION: "Animation reinforces continuity, never decoration.",
            PhilosophyKind.LAYOUT: f"{dna.visual_style.value} layouts led by a single hierarchy.",
            PhilosophyKind.COMPONENT: "Components are consistent, composable, and restrained.",
        }
        motion_kinds = {PhilosophyKind.MOTION, PhilosophyKind.INTERACTION, PhilosophyKind.ANIMATION}
        return PhilosophySet.of(
            Philosophy(
                id=PhilosophyId.new(), kind=kind, approach=approach,
                principles=(approach,),
                evidence_ids=(cd_cite if kind in motion_kinds else know_cite),
            )
            for kind, approach in approaches.items()
        )

    def _personalities(
        self, descriptor: ArchetypeDescriptor, brand_cite: tuple[DLEvidenceId, ...]
    ) -> PersonalitySet:
        characters = {
            PersonalityKind.TYPOGRAPHY: descriptor.type_character,
            PersonalityKind.ICONOGRAPHY: descriptor.icon_character,
            PersonalityKind.ILLUSTRATION: descriptor.illustration_character,
            PersonalityKind.PHOTOGRAPHY: descriptor.photography_character,
        }
        return PersonalitySet.of(
            Personality(
                kind=kind, character=character,
                attributes=tuple(descriptor.traits[:2]), evidence_ids=brand_cite,
            )
            for kind, character in characters.items()
        )

    # ------------------------------------------------------------------ #
    @staticmethod
    def _dedup(ids: tuple[DLEvidenceId, ...]) -> tuple[DLEvidenceId, ...]:
        return tuple(dict.fromkeys(ids))

    @staticmethod
    def _prefer(
        ranked: Sequence[DLEvidence], provenance: ProvenanceKind, keywords: Sequence[str],
        limit: int = 2,
    ) -> tuple[DLEvidenceId, ...]:
        """Cite the given provenance first (then keyword matches, then the strongest evidence).

        Grounding the DNA in Brand, the tokens in Knowledge, and the selection in Business and
        the Creative Director makes the language cite the source that justifies each decision —
        and surfaces every upstream engine across the specification.
        """
        if not ranked:
            return ()
        kws = [k.lower() for k in keywords]

        def matches(e: DLEvidence) -> bool:
            hay = f"{e.claim} {e.statement} {' '.join(t.value for t in e.tags)}".lower()
            return any(k in hay for k in kws)

        pref = [e for e in ranked if e.provenance is provenance]
        pref_match = [e for e in pref if matches(e)]
        other_match = [e for e in ranked if e.provenance is not provenance and matches(e)]
        ordered = list(dict.fromkeys([*pref_match, *pref, *other_match, ranked[0]]))
        return tuple(e.id for e in ordered[:limit])
