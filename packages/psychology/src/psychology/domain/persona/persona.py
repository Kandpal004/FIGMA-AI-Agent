"""Customer personas — the empathetic portrait of who is deciding.

A :class:`CustomerPersona` is a cited, structured portrait of a target customer: their
demographics and psychographics, what they want, and what they fear. The
:class:`PersonaSet` is the immutable collection produced by persona synthesis.

Pure domain: standard library, the shared-kernel error base, psychology ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from core.errors import DesignDirectorError

from psychology.domain.shared.ids import CustomerPersonaId, PsychologyEvidenceId
from psychology.domain.shared.value_objects import AwarenessLevel, Confidence

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
        name: A memorable persona name.
        archetype: The archetype it represents.
        awareness: The awareness level this persona typically enters at.
        confidence: Confidence in the persona.
        demographics: Structured demographic attributes (read-only).
        psychographics: Structured psychographic attributes (read-only).
        goals: What this persona is trying to accomplish.
        fears: What they are afraid of.
        evidence_ids: The evidence supporting it.
    """

    id: CustomerPersonaId
    name: str
    archetype: str
    awareness: AwarenessLevel
    confidence: Confidence
    demographics: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    psychographics: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    goals: tuple[str, ...] = ()
    fears: tuple[str, ...] = ()
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise InvalidPersonaError("CustomerPersona.name must be non-empty.")
        if not isinstance(self.demographics, MappingProxyType):
            object.__setattr__(self, "demographics", MappingProxyType(dict(self.demographics)))
        if not isinstance(self.psychographics, MappingProxyType):
            object.__setattr__(self, "psychographics", MappingProxyType(dict(self.psychographics)))
        object.__setattr__(self, "goals", tuple(self.goals))
        object.__setattr__(self, "fears", tuple(self.fears))
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

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for p in self.personas for eid in p.evidence_ids)
