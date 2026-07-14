"""Stage — Execution Order Resolution.

The planner proposes sections and their dependencies; this stage computes the deterministic
build order. It performs a stable topological sort over the section-dependency edges (a
dependency must be built before the section that needs it) and stamps each section's
``execution_order``. A cyclic dependency set is not executable, so it is rejected here with a
precise error — before the plan is ever assembled.

The sort is stable: among sections with no outstanding dependency, the original blueprint
order (page order, then section order, then higher priority first) breaks ties, so the same
draft always yields the same execution order.
"""

from __future__ import annotations

from dataclasses import replace

from core.errors import DesignDirectorError

from wireframe.domain.plan.blueprint import PlanBlueprint
from wireframe.domain.section.section_plan import SectionPlan
from wireframe.domain.shared.ids import SectionId

__all__ = ["CyclicDependencyError", "OrderingResolver"]


class CyclicDependencyError(DesignDirectorError):
    """Raised when the section-dependency set contains a cycle."""

    code = "wireframe_cyclic_dependency"
    http_status = 422


class OrderingResolver:
    """Assigns a deterministic execution order to every section via topological sort."""

    def resolve(self, blueprint: PlanBlueprint) -> PlanBlueprint:
        sections = blueprint.sections()
        present: frozenset[SectionId] = blueprint.section_ids()
        index = {s.id: i for i, s in enumerate(sections)}

        # Dependencies restricted to sections that actually exist in the plan.
        deps: dict[SectionId, set[SectionId]] = {
            s.id: {d for d in s.dependencies if d in present} for s in sections
        }
        dependents: dict[SectionId, list[SectionId]] = {s.id: [] for s in sections}
        for sid, ds in deps.items():
            for d in ds:
                dependents[d].append(sid)
        in_degree = {sid: len(ds) for sid, ds in deps.items()}

        ready = sorted((s.id for s in sections if in_degree[s.id] == 0), key=lambda i: index[i])
        order: dict[SectionId, int] = {}
        counter = 0
        while ready:
            current = ready.pop(0)
            order[current] = counter
            counter += 1
            freed: list[SectionId] = []
            for dependent in dependents[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    freed.append(dependent)
            if freed:
                ready.extend(freed)
                ready.sort(key=lambda i: index[i])

        if len(order) != len(sections):
            unresolved = [str(s.id) for s in sections if s.id not in order]
            raise CyclicDependencyError(
                "Section dependencies form a cycle; no valid build order exists.",
                details={"unresolved_sections": unresolved},
            )

        ordered_pages = tuple(
            replace(
                page,
                sections=tuple(
                    replace(section, execution_order=order[section.id])
                    for section in page.sections
                ),
            )
            for page in blueprint.pages
        )
        return PlanBlueprint.of(ordered_pages)
