"""UX laws — the applied heuristics that make every decision defensible.

A :class:`UXLawApplication` records how one UX law/heuristic (Jakob, Hick, Fitts, Miller,
Tesler, Occam, progressive disclosure, Gestalt, Nielsen, Baymard, WCAG) applies to the
strategy — where it applies, why, its enforcement strength, and the guardrail that keeps
its use sound. The :class:`UXLawLens` groups all applications; covering all eleven laws is
a quality dimension. WCAG applications carry a conformance level.

Pure domain: standard library, the shared-kernel error base, UX ids, and shared value
objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from ux.domain.shared.ids import UXEvidenceId
from ux.domain.shared.value_objects import RuleEnforcement, UXLaw, WCAGLevel

__all__ = ["InvalidLawError", "UXLawApplication", "UXLawLens"]


class InvalidLawError(DesignDirectorError):
    """Raised when a UX law application is constructed with invalid data."""

    code = "invalid_ux_law_application"
    http_status = 422


@dataclass(frozen=True, slots=True)
class UXLawApplication:
    """One cited application of a UX law / heuristic.

    Attributes:
        law: The law being applied.
        where_applies: Where in the strategy it applies.
        rationale: Why it applies and what it drives.
        enforcement: How strongly it is enforced.
        wcag_level: The WCAG level, when ``law`` is WCAG.
        guardrail: The rule that keeps its use sound (e.g. no dark patterns from scarcity).
        evidence_ids: The evidence supporting it.
    """

    law: UXLaw
    where_applies: str
    rationale: str = ""
    enforcement: RuleEnforcement = RuleEnforcement.SHOULD
    wcag_level: WCAGLevel | None = None
    guardrail: str = ""
    evidence_ids: tuple[UXEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        if not self.where_applies or not self.where_applies.strip():
            raise InvalidLawError("UXLawApplication.where_applies must be non-empty.")
        if self.law is UXLaw.WCAG and self.wcag_level is None:
            object.__setattr__(self, "wcag_level", WCAGLevel.AA)
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))


@dataclass(frozen=True, slots=True)
class UXLawLens:
    """The consolidated set of applied UX laws / heuristics."""

    applications: tuple[UXLawApplication, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "applications", tuple(self.applications))

    @classmethod
    def of(cls, applications: Iterable[UXLawApplication]) -> UXLawLens:
        return cls(applications=tuple(applications))

    def __len__(self) -> int:
        return len(self.applications)

    def __iter__(self):
        return iter(self.applications)

    def laws(self) -> frozenset[UXLaw]:
        return frozenset(a.law for a in self.applications)

    def for_law(self, law: UXLaw) -> tuple[UXLawApplication, ...]:
        return tuple(a for a in self.applications if a.law is law)

    def evidence_ids(self) -> tuple[UXEvidenceId, ...]:
        return tuple(eid for a in self.applications for eid in a.evidence_ids)
