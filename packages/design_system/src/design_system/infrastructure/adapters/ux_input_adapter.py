"""UXInputAdapter — feeds the Phase-10 UX Strategy into the engine.

Implements :class:`UXInputPort` over the Phase-10 UX facade, translating the design brief into
:class:`RawSignal` s (provenance ``UX_STRATEGY``), so the interaction/motion tokens and the
accessibility contract are grounded. The design-system domain never imports Phase 10, so this
adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from ux.domain.shared.ids import UXReportId
from ux.interfaces.ux_facade import UXFacade

from design_system.application.contracts import RawSignal
from design_system.domain.context.context import ProjectContext
from design_system.domain.shared.value_objects import ProvenanceKind

__all__ = ["UXInputAdapter"]


class UXInputAdapter:
    """Implements :class:`UXInputPort` over a Phase-10 UX report."""

    def __init__(self, facade: UXFacade, report_id: UXReportId) -> None:
        self._facade = facade
        self._report_id = report_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        bundle = await self._facade.design_brief_bundle(self._report_id)
        ref = str(self._report_id)
        signals: list[RawSignal] = [
            RawSignal(
                provenance=ProvenanceKind.UX_STRATEGY,
                external_ref=f"{ref}:goal",
                claim=bundle.primary_user_goal,
                confidence=0.85,
                source_name="UX Strategy",
                tags=("ux", "interaction", "motion", "accessibility"),
            ),
            RawSignal(
                provenance=ProvenanceKind.UX_STRATEGY,
                external_ref=f"{ref}:a11y",
                claim="Every interactive component must meet WCAG AA contrast and be fully "
                "keyboard-operable with a visible focus ring.",
                confidence=0.85,
                source_name="UX Strategy",
                tags=("accessibility", "contrast", "focus", "keyboard", "interaction"),
            ),
        ]
        for page in bundle.pages:
            signals.append(
                RawSignal(
                    provenance=ProvenanceKind.UX_STRATEGY,
                    external_ref=f"{ref}:page:{page['page']}",
                    claim=f"{page['page']}: {page.get('objective', '')}.",
                    confidence=0.8,
                    source_name="UX Strategy",
                    tags=(page["page"], "ux", "interaction", "motion"),
                )
            )
        return signals
