"""The Director facade — the inbound entry point of the engine.

This is the single surface the layers *above* the engine (the FastAPI app, the
background worker, tests) call. It accepts application commands, delegates to the
:class:`DirectorService`, and returns serializable :class:`RunResultView` s —
never raw domain aggregates. It also offers read queries (fetch a run, fetch its
decision history) so callers never touch a repository directly.

The facade is deliberately thin: it owns no orchestration logic (that is the
Director's) and no persistence logic (that is the repositories'). It is the clean
seam that keeps transport concerns out of the application and application concerns
out of transport. There is no HTTP here — this is a backend facade, per the phase's
scope.
"""

from __future__ import annotations

from collections.abc import Sequence

from director.application.director.commands import (
    ApproveStep,
    CancelRun,
    ProvideInput,
    RejectStep,
    ResumeRun,
    SubmitPageDesign,
    SubmitSectionDesign,
)
from director.application.director.director_service import DirectorService
from director.application.ports.unit_of_work import UnitOfWorkFactory
from director.domain.director.decision import DecisionRecord
from director.domain.shared.ids import RunId
from director.interfaces.dto import RunResultView, RunView

__all__ = ["DirectorFacade"]


class DirectorFacade:
    """The engine's inbound API: commands in, views out."""

    def __init__(
        self, director: DirectorService, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        self._director = director
        self._uow = unit_of_work_factory

    # -- commands ---------------------------------------------------------- #
    async def submit_section(self, command: SubmitSectionDesign) -> RunResultView:
        """Start and drive a section-design run."""
        return RunResultView.from_result(await self._director.submit_section(command))

    async def submit_page(self, command: SubmitPageDesign) -> RunResultView:
        """Start and drive a page-design run."""
        return RunResultView.from_result(await self._director.submit_page(command))

    async def resume(self, command: ResumeRun) -> RunResultView:
        """Resume a run from its persisted state."""
        return RunResultView.from_result(await self._director.resume(command))

    async def approve(self, command: ApproveStep) -> RunResultView:
        """Approve a gate step and continue the run."""
        return RunResultView.from_result(await self._director.approve(command))

    async def reject(self, command: RejectStep) -> RunResultView:
        """Reject a gate step and continue the run."""
        return RunResultView.from_result(await self._director.reject(command))

    async def provide_input(self, command: ProvideInput) -> RunResultView:
        """Unblock a step with supplied input and continue the run."""
        return RunResultView.from_result(await self._director.provide_input(command))

    async def cancel(self, command: CancelRun) -> RunResultView:
        """Cancel a run."""
        return RunResultView.from_result(await self._director.cancel(command))

    # -- queries ----------------------------------------------------------- #
    async def get_run(self, run_id: RunId) -> RunView:
        """Return the current state of a run.

        Raises:
            NotFoundError: If no such run exists.
        """
        async with self._uow() as uow:
            run = await uow.runs.get(run_id)
        return RunView.from_run(run)

    async def get_history(self, run_id: RunId) -> Sequence[DecisionRecord]:
        """Return the Director's decision log for a run, in order."""
        async with self._uow() as uow:
            return await uow.decisions.list_for_run(run_id)
