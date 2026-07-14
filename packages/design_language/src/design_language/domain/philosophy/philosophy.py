"""The Philosophy model — the reasoned approach behind each visual dimension.

A :class:`Philosophy` captures the language's stance on one of the eleven dimensions (spacing,
grid, alignment, container, elevation, surface, motion, interaction, animation, layout,
component): the approach it takes and the principles that govern it, grounded in evidence. The
:class:`PhilosophySet` is the immutable collection, one philosophy per kind, and knows whether
the language is fully elaborated.

Pure domain: standard library, the shared-kernel error base, DL ids, and shared value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from design_language.domain.shared.ids import DLEvidenceId, PhilosophyId
from design_language.domain.shared.value_objects import PhilosophyKind

__all__ = ["InvalidPhilosophyError", "Philosophy", "PhilosophySet"]


class InvalidPhilosophyError(DesignDirectorError):
    """Raised when a philosophy or philosophy set is constructed with invalid data."""

    code = "invalid_design_language_philosophy"
    http_status = 422


@dataclass(frozen=True, slots=True)
class Philosophy:
    """The language's reasoned stance on one visual dimension.

    Attributes:
        id: Philosophy identity.
        kind: Which dimension it governs.
        approach: The chosen approach (a short statement of stance).
        principles: The principles that govern it.
        evidence_ids: The evidence grounding it.
    """

    id: PhilosophyId
    kind: PhilosophyKind
    approach: str
    principles: tuple[str, ...] = ()
    evidence_ids: tuple[DLEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.approach or not self.approach.strip():
            raise InvalidPhilosophyError("Philosophy.approach must be non-empty.")
        object.__setattr__(self, "principles", tuple(p for p in self.principles if p and p.strip()))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    def all_evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return self.evidence_ids


@dataclass(frozen=True, slots=True)
class PhilosophySet:
    """The immutable set of the language's philosophies, one per kind."""

    philosophies: tuple[Philosophy, ...] = ()

    def __post_init__(self) -> None:
        seen: set[PhilosophyKind] = set()
        for philosophy in self.philosophies:
            if philosophy.kind in seen:
                raise InvalidPhilosophyError(
                    "Duplicate philosophy kind in set.",
                    details={"kind": philosophy.kind.value},
                )
            seen.add(philosophy.kind)
        object.__setattr__(self, "philosophies", tuple(self.philosophies))

    @classmethod
    def of(cls, philosophies: Iterable[Philosophy]) -> PhilosophySet:
        return cls(philosophies=tuple(philosophies))

    def __len__(self) -> int:
        return len(self.philosophies)

    def __iter__(self):
        return iter(self.philosophies)

    def get(self, kind: PhilosophyKind) -> Philosophy | None:
        return next((p for p in self.philosophies if p.kind is kind), None)

    def kinds(self) -> frozenset[PhilosophyKind]:
        return frozenset(p.kind for p in self.philosophies)

    def evidence_ids(self) -> tuple[DLEvidenceId, ...]:
        return tuple(eid for p in self.philosophies for eid in p.all_evidence_ids())
