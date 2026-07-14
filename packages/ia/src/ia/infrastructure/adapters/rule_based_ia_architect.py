"""RuleBasedIAArchitect — the deterministic default implementation of the architect.

This adapter implements :class:`IASynthesisPort` with explicit, explainable heuristics rather
than an LLM: it derives the site map (page blueprints with sections, goals, priorities,
actions), the navigation, the page relationships, and the product discovery from a
codification of Shopify / Adobe Commerce IA practice (the page specs) and the consolidated
evidence, citing real evidence ids for each decision. It is fully deterministic (same input +
evidence ⇒ same draft), dependency-free, and honest — it invents no facts; it *structures* the
experience over the evidence it is given and grounds each decision by citing it.

In production this port is swapped for a reasoning/LLM-backed architect; the contract (propose
grounded content, citing only supplied evidence) is unchanged, so the engine's integrity
guarantees hold regardless of which brain is plugged in.
"""

from __future__ import annotations

from collections.abc import Sequence

from ia.application.contracts import IADraft, IAInput
from ia.domain.context.context import IABrief
from ia.domain.discovery.discovery import (
    Discovery,
    FilteringStrategy,
    SearchStrategy,
    SortingStrategy,
)
from ia.domain.evidence.evidence import EvidenceGraph, IAEvidence
from ia.domain.navigation.nav_item import NavItem
from ia.domain.navigation.navigation import (
    Breadcrumbs,
    Footer,
    GlobalNavigation,
    MegaMenu,
    Navigation,
)
from ia.domain.page.action import PageAction
from ia.domain.page.goals import PageGoals
from ia.domain.page.page_blueprint import PageBlueprint
from ia.domain.page.priorities import PagePriorities
from ia.domain.relationship.relationship import (
    InternalLinkingStrategy,
    PageRelationship,
    RelationshipSet,
)
from ia.domain.section.section import ContentBlock, Section
from ia.domain.shared.ids import (
    ContentBlockId,
    IAEvidenceId,
    NavItemId,
    PageActionId,
    PageBlueprintId,
    PageRelationshipId,
    SectionId,
)
from ia.domain.shared.value_objects import (
    ActionType,
    FilterType,
    PageType,
    Priority,
    ProvenanceKind,
    RelationshipKind,
    SortOption,
)
from ia.domain.sitemap.sitemap import SiteMap
from ia.infrastructure.adapters.page_specs import PageSpec, spec_for

__all__ = ["RuleBasedIAArchitect"]


