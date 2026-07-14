"""Jobs-to-be-Done — the progress a customer is trying to make.

A :class:`JobToBeDone` follows the Christensen framing: in a *situation*, a customer
is *motivated* to reach an *expected outcome*. Typing the job (functional / emotional
/ social) lets messaging and value strategy speak to the right register. The
:class:`JTBDSet` is the immutable collection produced by customer synthesis.

Pure domain: standard library, the shared-kernel error base, strategy ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from strategy.domain.shared.ids import JobToBeDoneId, StrategyEvidenceId
from strategy.domain.shared.value_objects import JobType

__all__ = ["InvalidJTBDError", "JTBDSet", "JobToBeDone"]


class InvalidJTBDError(DesignDirectorError):
    """Raised when a job-to-be-done is constructed with invalid data."""

    code = "invalid_jtbd"
    http_status = 422


@dataclass(frozen=True, slots=True)
class JobToBeDone:
    """One cited job-to-be-done.

    Attributes:
        id: Job identity.
        when_situation: The triggering situation ("When I…").
        motivation: The motivation ("I want to…").
        expected_outcome: The desired outcome ("so I can…").
        job_type: Whether the job is functional, emotional, or social.
        evidence_ids: The evidence supporting it.
    """

    id: JobToBeDoneId
    when_situation: str
    motivation: str
    expected_outcome: str
    job_type: JobType
    evidence_ids: tuple[StrategyEvidenceId, ...] = ()

    def __post_init__(self) -> None:
        for name in ("when_situation", "motivation", "expected_outcome"):
            value = getattr(self, name)
            if not value or not value.strip():
                raise InvalidJTBDError(f"JobToBeDone.{name} must be non-empty.")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def statement(self) -> str:
        """The canonical one-line JTBD statement."""
        return (
            f"When {self.when_situation}, I want to {self.motivation}, "
            f"so I can {self.expected_outcome}."
        )


@dataclass(frozen=True, slots=True)
class JTBDSet:
    """An immutable set of jobs-to-be-done."""

    jobs: tuple[JobToBeDone, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "jobs", tuple(self.jobs))

    @classmethod
    def of(cls, jobs: Iterable[JobToBeDone]) -> JTBDSet:
        return cls(jobs=tuple(jobs))

    def __len__(self) -> int:
        return len(self.jobs)

    def __iter__(self):
        return iter(self.jobs)

    def by_type(self, job_type: JobType) -> tuple[JobToBeDone, ...]:
        return tuple(j for j in self.jobs if j.job_type is job_type)

    def evidence_ids(self) -> tuple[StrategyEvidenceId, ...]:
        return tuple(eid for j in self.jobs for eid in j.evidence_ids)
