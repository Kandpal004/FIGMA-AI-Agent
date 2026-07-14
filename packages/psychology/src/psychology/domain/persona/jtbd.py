"""Jobs-to-be-Done — the progress a customer is trying to make, with the forces.

A :class:`JobToBeDone` follows the Christensen framing and models the **four forces of
progress** that make JTBD behavioral rather than descriptive: the *push* of the current
situation and the *pull* of the new solution (which drive change), against the *anxiety*
of the new and the *habit* of the present (which resist it). The net of these forces is
what actually predicts whether the customer switches.

Pure domain: standard library, the shared-kernel error base, psychology ids, and shared
value objects.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from core.errors import DesignDirectorError

from psychology.domain.shared.ids import JobToBeDoneId, PsychologyEvidenceId
from psychology.domain.shared.value_objects import Intensity, JobType

__all__ = ["ForcesOfProgress", "InvalidJTBDError", "JTBDSet", "JobToBeDone"]


class InvalidJTBDError(DesignDirectorError):
    """Raised when a job-to-be-done is constructed with invalid data."""

    code = "invalid_jtbd"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ForcesOfProgress:
    """The four forces acting on a switch decision.

    Attributes:
        push: The push of the current situation (drives change).
        pull: The pull of the new solution (drives change).
        anxiety: The anxiety of the new (resists change).
        habit: The habit of the present (resists change).
    """

    push: Intensity = Intensity(3)
    pull: Intensity = Intensity(3)
    anxiety: Intensity = Intensity(3)
    habit: Intensity = Intensity(3)

    @property
    def net_progress(self) -> int:
        """Forces for change minus forces against — positive favours switching."""
        return (int(self.push) + int(self.pull)) - (int(self.anxiety) + int(self.habit))

    @property
    def favours_switch(self) -> bool:
        return self.net_progress > 0


@dataclass(frozen=True, slots=True)
class JobToBeDone:
    """One cited job-to-be-done with its forces of progress.

    Attributes:
        id: Job identity.
        when_situation: The triggering situation ("When I…").
        motivation: The motivation ("I want to…").
        expected_outcome: The desired outcome ("so I can…").
        job_type: Whether the job is functional, emotional, or social.
        forces: The four forces of progress acting on the switch.
        evidence_ids: The evidence supporting it.
    """

    id: JobToBeDoneId
    when_situation: str
    motivation: str
    expected_outcome: str
    job_type: JobType
    forces: ForcesOfProgress = ForcesOfProgress()
    evidence_ids: tuple[PsychologyEvidenceId, ...] = ()

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

    def evidence_ids(self) -> tuple[PsychologyEvidenceId, ...]:
        return tuple(eid for j in self.jobs for eid in j.evidence_ids)
