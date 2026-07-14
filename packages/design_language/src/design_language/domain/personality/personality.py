"""The Personality model — the character of the language's expressive media.

A :class:`Personality` captures the character of one expressive medium (typography,
iconography, illustration, photography): the character it projects and the attributes that
define it, grounded in evidence. It fixes *how* type, icons, illustration, and photography must
feel — never a concrete font file or image. The :class:`PersonalitySet` is the immutable
collection, one personality per medium.

Pure domain: standard library, the shared-kernel error base, DL ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_language.domain.shared.ids import DLEvidenceId
from design_language.domain.shared.value_objects import PersonalityKind

__all__ = ["InvalidPersonalityError", "Personality", "PersonalitySet"]


class InvalidPersonalityError(DesignDirectorError):
    """Raised when a personality or personality set is constructed with invalid data."""

    code = "invalid_design_language_personality"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Personality:
    """The character of one expressive medium.

    Attributes:
        kind: Which medium it governs.
        character: The character it projects (a short statement).
        attributes: The defining attributes.
        evidence_ids: The evidence grounding it.
    """

    kind: PersonalityKind
    character: str
    attributes: tuple[str, ...] = ()
    evidence_ids: tuple[DLEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.character or not self.character.strip():
            raise InvalidPersonalityError("Personality.character must be non-empty.")
        object.__setattr__(self, "attributes", tuple(a for a in self.attributes if a and a.strip()))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return self.evidence_ids


@dataclass(frozen=True, slots=True)
class PersonalitySet:
    """The immutable set of the language's personalities, one per medium."""

    personalities: tuple[Personality, ...] = ()

    def __post_init__(self) -> None:
        seen: set[PersonalityKind] = set()
        for personality in self.personalities:
            if personality.kind in seen:
                raise InvalidPersonalityError(
                    "Duplicate personality kind in set.",
                    details={"kind": personality.kind.value},
                )
            seen.add(personality.kind)
        object.__setattr__(self, "personalities", tuple(self.personalities))

    @classmethod
    def of(cls, personalities: Iterable[Personality]) -> PersonalitySet:
        return cls(personalities=tuple(personalities))

    def __len__(self) -> int:
        return len(self.personalities)

    def __iter__(self):
        return iter(self.personalities)

    def get(self, kind: PersonalityKind) -> Personality | None:
        return next((p for p in self.personalities if p.kind is kind), None)

    def kinds(self) -> frozenset[PersonalityKind]:
        return frozenset(p.kind for p in self.personalities)

    def evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return tuple(eid for p in self.personalities for eid in p.all_evidence_ids())
