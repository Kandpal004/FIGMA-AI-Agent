"""The Competitive Brief — the engine's input.

A :class:`CompetitiveBrief` describes what to analyse: the industry, market, and
country, the business goals, the client's own baseline (its current per-dimension
scores, if known), and the candidate competitors to profile. The engine gathers
observations for these competitors through the data-source port, classifies them,
and produces the report.

Pure domain: standard library, the shared-kernel error base, the competitor entity,
and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from competitive.domain.competitor.competitor import Competitor
from competitive.domain.shared.value_objects import CompetitorDimension, Score

__all__ = ["CompetitiveBrief", "InvalidBriefError"]


class InvalidBriefError(DesignDirectorError):
    """Raised when a competitive brief is constructed with invalid data."""

    code = "invalid_brief"
    http_status = 422


@dataclass(frozen=True, slots=True)
class CompetitiveBrief:
    """What the Competitor Intelligence Engine is asked to analyse.

    Attributes:
        industry: The industry to analyse.
        market: The target market segment.
        country: The primary country.
        business_goals: The business goals the analysis must serve.
        client_name: The client brand's name.
        client_positioning: The client's positioning statement.
        client_baseline: The client's current score per dimension (may be partial;
            dimensions absent are treated as unknown/greenfield in gap analysis).
        competitors: The candidate competitors to profile.
        tenant_id: The viewer's tenant, for Knowledge scope resolution.
    """

    industry: str
    market: str = ""
    country: str = ""
    business_goals: tuple[str, ...] = ()
    client_name: str = ""
    client_positioning: str = ""
    client_baseline: Mapping[CompetitorDimension, Score] = field(
        default_factory=lambda: MappingProxyType({})
    )
    competitors: tuple[Competitor, ...] = ()
    tenant_id: object | None = None

    def __post_init__(self) -> None:
        if not self.industry or not self.industry.strip():
            raise InvalidBriefError("CompetitiveBrief.industry must be non-empty.")
        object.__setattr__(self, "business_goals", tuple(self.business_goals))
        object.__setattr__(self, "competitors", tuple(self.competitors))
        if not isinstance(self.client_baseline, MappingProxyType):
            object.__setattr__(
                self, "client_baseline", MappingProxyType(dict(self.client_baseline))
            )

    @classmethod
    def build(
        cls,
        industry: str,
        *,
        market: str = "",
        country: str = "",
        business_goals: Iterable[str] = (),
        client_name: str = "",
        client_positioning: str = "",
        client_baseline: Mapping[CompetitorDimension, Score] | None = None,
        competitors: Iterable[Competitor] = (),
        tenant_id: object | None = None,
    ) -> CompetitiveBrief:
        return cls(
            industry=industry,
            market=market,
            country=country,
            business_goals=tuple(business_goals),
            client_name=client_name,
            client_positioning=client_positioning,
            client_baseline=MappingProxyType(dict(client_baseline or {})),
            competitors=tuple(competitors),
            tenant_id=tenant_id,
        )
