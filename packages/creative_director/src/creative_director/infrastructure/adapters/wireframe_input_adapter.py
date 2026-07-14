"""WireframeInputAdapter — feeds the Phase-12 Wireframe plan (the subject) into the review.

Implements :class:`WireframeInputPort` over the Phase-12 wireframe facade: it pulls the plan's
neutral Figma plan bundle and translates its pages, sections, blocks, and components into
:class:`RawSignal` s (provenance ``WIREFRAME``) tagged so the Creative Director's critics can
see what the plan actually contains — trust, conversion, components, accessibility,
performance, and platform structure. This is the subject the review judges. The
creative-director domain never imports Phase 12, so this adapter is the seam.
"""

from __future__ import annotations

from collections.abc import Sequence

from wireframe.domain.shared.ids import WireframePlanId
from wireframe.interfaces.wireframe_facade import WireframeFacade

from creative_director.application.contracts import RawSignal
from creative_director.domain.context.context import ProjectContext
from creative_director.domain.shared.value_objects import ProvenanceKind

__all__ = ["WireframeInputAdapter"]


class WireframeInputAdapter:
    """Implements :class:`WireframeInputPort` over a Phase-12 wireframe plan."""

    def __init__(self, facade: WireframeFacade, plan_id: WireframePlanId) -> None:
        self._facade = facade
        self._plan_id = plan_id

    async def gather(self, project: ProjectContext) -> Sequence[RawSignal]:
        bundle = await self._facade.figma_plan_bundle(self._plan_id)
        ref = str(self._plan_id)
        signals: list[RawSignal] = [
            RawSignal(
                provenance=ProvenanceKind.WIREFRAME, external_ref=f"{ref}:plan",
                claim="Wireframe plan defines pages, sections, components, and approvals.",
                confidence=0.9, source_name="Wireframe Plan",
                tags=("structure", "section", "component", "consistency", "scalability",
                      "maintainability", "shopify", "magento", "theme", "spacing", "layout"),
            ),
        ]
        for page in bundle.pages:
            for section in page.get("sections", ()):
                stype = section.get("type", "")
                block_kinds = [b.get("kind", "") for b in section.get("blocks", ())]
                comps = [c.get("component", "") for c in section.get("required_components", ())]
                acc = [a.get("kind", "") for a in section.get("accessibility_requirements", ())]
                perf = [p.get("kind", "") for p in section.get("performance_considerations", ())]
                resp = bool(section.get("responsive_behaviour"))
                tags = [stype, "section", "structure", "component", "hierarchy", "priority"]
                tags.extend(block_kinds)
                tags.extend(comps)
                if any(k in ("trust", "review") for k in block_kinds) or "trust" in stype:
                    tags += ["trust", "review", "guarantee"]
                if any(k in ("cta", "product") for k in block_kinds) or stype in ("buy_box", "checkout_form", "cart_summary"):
                    tags += ["conversion", "cta", "buy", "checkout"]
                if acc:
                    tags += ["accessibility", "wcag"]
                if perf:
                    tags += ["performance", "lazy"]
                if resp:
                    tags += ["mobile", "responsive"]
                signals.append(
                    RawSignal(
                        provenance=ProvenanceKind.WIREFRAME,
                        external_ref=f"{ref}:section:{page['page_type']}:{stype}",
                        claim=f"{stype} section on {page['page_type']}: "
                              f"{section.get('goals', {}).get('purpose', '')}.",
                        confidence=0.85, source_name="Wireframe Plan",
                        tags=tuple(t for t in tags if t),
                    )
                )
        return signals
