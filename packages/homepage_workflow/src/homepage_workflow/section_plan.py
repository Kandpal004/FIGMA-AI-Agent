"""The Homepage Design Plan output model — the structured, section-by-section deliverable.

This is the *output* the Homepage Workflow produces: not a new engine, port, or domain layer, but
the plain, immutable data structure the workflow emits — a :class:`HomepageDesignPlan` composed of
one :class:`SectionDesignPlan` per homepage section. Each section plan carries exactly the thirteen
attributes a senior D2C creative director specifies for a section (purpose, the business/customer/
conversion goals, required components and assets, content, CTA and trust strategy, responsive/
accessibility/animation guidance, and a review checklist), plus the required envelope — reasoning,
design intent, dependencies, review score, approval status — and serialises to structured JSON.

Every section plan is bound by the platform's :data:`FIGMA_CONSTRAINTS` (auto-layout only, variables
only, components + variants only, no absolute positioning, no unnecessary layers, no raster text,
reusable components), so the plan is *ready for Figma generation* under exactly those rules.

Pure output data: standard library and the shared-kernel error base only. Component types are held
as their canonical string keys (aligned with the engines' component enums) so this model stays a
self-contained deliverable, free of engine imports.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from core.errors import DesignDirectorError

__all__ = [
    "FIGMA_CONSTRAINTS",
    "HOMEPAGE_SECTIONS",
    "ApprovalStatus",
    "FigmaConstraints",
    "HomepageDesignPlan",
    "InvalidSectionPlanError",
    "SectionRole",
    "SectionSpec",
    "SectionDesignPlan",
]


class InvalidSectionPlanError(DesignDirectorError):
    """Raised when a section or homepage design plan is constructed with invalid data."""

    code = "invalid_homepage_section_plan"
    http_status = 422


# --------------------------------------------------------------------------- #
# Approval status                                                              #
# --------------------------------------------------------------------------- #
class ApprovalStatus(str, Enum):
    """The lifecycle status of a section plan under the Creative Director gate."""

    PENDING = "pending"
    IMPROVING = "improving"
    APPROVED = "approved"
    REJECTED = "rejected"


# --------------------------------------------------------------------------- #
# Section role                                                                 #
# --------------------------------------------------------------------------- #
class SectionRole(str, Enum):
    """The primary job a homepage section does — drives its CTA and trust strategy."""

    NAVIGATION = "navigation"
    HERO = "hero"
    TRUST = "trust"
    VALUE = "value"
    DISCOVERY = "discovery"
    SOCIAL_PROOF = "social_proof"
    CONVERSION = "conversion"
    CONTENT = "content"
    FOOTER = "footer"


# --------------------------------------------------------------------------- #
# The homepage section taxonomy                                                #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class SectionSpec:
    """One entry in the ordered homepage section taxonomy.

    Attributes:
        key: The stable section key (unique; e.g. ``"hero"``, ``"trust_bar"``).
        title: Human-readable label.
        component: The canonical component-type key the section is built from (aligned with the
            Component Intelligence / Design System component enums).
        role: The primary job the section does.
        above_the_fold: Whether the section is expected above the fold on desktop.
    """

    key: str
    title: str
    component: str
    role: SectionRole
    above_the_fold: bool = False

    def __post_init__(self) -> None:
        if not self.key or not self.key.strip():
            raise InvalidSectionPlanError("SectionSpec.key must be non-empty.")
        if not self.component or not self.component.strip():
            raise InvalidSectionPlanError("SectionSpec.component must be non-empty.")


#: The canonical, ordered homepage section taxonomy — the fourteen sections a world-class D2C
#: homepage is composed from, top to bottom. Each maps to the component the engines already model.
HOMEPAGE_SECTIONS: tuple[SectionSpec, ...] = (
    SectionSpec("announcement_bar", "Announcement Bar", "announcement_bar",
                SectionRole.NAVIGATION, above_the_fold=True),
    SectionSpec("header", "Header", "header", SectionRole.NAVIGATION, above_the_fold=True),
    SectionSpec("hero", "Hero", "hero", SectionRole.HERO, above_the_fold=True),
    SectionSpec("trust_bar", "Trust Bar", "trust_badges", SectionRole.TRUST, above_the_fold=True),
    SectionSpec("usp", "USP Section", "usp_grid", SectionRole.VALUE),
    SectionSpec("featured_collections", "Featured Collections", "collection_grid",
                SectionRole.DISCOVERY),
    SectionSpec("featured_products", "Featured Products", "product_grid", SectionRole.DISCOVERY),
    SectionSpec("category_grid", "Category Grid", "category_grid", SectionRole.DISCOVERY),
    SectionSpec("social_proof", "Social Proof", "testimonials", SectionRole.SOCIAL_PROOF),
    SectionSpec("testimonials", "Testimonials", "testimonials", SectionRole.SOCIAL_PROOF),
    SectionSpec("reviews", "Reviews", "reviews", SectionRole.SOCIAL_PROOF),
    SectionSpec("faq", "FAQ", "faq", SectionRole.CONTENT),
    SectionSpec("newsletter", "Newsletter", "newsletter", SectionRole.CONVERSION),
    SectionSpec("footer", "Footer", "footer", SectionRole.FOOTER),
)


def section_spec(key: str) -> SectionSpec:
    """Return the taxonomy entry for ``key``.

    Raises:
        InvalidSectionPlanError: If no section with that key exists.
    """
    for spec in HOMEPAGE_SECTIONS:
        if spec.key == key:
            return spec
    raise InvalidSectionPlanError(f"Unknown homepage section {key!r}.", details={"key": key})


# --------------------------------------------------------------------------- #
# Figma constraints                                                            #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class FigmaConstraints:
    """The non-negotiable Figma-generation rules every section plan is bound by.

    A plan produced under these constraints is *ready for Figma generation* with no absolute
    positioning, no raster text, and everything driven by variables, components, and variants.
    """

    auto_layout_only: bool = True
    variables_only: bool = True
    components_only: bool = True
    variants_only: bool = True
    no_absolute_positioning: bool = True
    no_unnecessary_layers: bool = True
    no_raster_text: bool = True
    reusable_components: bool = True

    def rules(self) -> tuple[str, ...]:
        """The active rules as human-readable statements (for the plan and handoff)."""
        statements: list[str] = []
        if self.auto_layout_only:
            statements.append("Use Auto Layout for every frame; no absolute positioning.")
        if self.variables_only:
            statements.append("Bind every colour, spacing, radius and type value to a Variable.")
        if self.components_only:
            statements.append("Build every repeated element as a Component.")
        if self.variants_only:
            statements.append("Express component states and options as Variants, not copies.")
        if self.no_absolute_positioning:
            statements.append("No absolutely-positioned layers.")
        if self.no_unnecessary_layers:
            statements.append("No empty or redundant layers; keep the tree lean.")
        if self.no_raster_text:
            statements.append("All text is live text, never rasterised.")
        if self.reusable_components:
            statements.append("Reuse library components and instances; do not detach.")
        return tuple(statements)

    def to_json(self) -> dict[str, object]:
        return {
            "auto_layout_only": self.auto_layout_only,
            "variables_only": self.variables_only,
            "components_only": self.components_only,
            "variants_only": self.variants_only,
            "no_absolute_positioning": self.no_absolute_positioning,
            "no_unnecessary_layers": self.no_unnecessary_layers,
            "no_raster_text": self.no_raster_text,
            "reusable_components": self.reusable_components,
            "rules": list(self.rules()),
        }


#: The platform-wide Figma constraints applied to every homepage plan.
FIGMA_CONSTRAINTS = FigmaConstraints()

#: The Creative Director's review-score bar a section must clear to be approved.
APPROVAL_SCORE_THRESHOLD = 95.0


def _clean_tuple(values: Iterable[str] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    return tuple(v.strip() for v in values if v and v.strip())


# --------------------------------------------------------------------------- #
# The section design plan                                                      #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class SectionDesignPlan:
    """The complete, cited design plan for one homepage section.

    Carries the thirteen creative-director attributes plus the required envelope (reasoning,
    design intent, dependencies, review score, approval status) and the Figma constraints. It
    serialises to structured JSON via :meth:`to_json`.

    Attributes:
        section_key: The section this plans (a taxonomy key).
        title: Human-readable section label.
        component: The component-type key the section is built from.
        order: The 1-based position of the section on the page.
        role: The primary job of the section.
        purpose: Why the section exists.
        business_goal: The business outcome it advances.
        customer_goal: The customer need it serves.
        conversion_goal: The conversion outcome it drives.
        required_components: The components the section needs (including dependencies).
        required_assets: The assets (images, icons, logos) the section needs.
        content_requirements: The content the section must be supplied.
        cta_strategy: How the section drives action.
        trust_strategy: How the section builds trust and reduces anxiety.
        responsive_behaviour: How the section adapts per breakpoint (band → note).
        accessibility_requirements: The a11y requirements the section must meet.
        animation_guidance: How the section should animate (restraint-first).
        review_checklist: The checklist the Creative Director reviews the section against.
        reasoning: Why these choices were made (grounded in the engines' evidence).
        design_intent: The one-line design intent for the section.
        dependencies: Other sections/components this section depends on.
        review_score: The Creative Director's 0–100 review score.
        approval_status: The section's approval lifecycle status.
        figma_constraints: The Figma-generation rules the section is bound by.
        evidence_refs: The upstream spec ids the plan was projected from (audit anchors).
    """

    section_key: str
    title: str
    component: str
    order: int
    role: SectionRole
    purpose: str
    business_goal: str
    customer_goal: str
    conversion_goal: str
    required_components: tuple[str, ...]
    required_assets: tuple[str, ...]
    content_requirements: tuple[str, ...]
    cta_strategy: str
    trust_strategy: str
    responsive_behaviour: Mapping[str, str]
    accessibility_requirements: tuple[str, ...]
    animation_guidance: str
    review_checklist: tuple[str, ...]
    reasoning: str
    design_intent: str
    dependencies: tuple[str, ...] = ()
    review_score: float = 0.0
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    figma_constraints: FigmaConstraints = FIGMA_CONSTRAINTS
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("section_key", "title", "component", "purpose", "business_goal",
                     "customer_goal", "conversion_goal", "cta_strategy", "trust_strategy",
                     "animation_guidance", "reasoning", "design_intent"):
            value = getattr(self, name)
            if not value or not str(value).strip():
                raise InvalidSectionPlanError(
                    f"SectionDesignPlan.{name} must be non-empty.",
                    details={"section": self.section_key},
                )
        if not isinstance(self.order, int) or isinstance(self.order, bool) or self.order < 1:
            raise InvalidSectionPlanError("SectionDesignPlan.order must be an int >= 1.")
        if not 0.0 <= self.review_score <= 100.0:
            raise InvalidSectionPlanError(
                "SectionDesignPlan.review_score must be within [0, 100].",
                details={"section": self.section_key, "score": self.review_score},
            )
        object.__setattr__(self, "required_components", _clean_tuple(self.required_components))
        object.__setattr__(self, "required_assets", _clean_tuple(self.required_assets))
        object.__setattr__(self, "content_requirements", _clean_tuple(self.content_requirements))
        object.__setattr__(
            self, "accessibility_requirements", _clean_tuple(self.accessibility_requirements)
        )
        object.__setattr__(self, "review_checklist", _clean_tuple(self.review_checklist))
        object.__setattr__(self, "dependencies", _clean_tuple(self.dependencies))
        object.__setattr__(self, "evidence_refs", _clean_tuple(self.evidence_refs))
        responsive = {
            str(bp).strip(): str(note).strip()
            for bp, note in self.responsive_behaviour.items()
            if str(bp).strip() and str(note).strip()
        }
        object.__setattr__(self, "responsive_behaviour", MappingProxyType(responsive))

    @property
    def is_approved(self) -> bool:
        return self.approval_status is ApprovalStatus.APPROVED

    def with_review(self, score: float, status: ApprovalStatus) -> SectionDesignPlan:
        """Return a copy with the review score and approval status set."""
        import dataclasses

        return dataclasses.replace(self, review_score=score, approval_status=status)

    def to_json(self) -> dict[str, object]:
        """Serialise the section plan to a structured, JSON-safe dict."""
        return {
            "section_key": self.section_key,
            "title": self.title,
            "component": self.component,
            "order": self.order,
            "role": self.role.value,
            "purpose": self.purpose,
            "business_goal": self.business_goal,
            "customer_goal": self.customer_goal,
            "conversion_goal": self.conversion_goal,
            "required_components": list(self.required_components),
            "required_assets": list(self.required_assets),
            "content_requirements": list(self.content_requirements),
            "cta_strategy": self.cta_strategy,
            "trust_strategy": self.trust_strategy,
            "responsive_behaviour": dict(self.responsive_behaviour),
            "accessibility_requirements": list(self.accessibility_requirements),
            "animation_guidance": self.animation_guidance,
            "review_checklist": list(self.review_checklist),
            "reasoning": self.reasoning,
            "design_intent": self.design_intent,
            "dependencies": list(self.dependencies),
            "review_score": self.review_score,
            "approval_status": self.approval_status.value,
            "figma_constraints": self.figma_constraints.to_json(),
            "evidence_refs": list(self.evidence_refs),
        }


# --------------------------------------------------------------------------- #
# The homepage design plan                                                     #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class HomepageDesignPlan:
    """The complete homepage design plan — the ordered, approved section plans plus metadata.

    Attributes:
        brand_name: The brand this homepage is for.
        project_id: The owning project / run reference.
        sections: The ordered section plans.
        source_refs: The upstream spec ids the plan was built from (audit anchors).
        created_at: An ISO timestamp, supplied by the caller.
    """

    brand_name: str
    project_id: str
    sections: tuple[SectionDesignPlan, ...]
    source_refs: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.brand_name or not self.brand_name.strip():
            raise InvalidSectionPlanError("HomepageDesignPlan.brand_name must be non-empty.")
        sections = tuple(self.sections)
        orders = [s.order for s in sections]
        if len(set(orders)) != len(orders):
            raise InvalidSectionPlanError("Section orders must be unique within the plan.")
        keys = [s.section_key for s in sections]
        if len(set(keys)) != len(keys):
            raise InvalidSectionPlanError("Section keys must be unique within the plan.")
        object.__setattr__(self, "sections", tuple(sorted(sections, key=lambda s: s.order)))
        if not isinstance(self.source_refs, MappingProxyType):
            object.__setattr__(self, "source_refs", MappingProxyType(dict(self.source_refs)))

    def __len__(self) -> int:
        return len(self.sections)

    def __iter__(self):
        return iter(self.sections)

    def get(self, section_key: str) -> SectionDesignPlan:
        """The section plan for ``section_key``.

        Raises:
            InvalidSectionPlanError: If no such section is in the plan.
        """
        for section in self.sections:
            if section.section_key == section_key:
                return section
        raise InvalidSectionPlanError(
            f"Section {section_key!r} not in plan.", details={"section": section_key}
        )

    @property
    def all_approved(self) -> bool:
        return bool(self.sections) and all(s.is_approved for s in self.sections)

    @property
    def overall_score(self) -> float:
        if not self.sections:
            return 0.0
        return round(sum(s.review_score for s in self.sections) / len(self.sections), 1)

    @property
    def ready_for_figma(self) -> bool:
        """Whether every section is approved — the plan is ready for Figma generation."""
        return self.all_approved

    def to_json(self) -> dict[str, object]:
        """Serialise the whole plan to a structured, JSON-safe dict."""
        return {
            "brand_name": self.brand_name,
            "project_id": self.project_id,
            "created_at": self.created_at,
            "source_refs": dict(self.source_refs),
            "overall_score": self.overall_score,
            "ready_for_figma": self.ready_for_figma,
            "figma_constraints": FIGMA_CONSTRAINTS.to_json(),
            "section_count": len(self.sections),
            "sections": [s.to_json() for s in self.sections],
        }

    def to_json_str(self, *, indent: int = 2) -> str:
        """Serialise the whole plan to a pretty JSON string."""
        return json.dumps(self.to_json(), indent=indent, ensure_ascii=False)
