"""Customer personas — who the ideal customer is.

A :class:`CustomerPersona` is a cited, structured portrait of a target customer: an
archetype, demographics and psychographics, what they want, and what frustrates them.
The :class:`PersonaSet` is the immutable collection produced by customer synthesis.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import CustomerPersonaId, StrategyEvidenceId
from strategy.domain.shared.value_objects import Confidence

__all__ = ["CustomerPersona", "InvalidPersonaError", "PersonaSet"]


class InvalidPersonaError(DesignDirectorError):
    """Raised when a persona is constructed with invalid data."""

    code = "invalid_customer_persona"
    http_status = 422


@dataclass(frozen=True, slots=True)
class CustomerPersona:
    """A cited portrait of a target customer.

    Attributes:
        id: Persona identity.
        name: A memorable persona name (e.g. "Considered Claire").
        archetype: The archetype it represents (e.g. "value-driven researcher").
        demographics: Structured demographic attributes (read-only).
        psychographics: Structured psychographic attributes (read-only).
        goals: What this persona is trying to accomplish.
        frustrations: What gets in their way today.
        confidence: Confidence in the persona.
        evidence_ids: The evidence supporting it.
    """

    id: CustomerPersonaId
    name: str
    archetype: str
    confidence: Confidence
    demographics: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    psychographics: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )
    goals: tuple[str, ...] = ()
    frustrations: tuple[str, ...] = ()
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidPersonaError("CustomerPersona.name must be non-empty.")
        if not isinstance(self.demographics, MappingProxyType):
            object.__setattr__(
                self, "demographics", MappingProxyType(dict(self.demographics))
            )
        if not isinstance(self.psychographics, MappingProxyType):
            object.__setattr__(
                self, "psychographics", MappingProxyType(dict(self.psychographics))
            )
        object.__setattr__(self, "goals", tuple(self.goals))
        object.__setattr__(self, "frustrations", tuple(self.frustrations))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class PersonaSet:
    """An immutable set of customer personas, primary first."""

    personas: tuple[CustomerPersona, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "personas", tuple(self.personas))

    @classmethod
    def of(cls, personas: Iterable[CustomerPersona]) -> PersonaSet:
        return cls(personas=tuple(personas))

    def __len__(self) -> int:
        return len(self.personas)

    def __iter__(self):
        return iter(self.personas)

    @property
    def primary(self) -> CustomerPersona | None:
        return self.personas[0] if self.personas else None

    def evidence_ids(self) -> tuple[StrategyEvidenceId, ...]:
        return tuple(eid for p in self.personas for eid in p.evidence_ids)
