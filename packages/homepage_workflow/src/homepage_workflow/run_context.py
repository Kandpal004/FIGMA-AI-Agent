"""Per-run execution context — the thread that carries real engine outputs across steps.

As the Director drives the homepage run one step at a time, each engine step must build on the
*real* output of the engines before it (Research feeds Strategy, the Design System feeds the
Orchestrator, and so on). A :class:`RunContext` is the per-run holder that carries those live
facades and the ids of the artifacts they produced, so the engine executor can wire each engine to
its true upstream inputs exactly as the platform's real input adapters do.

This is deliberately a plain, mutable application-layer holder — not a domain aggregate. It stores
no engine *types* (they are held as opaque handles), so this module stays free of engine imports;
the executor, which does import the engines, reads and writes these slots. Durability is the
Director's concern (it persists the run); the context is the in-process wiring for one drive.

Pure application glue: standard library only.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

__all__ = ["HomepageBrief", "RunContext"]


# --------------------------------------------------------------------------- #
# The normalized brief                                                         #
# --------------------------------------------------------------------------- #
def _as_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    if isinstance(value, Iterable):
        return tuple(str(v).strip() for v in value if str(v).strip())
    return ()


@dataclass(frozen=True, slots=True)
class HomepageBrief:
    """The normalized homepage brief the workflow designs against.

    Attributes:
        project_id: The owning project (UUID string).
        product_category: The product/offer category (e.g. "skincare").
        brand_name: The brand's name.
        industry: The brand's industry.
        market: The market segment (e.g. "premium", "mass").
        platform: The commerce platform (e.g. "shopify_plus").
        tenant_id: The viewer's tenant, for Knowledge scope resolution (UUID string).
        goal: A short statement of the research/design goal.
        business_goals: The business goals to advance.
        user_goals: The user goals to serve.
        descriptors: Brand descriptors (e.g. "premium", "minimal").
    """

    project_id: str
    product_category: str
    brand_name: str
    industry: str
    market: str = "premium"
    platform: str = "shopify_plus"
    tenant_id: str | None = None
    goal: str = ""
    business_goals: tuple[str, ...] = ()
    user_goals: tuple[str, ...] = ()
    descriptors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("project_id", "product_category", "brand_name", "industry"):
            value = getattr(self, name)
            if not value or not str(value).strip():
                raise ValueError(f"HomepageBrief.{name} must be non-empty.")
        if not self.goal:
            object.__setattr__(
                self, "goal", f"Design a world-class {self.product_category} homepage."
            )

    @classmethod
    def from_mapping(cls, brief: Mapping[str, object], project_id: str) -> HomepageBrief:
        """Build a brief from the Director run's ``brief`` mapping, filling sensible defaults."""
        category = str(brief.get("product_category", "")).strip() or "skincare"
        brand_name = str(brief.get("brand_name", "")).strip() or "Storefront"
        industry = str(brief.get("industry", "")).strip() or category
        return cls(
            project_id=project_id,
            product_category=category,
            brand_name=brand_name,
            industry=industry,
            market=str(brief.get("market", "")).strip() or "premium",
            platform=str(brief.get("platform", "")).strip() or "shopify_plus",
            tenant_id=(str(brief["tenant_id"]) if brief.get("tenant_id") else None),
            goal=str(brief.get("goal", "")).strip(),
            business_goals=_as_tuple(brief.get("business_goals")) or ("Grow revenue",),
            user_goals=_as_tuple(brief.get("user_goals")) or ("Buy with confidence",),
            descriptors=_as_tuple(brief.get("descriptors")) or ("premium",),
        )


# --------------------------------------------------------------------------- #
# The per-run context                                                          #
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class RunContext:
    """The live wiring for one homepage run: the brief, the shared knowledge query, and the
    per-engine ``(facade, artifact_id)`` outputs produced as the run advances.

    Attributes:
        brief: The normalized homepage brief.
        knowledge_query: The shared Phase-3 knowledge query service.
        critique_notes: The Creative Director's required changes from the latest critique — fed
            into self-improvement.
    """

    brief: HomepageBrief
    knowledge_query: Any
    critique_notes: tuple[str, ...] = ()
    _facades: dict[str, Any] = field(default_factory=dict)
    _refs: dict[str, Any] = field(default_factory=dict)

    def set_output(self, engine: str, facade: Any, ref: Any) -> None:
        """Record an engine's live facade and the id of the artifact it produced."""
        self._facades[engine] = facade
        self._refs[engine] = ref

    def has(self, engine: str) -> bool:
        return engine in self._refs

    def facade(self, engine: str) -> Any:
        """The live facade for a previously-run engine.

        Raises:
            KeyError: If the engine has not run yet in this context.
        """
        if engine not in self._facades:
            raise KeyError(f"Engine {engine!r} has not run yet in this context.")
        return self._facades[engine]

    def ref(self, engine: str) -> Any:
        """The artifact id a previously-run engine produced.

        Raises:
            KeyError: If the engine has not run yet in this context.
        """
        if engine not in self._refs:
            raise KeyError(f"Engine {engine!r} has not run yet in this context.")
        return self._refs[engine]

    def ref_str(self, engine: str) -> str:
        """The artifact id as a string, or ``""`` if the engine has not run."""
        return str(self._refs[engine]) if engine in self._refs else ""

    def set_critique_notes(self, notes: Iterable[str]) -> None:
        self.critique_notes = tuple(n for n in notes if n and n.strip())
