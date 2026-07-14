"""The Brand Visual Direction — the consolidated creative direction.

:class:`BrandVisualDirection` groups every strategic creative direction — logo,
typography, colour, spacing, photography, illustration, iconography, motion, and the UI
and component personalities — into one cohesive, cited value object the report composes.
It is strategic intent throughout; it emits no tokens, assets, or code.

Pure domain: standard library and the visual sub-models.
"""

from __future__ import annotations

from dataclasses import dataclass

from brand.domain.shared.ids import BrandEvidenceId
from brand.domain.visual.color import ColorPhilosophy
from brand.domain.visual.iconography import IconographyDirection
from brand.domain.visual.imagery import IllustrationDirection, PhotographyDirection
from brand.domain.visual.logo import LogoDirection
from brand.domain.visual.motion import MotionPrinciples
from brand.domain.visual.spacing import SpacingPhilosophy
from brand.domain.visual.typography import TypographyDirection
from brand.domain.visual.ui_personality import ComponentPersonality, UIPersonality

__all__ = ["BrandVisualDirection"]


@dataclass(frozen=True, slots=True)
class BrandVisualDirection:
    """The consolidated, cited creative direction (intent only, never tokens).

    Attributes:
        logo: Logo direction.
        typography: Typography direction.
        color: Colour philosophy.
        spacing: Spacing philosophy.
        photography: Photography direction.
        illustration: Illustration direction.
        iconography: Iconography direction.
        motion: Motion principles.
        ui: How the interface should feel.
        component: How components should feel.
    """

    logo: LogoDirection
    typography: TypographyDirection
    color: ColorPhilosophy
    spacing: SpacingPhilosophy
    photography: PhotographyDirection
    illustration: IllustrationDirection
    iconography: IconographyDirection
    motion: MotionPrinciples
    ui: UIPersonality
    component: ComponentPersonality

    def evidence_ids(self) -> tuple[BrandEvidenceId, ...]:
        return (
            *self.logo.evidence_ids,
            *self.typography.evidence_ids,
            *self.color.evidence_ids,
            *self.spacing.evidence_ids,
            *self.photography.evidence_ids,
            *self.illustration.evidence_ids,
            *self.iconography.evidence_ids,
            *self.motion.evidence_ids,
            *self.ui.evidence_ids,
            *self.component.evidence_ids,
        )
