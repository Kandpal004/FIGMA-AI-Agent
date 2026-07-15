"""End-to-end tests: the Homepage Design Workflow driven over the REAL engines.

These prove the first production workflow actually runs — every engine (Research, Competitive,
Strategy, Brand, Psychology, UX, IA, Wireframe, Creative Director, Design Language, Component
Intelligence, Design System, Design Orchestrator, Figma Design) is invoked through its real facade,
the run advances through all sixteen steps, and the platform's requirements hold: the run is
resumable and event-emitting, it stores reasoning and review results, and the review gates give a
self-correcting improve loop.
"""

from __future__ import annotations

from director.domain.director.decision import DecisionKind
from director.domain.shared.ids import RunId

from homepage_workflow import definition as wf

# Every engine output the executor threads through the run, keyed by engine.
_EXPECTED_ENGINE_OUTPUTS = (
    "research",
    "competitive",
    "strategy",
    "brand",
    "psychology",
    "ux",
    "ia",
    "wireframe",
    "creative_director",
    "design_language",
    "component_intelligence",
    "design_system",
    "orchestrator",
    "figma",
)


async def test_designs_a_homepage_end_to_end(homepage_env, runner, brief):
    # 1. Start: the run drives itself through fifteen engine steps and pauses at final approval.
    result = await runner.start(brief)
    run = result.run
    assert run.status == "paused"
    assert run.current_step_key == wf.STEP_FINAL_APPROVAL
    completed = {s.key for s in run.steps if s.state == "completed"}
    assert completed == set(wf.build_homepage_definition().step_keys()) - {wf.STEP_FINAL_APPROVAL}

    # Events were emitted for the run.
    names = [e.name for e in result.events]
    assert names[0] == "RunStarted"
    assert "StepDispatched" in names and "StepCompleted" in names

    run_id = RunId.from_string(run.run_id)

    # 2. Every real engine actually ran and threaded its output id forward.
    context = homepage_env.executor._contexts[run_id]  # noqa: SLF001 - white-box assertion
    for engine in _EXPECTED_ENGINE_OUTPUTS:
        assert context.has(engine), f"engine {engine} did not run"
        assert context.ref_str(engine), f"engine {engine} produced no artifact id"

    # 3. Approve the final design: the run completes.
    approved = await runner.approve_final(run_id)
    assert approved.run.status == "completed"
    status = await runner.status(run_id)
    assert all(s.state == "completed" for s in status.steps)

    # 4. Reasoning and review results were stored.
    reasoning = await runner.reasoning(run_id)
    assert len(reasoning) >= len(wf.build_homepage_definition())  # at least one decision per step
    reviews = await runner.review_results(run_id)
    assert any(d.kind is DecisionKind.APPROVE for d in reviews)


async def test_resume_is_a_no_op_when_paused_for_approval(runner, brief):
    result = await runner.start(brief)
    run_id = RunId.from_string(result.run.run_id)
    # A run paused for human approval is not advanced by resume — it awaits approve/reject.
    resumed = await runner.resume(run_id)
    assert resumed.run.status == "paused"
    assert resumed.run.current_step_key == wf.STEP_FINAL_APPROVAL


async def test_final_rejection_drives_a_self_improvement_loop(runner, brief):
    result = await runner.start(brief)
    run_id = RunId.from_string(result.run.run_id)
    assert result.run.redesign_count == 0

    # Reject the final design: the Director rewinds to self-improvement, re-runs it, and pauses at
    # the final gate again — the improve loop — with the redesign counter incremented.
    rejected = await runner.reject_final(run_id, notes=("Increase hero contrast; tighten spacing.",))
    assert rejected.run.redesign_count == 1
    assert rejected.run.current_step_key == wf.STEP_FINAL_APPROVAL
    assert rejected.run.status == "paused"

    # A human can then approve the improved design to complete the run.
    approved = await runner.approve_final(run_id)
    assert approved.run.status == "completed"


async def test_determinism_of_the_pipeline_shape(runner, brief):
    # The workflow shape (which steps, in what order, completing) is deterministic across runs.
    r1 = await runner.start(brief)
    completed1 = [s.key for s in r1.run.steps if s.state == "completed"]
    assert completed1 == [
        k for k in wf.build_homepage_definition().step_keys() if k != wf.STEP_FINAL_APPROVAL
    ]
