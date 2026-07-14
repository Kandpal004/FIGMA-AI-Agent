"""Strategy inputs — the neutral context the engine reasons over.

These value objects capture the *given* context of a strategy engagement — the brand,
the project, and the raw goals — in the engine's own vocabulary, independent of any
upstream engine's models. Infrastructure adapters translate Phase 3–6 outputs and
user input into these; the domain never imports those engines.

Pure domain: standard library, the shared-kernel error base, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from strategy.domain.shared.value_objects import StrategyTier

__all__ = ["BrandContext", "GoalContext", "InvalidContextError", "ProjectContext"]


class InvalidContextError(DesignDirectorError):
    """Raised when strategy context is constructed with invalid data."""

    code = "invalid_strategy_context"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """The project a strategy serves.

    Attributes:
        project_id: The owning project (UUID string).
        platform: The commerce platform (e.g. "shopify_plus", "adobe_commerce").
        market: The market segment (e.g. "premium", "mass").
        country: The primary country/region.
        tenant_id: The viewer's tenant, for Knowledge scope resolution (UUID string).
    """

    project_id: str
    platform: str = ""
    market: str = ""
    country: str = ""
    tenant_id: str | None = None

    def __post_init__(self) -> None:
        if not self.project_id or not self.project_id.strip():
            raise InvalidContextError("ProjectContext.project_id must be non-empty.")


@dataclass(frozen=True, slots=True)
class BrandContext:
    """The brand a strategy is built for.

    Attributes:
        name: The brand name.
        industry: The industry/vertical.
        maturity: Brand maturity (e.g. "startup", "growth", "established").
        tier_hint: An optional desired positioning tier, if the brand has stated one.
        descriptors: Free-form brand descriptors/adjectives the brand already uses.
        existing_tokens: Any pre-existing brand tokens (read-only), as strings — the
            strategy reasons about them but does not emit design tokens.
    """

    name: str
    industry: str = ""
    maturity: str = ""
    tier_hint: StrategyTier | None = None
    descriptors: tuple[str, ...] = ()
    existing_tokens: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidContextError("BrandContext.name must be non-empty.")
        object.__setattr__(self, "descriptors", tuple(self.descriptors))
        if not isinstance(self.existing_tokens, MappingProxyType):
            object.__setattr__(
                self, "existing_tokens", MappingProxyType(dict(self.existing_tokens))
            )


@dataclass(frozen=True, slots=True)
class GoalContext:
    """The raw goals a strategy must serve, before synthesis.

    Attributes:
        business_goals: Stated business goals, verbatim.
        user_goals: Stated end-user goals, verbatim.
    """

    business_goals: tuple[str, ...] = ()
    user_goals: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "business_goals", tuple(self.business_goals))
        object.__setattr__(self, "user_goals", tuple(self.user_goals))

    @property
    def is_empty(self) -> bool:
        return not (self.business_goals or self.user_goals)
