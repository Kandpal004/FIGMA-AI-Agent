"""The Homepage Workflow runner — the thin, human-facing entry point.

A :class:`HomepageWorkflowRunner` wraps the Director facade with a small, task-shaped API for the
one job this workflow does: design a homepage. It translates a plain design brief into the
Director's :class:`SubmitPageDesign` command, drives the run through the Director (which provides
resumability, retry, events, stored reasoning, and the review gates), and exposes the operations a
creative director needs — resume an interrupted run, approve or reject the final design, and read
back the events, the stored reasoning, and the review results.

It is pure composition: it holds no design logic of its own. Every decision happens inside the
engines; every state transition happens inside the Director.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from director.application.director.commands import (
    ApproveStep,
    RejectStep,
    ResumeRun,
    SubmitPageDesign,
)
from director.domain.director.decision import DecisionRecord
from director.domain.shared.ids import RunId
from director.domain.shared.value_objects import PageType, Priority
from director.interfaces.dto import RunResultView, RunView

from homepage_workflow.composition import HomepageEnvironment
from homepage_workflow.definition import STEP_FINAL_APPROVAL

__all__ = ["HomepageWorkflowRunner"]


class HomepageWorkflowRunner:
    """Drives and inspects Homepage Design Workflow runs over a wired environment."""

    def __init__(self, environment: HomepageEnvironment) -> None:
        self._env = environment
        self._facade = environment.facade

    # ================================================================== #
    # Driving a run
    # ================================================================== #
    async def start(
        self,
        brief: Mapping[str, object],
        *,
        priority: Priority = Priority.NORMAL,
    ) -> RunResultView:
        """Start a homepage run for a brief and drive it to its first pause or terminal state.

        The run advances through every engine step automatically; it pauses at the manual
        ``final_approval`` gate awaiting a human sign-off (approve/reject).
        """
        command = SubmitPageDesign(
            tenant_id=self._env.tenant_id,
            project_id=self._env.project_id,
            page_section_id=self._env.page_section_id,
            page_type=PageType.HOMEPAGE,
            brief=dict(brief),
            priority=priority,
        )
        return await self._facade.submit_page(command)

    async def resume(self, run_id: RunId) -> RunResultView:
        """Resume an interrupted run from its persisted state."""
        return await self._facade.resume(ResumeRun(run_id=run_id))

    async def approve_final(
        self, run_id: RunId, *, approver: str = "creative_director", notes: tuple[str, ...] = ()
    ) -> RunResultView:
        """Approve the final design at the ``final_approval`` gate, completing the run."""
        return await self._facade.approve(
            ApproveStep(run_id=run_id, step_key=STEP_FINAL_APPROVAL, approver=approver, notes=notes)
        )

    async def reject_final(
        self, run_id: RunId, notes: tuple[str, ...], *, approver: str = "creative_director"
    ) -> RunResultView:
        """Reject the final design, rewinding to self-improvement for another round."""
        return await self._facade.reject(
            RejectStep(run_id=run_id, step_key=STEP_FINAL_APPROVAL, approver=approver, notes=notes)
        )

    async def design_homepage(
        self,
        brief: Mapping[str, object],
        *,
        auto_approve: bool = True,
        approver: str = "creative_director",
    ) -> RunResultView:
        """Design a homepage end to end.

        Runs the full pipeline; when it pauses at the final-approval gate, either signs off
        automatically (``auto_approve``) to complete the run, or returns the paused run for a human
        to decide.
        """
        result = await self.start(brief)
        if auto_approve and self._is_awaiting_final_approval(result.run):
            run_id = RunId.from_string(result.run.run_id)
            return await self.approve_final(run_id, approver=approver)
        return result

    # ================================================================== #
    # Inspecting a run
    # ================================================================== #
    async def status(self, run_id: RunId) -> RunView:
        """The current run state — status, current step, and per-step lifecycle."""
        return await self._facade.get_run(run_id)

    async def reasoning(self, run_id: RunId) -> Sequence[DecisionRecord]:
        """The Director's stored reasoning (decision log) for the run — every dispatch, advance,
        approval, rejection, and rollback, in order."""
        return await self._facade.get_history(run_id)

    async def review_results(self, run_id: RunId) -> tuple[DecisionRecord, ...]:
        """The stored review results — the approve/reject decisions the gates produced."""
        from director.domain.director.decision import DecisionKind

        history = await self._facade.get_history(run_id)
        return tuple(
            d for d in history
            if d.kind in (DecisionKind.APPROVE, DecisionKind.REJECT, DecisionKind.REQUEST_APPROVAL)
        )

    # ================================================================== #
    # Helpers
    # ================================================================== #
    @staticmethod
    def _is_awaiting_final_approval(run: RunView) -> bool:
        if run.current_step_key != STEP_FINAL_APPROVAL:
            return False
        for step in run.steps:
            if step.key == STEP_FINAL_APPROVAL:
                return step.state == "waiting_for_approval"
        return False
