"""The Workflow Engine — selection and navigation over workflow definitions.

The Workflow Engine is the application service the Director consults to answer
the *"what next?"* questions: which workflow designs this page, which definition
a run is executing, what the first step is, what follows a given step, and —
when a gate rejects — which earlier step to rewind to. It owns no control flow of
its own (that is the Director's); it is a stateless navigator over the injected
:class:`~director.domain.workflow.catalog.WorkflowCatalog`.

Keeping this logic here, rather than in the Director, means the Director does not
need to know how definitions are stored or resolved, and the two-tier PAGE/SECTION
model is expressed once, in data (the catalog), and navigated uniformly.

Testing considerations
----------------------
* :meth:`definition_for_run` resolves a run's ``(workflow_key, version)`` back to
  its definition.
* :meth:`first_step` / :meth:`next_step` / :meth:`resolve_rollback` delegate to
  the definition and behave exactly as its navigation does.
"""

from __future__ import annotations

from director.domain.shared.value_objects import PageType
from director.domain.workflow.catalog import WorkflowCatalog
from director.domain.workflow.definition import WorkflowDefinition, WorkflowStepSpec
from director.domain.workflow.run import WorkflowRun

__all__ = ["WorkflowEngine"]


class WorkflowEngine:
    """Selects and navigates workflow definitions on the Director's behalf."""

    def __init__(self, catalog: WorkflowCatalog) -> None:
        self._catalog = catalog

    # -- selection --------------------------------------------------------- #
    def section_workflow(self) -> WorkflowDefinition:
        """The canonical section-design workflow."""
        return self._catalog.section_design()

    def page_workflow(self, page_type: PageType) -> WorkflowDefinition:
        """The page-level workflow for ``page_type``.

        Raises:
            WorkflowNotFoundError: If no page workflow is registered.
        """
        return self._catalog.for_page(page_type)

    def get_definition(self, key: str, version: int | None = None) -> WorkflowDefinition:
        """Resolve a definition by key (and optional version).

        Raises:
            WorkflowNotFoundError: If no matching definition exists.
        """
        return self._catalog.get(key, version)

    def definition_for_run(self, run: WorkflowRun) -> WorkflowDefinition:
        """The definition a run is executing.

        Raises:
            WorkflowNotFoundError: If the run references an unknown definition.
        """
        return self._catalog.get(run.workflow_key, run.workflow_version)

    # -- navigation -------------------------------------------------------- #
    def first_step(self, definition: WorkflowDefinition) -> WorkflowStepSpec:
        """The first step of a definition."""
        return definition.first_step

    def spec_for(self, definition: WorkflowDefinition, step_key: str) -> WorkflowStepSpec:
        """The spec for ``step_key``.

        Raises:
            StepNotFoundError: If the step is unknown.
        """
        return definition.get_step(step_key)

    def next_step(
        self, definition: WorkflowDefinition, step_key: str
    ) -> WorkflowStepSpec | None:
        """The step following ``step_key`` on the happy path, or ``None`` if it is
        the last step."""
        return definition.next_step(step_key)

    def is_last(self, definition: WorkflowDefinition, step_key: str) -> bool:
        """Whether ``step_key`` is the final step of the definition."""
        return definition.is_last(step_key)

    def resolve_rollback(
        self, definition: WorkflowDefinition, gate_key: str
    ) -> WorkflowStepSpec | None:
        """The step a gate rewinds to on rejection, or ``None`` if its policy does
        not rewind."""
        return definition.resolve_rollback(gate_key)

    def steps_between(
        self, definition: WorkflowDefinition, from_key: str, to_key: str
    ) -> tuple[WorkflowStepSpec, ...]:
        """The steps from ``from_key`` up to and including ``to_key`` (inclusive),
        in order. Used by rollback to reset the redesign span.

        Raises:
            StepNotFoundError: If either key is unknown.
        """
        start = definition.index_of(from_key)
        end = definition.index_of(to_key)
        lo, hi = (start, end) if start <= end else (end, start)
        return tuple(definition.step_at(i) for i in range(lo, hi + 1))