class RuleBasedIAArchitect:
    """A deterministic, evidence-grounded implementation of the IA-architect port."""

    async def draft(self, ia_input: IAInput, evidence: EvidenceGraph) -> IADraft:
        ranked = sorted(evidence, key=lambda e: e.confidence.value, reverse=True)
        brief = ia_input.brief
        present = set(brief.pages)
        sitemap = self._sitemap(brief, ranked)
        return IADraft(
            sitemap=sitemap,
            navigation=self._navigation(present, brief, ranked),
            relationships=self._relationships(present, ranked),
            discovery=self._discovery(ranked),
        )

    # ------------------------------------------------------------------ #
    @staticmethod
    def _cite(
        ranked: Sequence[IAEvidence], keywords: Sequence[str], limit: int = 2
    ) -> tuple[IAEvidenceId, ...]:
        if not ranked:
            return ()
        kws = [k.lower() for k in keywords]
        matched = [
            e
            for e in ranked
            if any(
                k in f"{e.claim} {e.statement} {' '.join(t.value for t in e.tags)}".lower()
                for k in kws
            )
        ]
        chosen = matched[:limit] or ranked[:1]
        return tuple(e.id for e in chosen)

    @staticmethod
    def _cite_prefer(
        ranked: Sequence[IAEvidence],
        provenance: ProvenanceKind,
        keywords: Sequence[str],
        limit: int = 2,
    ) -> tuple[IAEvidenceId, ...]:
        """Cite the given keywords, grounding the decision in ``provenance`` first.

        Trust/conversion decisions are grounded in Psychology and page goals in Business
        Strategy, so the architecture cites the source that actually justifies the decision
        rather than whichever evidence merely ranks highest by confidence.
        """
        if not ranked:
            return ()
        kws = [k.lower() for k in keywords]

        def matches(e: IAEvidence) -> bool:
            hay = f"{e.claim} {e.statement} {' '.join(t.value for t in e.tags)}".lower()
            return any(k in hay for k in kws)

        preferred = [e for e in ranked if e.provenance is provenance and matches(e)]
        others = [e for e in ranked if e.provenance is not provenance and matches(e)]
        chosen = (preferred + others)[:limit] or ranked[:1]
        return tuple(e.id for e in chosen)

    # ------------------------------------------------------------------ #
    def _sitemap(self, brief: IABrief, ranked: Sequence[IAEvidence]) -> SiteMap:
        page_types = list(brief.pages)
        # Honour the storefront's optional capabilities the brief declares.
        if brief.has_blog and PageType.BLOG not in page_types:
            page_types.append(PageType.BLOG)
        if brief.has_wishlist and PageType.WISHLIST not in page_types:
            page_types.append(PageType.WISHLIST)
        pages = [self._page(page_type, spec_for(page_type), ranked) for page_type in page_types]
        return SiteMap.of(pages)

    def _page(
        self, page_type: PageType, spec: PageSpec, ranked: Sequence[IAEvidence]
    ) -> PageBlueprint:
        cite = self._cite(ranked, (page_type.value, "page", "conversion", "trust"), 2)
        # Ground the page's goals in Business Strategy and its trust structure in Psychology,
        # so the blueprint cites the source that justifies each decision — not just the
        # highest-confidence structural evidence.
        goal_cite = self._cite_prefer(
            ranked, ProvenanceKind.BUSINESS_STRATEGY,
            ("business", "conversion", "aov", "revenue", "positioning", page_type.value), 2,
        )
        trust_cite = self._cite_prefer(
            ranked, ProvenanceKind.PSYCHOLOGY,
            ("trust", "review", "objection", "anxiety", "guarantee", "confidence"), 2,
        )
        page_cite = tuple(dict.fromkeys(cite + goal_cite + trust_cite))
        required, optional = [], []
        for s in spec.sections:
            section = Section(
                id=SectionId.new(), type=s.type, purpose=f"{s.type.value.replace('_', ' ')} section.",
                priority=Priority(s.priority), placement=s.placement, is_required=s.required,
                content_blocks=tuple(
                    ContentBlock(id=ContentBlockId.new(), kind=kind, label=label,
                                 priority=Priority(s.priority), evidence_ids=cite)
                    for kind, label in s.blocks
                ),
                evidence_ids=cite,
            )
            (required if s.required else optional).append(section)
        primary_actions = ()
        if spec.primary_action is not None:
            action, target = spec.primary_action
            primary_actions = (
                PageAction(id=PageActionId.new(), type=ActionType.PRIMARY, action=action,
                           target=target, placement=spec.conversion_placement, evidence_ids=cite),
            )
        secondary_actions = tuple(
            PageAction(id=PageActionId.new(), type=ActionType.SECONDARY, action=a, evidence_ids=cite)
            for a in spec.secondary_actions
        )
        nav, seo, a11y, conv, mob = spec.priorities
        return PageBlueprint(
            id=PageBlueprintId.new(), page_type=page_type, requirement=spec.requirement,
            purpose=spec.purpose, slug_intent=spec.slug,
            goals=PageGoals(business_goal=spec.business_goal, primary_user_goal=spec.primary_user_goal,
                            secondary_user_goal=spec.secondary_user_goal, evidence_ids=goal_cite),
            required_sections=tuple(required), optional_sections=tuple(optional),
            priorities=PagePriorities(navigation=Priority(nav), seo=Priority(seo),
                                      accessibility=Priority(a11y), conversion=Priority(conv),
                                      mobile=Priority(mob)),
            primary_actions=primary_actions, secondary_actions=secondary_actions,
            trust_placement=spec.trust_placement, conversion_placement=spec.conversion_placement,
            evidence_ids=page_cite,
        )

    # ------------------------------------------------------------------ #
    def _navigation(
        self, present: set[PageType], brief: IABrief, ranked: Sequence[IAEvidence]
    ) -> Navigation:
        cite = self._cite(ranked, ("navigation", "nav", "menu", "convention"), 2)

        def leaf(label: str, target: PageType | None) -> NavItem | None:
            if target is not None and target not in present:
                return None
            return NavItem.leaf(label, target, cite)

        global_items = [
            i for i in (
                leaf("Shop", PageType.COLLECTION), leaf("Search", PageType.SEARCH),
                leaf("Blog", PageType.BLOG), leaf("About", PageType.ABOUT),
            ) if i is not None
        ]
        footer_columns = []
        shop_children = [i for i in (leaf("Collections", PageType.COLLECTION),
                                     leaf("Search", PageType.SEARCH)) if i is not None]
        support_children = [i for i in (leaf("Contact", PageType.CONTACT),
                                        leaf("Account", PageType.ACCOUNT)) if i is not None]
        company_children = [i for i in (leaf("About", PageType.ABOUT),
                                        leaf("Blog", PageType.BLOG)) if i is not None]
        if shop_children:
            footer_columns.append(NavItem(id=NavItemId.new(), label_intent="Shop", children=tuple(shop_children), evidence_ids=cite))
        if support_children:
            footer_columns.append(NavItem(id=NavItemId.new(), label_intent="Support", children=tuple(support_children), evidence_ids=cite))
        if company_children:
            footer_columns.append(NavItem(id=NavItemId.new(), label_intent="Company", children=tuple(company_children), evidence_ids=cite))

        utility = [i for i in (
            leaf("Search", PageType.SEARCH), leaf("Account", PageType.ACCOUNT),
            leaf("Cart", PageType.CART), leaf("Wishlist", PageType.WISHLIST),
        ) if i is not None]

        mega = MegaMenu(enabled=brief.is_large_catalog,
                        columns=(tuple(shop_children) if brief.is_large_catalog else ()),
                        evidence_ids=cite if brief.is_large_catalog else ())
        breadcrumbs = Breadcrumbs(
            enabled=True, strategy="Derive from the category hierarchy.",
            shown_on=tuple(p for p in (PageType.COLLECTION, PageType.PRODUCT, PageType.SEARCH) if p in present),
            evidence_ids=cite,
        )
        return Navigation(
            global_nav=GlobalNavigation(items=tuple(global_items),
                                        principles=("match ecommerce conventions", "keep primary paths shallow"),
                                        evidence_ids=cite),
            mega_menu=mega, footer=Footer(columns=tuple(footer_columns), evidence_ids=cite),
            breadcrumbs=breadcrumbs, utility=tuple(utility),
        )

    # ------------------------------------------------------------------ #
    def _relationships(
        self, present: set[PageType], ranked: Sequence[IAEvidence]
    ) -> RelationshipSet:
        cite = self._cite(ranked, ("cross-sell", "upsell", "related", "recommend", "linking"), 2)
        specs: tuple[tuple[PageType, PageType, RelationshipKind], ...] = (
            (PageType.COLLECTION, PageType.PRODUCT, RelationshipKind.PARENT_CHILD),
            (PageType.HOMEPAGE, PageType.COLLECTION, RelationshipKind.INTERNAL_LINK),
            (PageType.PRODUCT, PageType.PRODUCT, RelationshipKind.CROSS_SELL),
            (PageType.PRODUCT, PageType.PRODUCT, RelationshipKind.UPSELL),
            (PageType.PRODUCT, PageType.PRODUCT, RelationshipKind.RELATED),
            (PageType.CART, PageType.PRODUCT, RelationshipKind.CROSS_SELL),
            (PageType.BLOG, PageType.PRODUCT, RelationshipKind.INTERNAL_LINK),
            (PageType.SEARCH, PageType.PRODUCT, RelationshipKind.INTERNAL_LINK),
        )
        relationships = [
            PageRelationship(
                id=PageRelationshipId.new(), source=s, target=t, kind=k,
                rationale=f"{k.value.replace('_', ' ')} from {s.value} to {t.value}.", evidence_ids=cite,
            )
            for s, t, k in specs
            if s in present and t in present
        ]
        linking = InternalLinkingStrategy(
            principles=("link collections and products bidirectionally", "surface related content from the blog"),
            hub_pages=tuple(p for p in (PageType.COLLECTION, PageType.HOMEPAGE, PageType.BLOG) if p in present),
            evidence_ids=cite,
        )
        return RelationshipSet.of(relationships, linking)

    # ------------------------------------------------------------------ #
    def _discovery(self, ranked: Sequence[IAEvidence]) -> Discovery:
        return Discovery(
            search=SearchStrategy(
                scope="products, collections, and content", autocomplete=True,
                no_results_handling="Show suggestions, popular products, and a refined-query prompt.",
                principles=("prominent, always-available search", "graceful no-results recovery"),
                evidence_ids=self._cite(ranked, ("search", "site-search", "autocomplete"), 2),
            ),
            filtering=FilteringStrategy(
                facets=(FilterType.CATEGORY, FilterType.PRICE, FilterType.BRAND,
                        FilterType.RATING, FilterType.AVAILABILITY),
                principles=("faceted navigation for large catalogs", "keep applied filters visible"),
                evidence_ids=self._cite(ranked, ("filter", "faceted", "facet"), 2),
            ),
            sorting=SortingStrategy(
                options=(SortOption.RELEVANCE, SortOption.PRICE_ASC, SortOption.PRICE_DESC,
                         SortOption.NEWEST, SortOption.BESTSELLING, SortOption.RATING),
                default=SortOption.RELEVANCE,
                evidence_ids=self._cite(ranked, ("sort", "sorting", "relevance"), 2),
            ),
        )
