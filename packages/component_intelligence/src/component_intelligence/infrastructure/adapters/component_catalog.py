"""The component knowledge base — the forty-one components, codified.

For each :class:`ComponentType` this encodes its intelligence: atomic level, page affinity, the
four purposes, its outcome effects (conversion/friction/trust) and quality impacts, its data,
dependencies, conflicts, variants, states, when to use and when *not* to use, and whether it is
a core inclusion or optional. This is the design judgement of a Shopify/Apple/Material-calibre
team expressed as data; the rule-based brain is a thin mapping over it that fills baseline
behaviour so every included component is fully specified.

Pure data over the shared value objects. No I/O, no framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.errors import DesignDirectorError

from component_intelligence.domain.shared.value_objects import (
    AtomicLevel,
    ComponentStateKind,
    ComponentType,
    DataKind,
    EffectLevel,
    ImpactLevel,
    InteractionKind,
    PageType,
)

__all__ = ["ComponentSpec", "all_specs", "spec_for"]

_C = ComponentType
_P = PageType
_A = AtomicLevel
_E = EffectLevel
_I = ImpactLevel
_D = DataKind
_K = InteractionKind
_S = ComponentStateKind


class UnknownComponentError(DesignDirectorError):
    """Raised when no spec exists for a component."""

    code = "component_intelligence_unknown_component"
    http_status = 422


@dataclass(frozen=True, slots=True)
class ComponentSpec:
    """The codified intelligence of one component."""

    component: ComponentType
    atomic: AtomicLevel
    pages: tuple[PageType, ...]
    business: str
    user: str
    conversion: str
    trust: str
    when_to_use: str
    when_not_to_use: str
    conversion_effect: EffectLevel = _E.NONE
    friction_effect: EffectLevel = _E.NONE
    trust_effect: EffectLevel = _E.NONE
    seo: ImpactLevel = _I.NEUTRAL
    accessibility: ImpactLevel = _I.POSITIVE
    performance: ImpactLevel = _I.NEUTRAL
    mobile: str = "Adapts gracefully to a single column on mobile."
    data: tuple[DataKind, ...] = ()
    dependencies: tuple[ComponentType, ...] = ()
    conflicts: tuple[ComponentType, ...] = ()
    interactions: tuple[InteractionKind, ...] = (_K.CLICK,)
    variants: tuple[str, ...] = ("default",)
    states: tuple[ComponentStateKind, ...] = (_S.DEFAULT,)
    priority: int = 3
    optional: bool = False
    tokens: tuple[str, ...] = field(default_factory=lambda: ("color.surface", "spacing.base"))


_ALL = tuple(_P)
_NAV_PAGES = tuple(p for p in _P)
_LISTING = (_P.COLLECTION, _P.SEARCH)


_SPECS: tuple[ComponentSpec, ...] = (
    ComponentSpec(_C.ANNOUNCEMENT_BAR, _A.ATOM, _ALL,
        "Promote offers and shipping thresholds.", "Learn of current offers.",
        "Nudge shoppers toward qualifying purchases.", "Signal an active, trustworthy store.",
        "Use for a single, current, high-value message.", "Never stack multiple messages or use during checkout.",
        conversion_effect=_E.SLIGHT, trust_effect=_E.SLIGHT, data=(_D.CONTENT,), priority=2),
    ComponentSpec(_C.HEADER, _A.ORGANISM, _ALL,
        "Anchor the brand and primary navigation.", "Orient and navigate from anywhere.",
        "Keep the cart and search one tap away.", "Present a coherent, professional storefront.",
        "Always — it frames every page.", "Never omit; never overload with links.",
        friction_effect=_E.MODERATE, seo=_I.POSITIVE, data=(_D.NAVIGATION,), priority=5,
        interactions=(_K.CLICK, _K.HOVER)),
    ComponentSpec(_C.MEGA_MENU, _A.ORGANISM, (_P.HOMEPAGE, _P.COLLECTION, _P.PRODUCT, _P.SEARCH),
        "Expose the catalog taxonomy for large ranges.", "Browse categories without leaving the page.",
        "Route shoppers to high-intent collections.", "Show catalog breadth and organisation.",
        "Use for large catalogs on desktop.", "Never on small catalogs or on mobile — collapse to navigation.",
        friction_effect=_E.MODERATE, data=(_D.NAVIGATION,), dependencies=(_C.HEADER,), priority=3,
        interactions=(_K.HOVER, _K.CLICK), tokens=("color.surface", "spacing.base", "elevation.1")),
    ComponentSpec(_C.NAVIGATION, _A.ORGANISM, _ALL,
        "Provide baseline wayfinding.", "Reach any section reliably.",
        "Keep products reachable in few taps.", "Signal a well-structured store.",
        "Always as the base navigation.", "Never bury primary categories.",
        friction_effect=_E.MODERATE, data=(_D.NAVIGATION,), dependencies=(_C.HEADER,), priority=4,
        interactions=(_K.CLICK, _K.DRAWER_TOGGLE)),
    ComponentSpec(_C.BREADCRUMBS, _A.MOLECULE, (_P.COLLECTION, _P.PRODUCT, _P.SEARCH, _P.BLOG),
        "Reduce bounce with legible hierarchy.", "Understand location and step back up.",
        "Keep shoppers browsing rather than leaving.", "Convey a well-organised catalog.",
        "Use on deep hierarchies (collection, product).", "Never on the homepage or flat structures.",
        friction_effect=_E.SLIGHT, seo=_I.POSITIVE, data=(_D.NAVIGATION,), priority=3),
    ComponentSpec(_C.HERO, _A.ORGANISM, (_P.HOMEPAGE, _P.LANDING, _P.COLLECTION),
        "Lead with the core value proposition.", "Understand what the store offers.",
        "Drive entry into the catalog.", "Convey brand quality at first glance.",
        "Use a single, focused hero above the fold.", "Never pair with a hero carousel in the same slot.",
        conversion_effect=_E.MODERATE, data=(_D.CONTENT, _D.MEDIA), conflicts=(_C.HERO_CAROUSEL,),
        priority=4, variants=("image", "video", "split"), tokens=("color.surface", "spacing.base", "type.display")),
    ComponentSpec(_C.HERO_CAROUSEL, _A.ORGANISM, (_P.HOMEPAGE, _P.LANDING),
        "Rotate multiple campaigns.", "Preview several offers.",
        "Surface more than one campaign.", "Show an active, curated store.",
        "Use only when multiple equal-priority campaigns must share the slot.",
        "Never when a single message converts better — prefer a static hero.",
        conversion_effect=_E.SLIGHT, performance=_I.NEGATIVE, data=(_D.CONTENT, _D.MEDIA),
        conflicts=(_C.HERO,), interactions=(_K.SWIPE, _K.CLICK), priority=2, optional=True,
        variants=("auto", "manual")),
    ComponentSpec(_C.CATEGORY_GRID, _A.ORGANISM, (_P.HOMEPAGE, _P.LANDING),
        "Distribute traffic across the catalog.", "Jump to the category I want.",
        "Route to high-intent collections.", "Demonstrate catalog breadth.",
        "Use to surface top collections on entry pages.", "Never as a substitute for real navigation.",
        conversion_effect=_E.SLIGHT, data=(_D.COLLECTION,), priority=3, variants=("tiles", "editorial")),
    ComponentSpec(_C.COLLECTION_GRID, _A.ORGANISM, (_P.HOMEPAGE, _P.COLLECTION),
        "Merchandise curated collections.", "Explore grouped products.",
        "Drive product visits from curation.", "Show a considered assortment.",
        "Use for curated, editorial groupings.", "Never for the full catalog — use a product grid.",
        conversion_effect=_E.MODERATE, data=(_D.COLLECTION, _D.PRODUCT_LIST),
        dependencies=(_C.PRODUCT_CARD,), priority=3),
    ComponentSpec(_C.PRODUCT_GRID, _A.ORGANISM, _LISTING,
        "Convert browsing into product visits.", "Scan products and pick some to inspect.",
        "Move shoppers to product pages efficiently.", "Show accurate prices and availability.",
        "Use on collection and search results.", "Never without pagination on large result sets.",
        conversion_effect=_E.MODERATE, data=(_D.PRODUCT_LIST, _D.PRICE, _D.INVENTORY),
        dependencies=(_C.PRODUCT_CARD,), priority=5, interactions=(_K.CLICK, _K.PAGINATE)),
    ComponentSpec(_C.PRODUCT_CARD, _A.MOLECULE, (_P.HOMEPAGE, _P.COLLECTION, _P.SEARCH, _P.PRODUCT),
        "Represent a product for entry.", "Assess a product at a glance.",
        "Drive product detail visits.", "Show honest price and imagery.",
        "Use in every product grid and carousel.", "Never overload with more than the key facts.",
        conversion_effect=_E.MODERATE, data=(_D.PRODUCT, _D.PRICE), priority=4,
        variants=("compact", "detailed"), states=(_S.DEFAULT, _S.HOVER, _S.LOADING),
        tokens=("color.surface", "spacing.base", "radius.1")),
    ComponentSpec(_C.PRODUCT_GALLERY, _A.ORGANISM, (_P.PRODUCT,),
        "Reduce uncertainty that suppresses purchase.", "See exactly what I would receive.",
        "Build confidence toward add-to-cart.", "Represent the product honestly.",
        "Use on every product page.", "Never with low-resolution or missing imagery.",
        conversion_effect=_E.MODERATE, trust_effect=_E.MODERATE, data=(_D.PRODUCT, _D.MEDIA),
        interactions=(_K.ZOOM, _K.SWIPE), priority=5, variants=("stacked", "thumbnails")),
    ComponentSpec(_C.PRODUCT_INFORMATION, _A.ORGANISM, (_P.PRODUCT,),
        "Convert interest into intent.", "Understand the product's features and fit.",
        "Advance shoppers toward the buy decision.", "Provide accurate, complete information.",
        "Use on every product page.", "Never omit the essentials (title, description, key attributes).",
        conversion_effect=_E.MODERATE, seo=_I.STRONG_POSITIVE, data=(_D.PRODUCT,), priority=5),
    ComponentSpec(_C.VARIANT_PICKER, _A.MOLECULE, (_P.PRODUCT,),
        "Enable accurate, purchasable selections.", "Pick my size, colour, or option.",
        "Unblock add-to-cart with a valid selection.", "Show real availability per variant.",
        "Use whenever a product has variants.", "Never for single-variant products.",
        conversion_effect=_E.STRONG, friction_effect=_E.MODERATE, data=(_D.PRODUCT, _D.INVENTORY),
        dependencies=(_C.PRODUCT_INFORMATION,), interactions=(_K.CLICK,),
        priority=4, states=(_S.DEFAULT, _S.ACTIVE, _S.DISABLED)),
    ComponentSpec(_C.STICKY_ADD_TO_CART, _A.ORGANISM, (_P.PRODUCT,),
        "Capture the purchase decision anywhere on the page.", "Add to cart without scrolling back.",
        "Drive the primary conversion on mobile.", "Keep price and stock transparent.",
        "Use on mobile once the buy box scrolls away.", "Never when it obscures critical content.",
        conversion_effect=_E.STRONG, friction_effect=_E.MODERATE, data=(_D.PRODUCT, _D.PRICE),
        dependencies=(_C.VARIANT_PICKER, _C.PRODUCT_INFORMATION),
        interactions=(_K.ADD_TO_CART,), priority=5, mobile="Pins to the bottom of the viewport on mobile."),
    ComponentSpec(_C.SIZE_GUIDE, _A.MOLECULE, (_P.PRODUCT,),
        "Reduce sizing-driven returns.", "Choose the right size with confidence.",
        "Prevent abandonment from sizing doubt.", "Show honest, detailed sizing.",
        "Use for apparel and fit-sensitive products.", "Never for products without meaningful sizing.",
        friction_effect=_E.MODERATE, trust_effect=_E.SLIGHT, data=(_D.CONTENT,),
        interactions=(_K.EXPAND_COLLAPSE,), priority=2, optional=True, states=(_S.DEFAULT, _S.EMPTY)),
    ComponentSpec(_C.DELIVERY_WIDGET, _A.MOLECULE, (_P.PRODUCT, _P.CART),
        "Prevent shipping surprises that cause abandonment.", "Know delivery cost and timing early.",
        "Keep shoppers moving to checkout.", "Show accurate, honest delivery info.",
        "Use near the buy box and cart summary.", "Never with vague or misleading estimates.",
        friction_effect=_E.MODERATE, trust_effect=_E.MODERATE, data=(_D.INVENTORY,), priority=3),
    ComponentSpec(_C.TRUST_BADGES, _A.MOLECULE, (_P.PRODUCT, _P.CART, _P.CHECKOUT),
        "Remove trust objections that suppress conversion.", "Feel safe buying.",
        "Reduce hesitation at the point of decision.", "Surface guarantees and security.",
        "Use near the buy box, cart, and payment.", "Never as decoration divorced from real policy.",
        conversion_effect=_E.MODERATE, trust_effect=_E.STRONG, data=(_D.CONTENT,), priority=4),
    ComponentSpec(_C.USP_GRID, _A.MOLECULE, (_P.HOMEPAGE, _P.LANDING, _P.PRODUCT),
        "Convert positioning into reasons to buy.", "Learn why this store is worth it.",
        "Increase propensity to browse and buy.", "Substantiate the value claims.",
        "Use to state three or fewer differentiators.", "Never as a long, unfocused list.",
        conversion_effect=_E.SLIGHT, trust_effect=_E.MODERATE, data=(_D.CONTENT,), priority=3),
    ComponentSpec(_C.TESTIMONIALS, _A.ORGANISM, (_P.HOMEPAGE, _P.LANDING),
        "Lift conversion through social proof.", "See that others trust the store.",
        "Reduce first-visit skepticism.", "Provide authentic third-party validation.",
        "Use with genuine, attributable testimonials.", "Never with fabricated or anonymous quotes.",
        conversion_effect=_E.SLIGHT, trust_effect=_E.MODERATE, data=(_D.REVIEW,), priority=3),
    ComponentSpec(_C.REVIEWS, _A.ORGANISM, (_P.PRODUCT,),
        "Lift conversion through peer validation.", "See what real buyers think.",
        "Reduce risk perception before buying.", "Show authentic, attributable reviews.",
        "Use on every product page.", "Never suppress or fabricate reviews.",
        conversion_effect=_E.MODERATE, trust_effect=_E.STRONG, seo=_I.POSITIVE,
        data=(_D.REVIEW, _D.RATING), interactions=(_K.PAGINATE,), priority=4),
    ComponentSpec(_C.FAQ, _A.ORGANISM, (_P.PRODUCT, _P.LANDING),
        "Recover conversions lost to unanswered questions.", "Get my blocking questions answered.",
        "Clear objections adjacent to the decision.", "Answer honestly and completely.",
        "Use to address the top blocking objections.", "Never to bury critical information.",
        friction_effect=_E.MODERATE, trust_effect=_E.SLIGHT, seo=_I.POSITIVE, data=(_D.CONTENT,),
        interactions=(_K.EXPAND_COLLAPSE,), priority=3),
    ComponentSpec(_C.COMPARISON_TABLE, _A.ORGANISM, (_P.PRODUCT, _P.COLLECTION),
        "Help shoppers choose between options.", "Compare products side by side.",
        "Prevent decision paralysis.", "Show honest, complete comparisons.",
        "Use when shoppers weigh similar products.", "Never for a single product or trivial differences.",
        friction_effect=_E.MODERATE, conversion_effect=_E.SLIGHT, data=(_D.PRODUCT_LIST,),
        priority=2, optional=True),
    ComponentSpec(_C.RECENTLY_VIEWED, _A.MOLECULE, (_P.PRODUCT, _P.HOMEPAGE),
        "Re-engage returning shoppers.", "Return to products I looked at.",
        "Recover interrupted browsing sessions.", "Respect the shopper's history.",
        "Use to resurface recent product views.", "Never for first-time visitors with no history.",
        conversion_effect=_E.MODERATE, data=(_D.PRODUCT_LIST,), priority=2, optional=True),
    ComponentSpec(_C.RELATED_PRODUCTS, _A.ORGANISM, (_P.PRODUCT,),
        "Rescue non-fits and expand discovery.", "Find alternatives that suit me better.",
        "Keep shoppers on the path to purchase.", "Recommend genuinely relevant products.",
        "Use on product pages to offer alternatives.", "Never with irrelevant filler.",
        conversion_effect=_E.MODERATE, data=(_D.RECOMMENDATION,), dependencies=(_C.PRODUCT_CARD,),
        priority=3),
    ComponentSpec(_C.RECOMMENDATIONS, _A.ORGANISM, (_P.HOMEPAGE, _P.PRODUCT, _P.CART),
        "Increase AOV via cross-sell and upsell.", "Discover products worth considering.",
        "Expand the basket and rescue non-fits.", "Recommend relevant, in-stock products.",
        "Use where complementary products add value.", "Never as generic, untargeted filler.",
        conversion_effect=_E.MODERATE, data=(_D.RECOMMENDATION,), dependencies=(_C.PRODUCT_CARD,),
        priority=3),
    ComponentSpec(_C.BUNDLE_BUILDER, _A.ORGANISM, (_P.PRODUCT,),
        "Raise average order value with bundles.", "Build a complete set easily.",
        "Increase basket size at the decision point.", "Show honest bundle savings.",
        "Use when products are naturally bought together.", "Never force unrelated bundles.",
        conversion_effect=_E.STRONG, data=(_D.PRODUCT_LIST, _D.PRICE), dependencies=(_C.PRODUCT_CARD,),
        interactions=(_K.CLICK, _K.ADD_TO_CART), priority=2, optional=True),
    ComponentSpec(_C.CART_DRAWER, _A.ORGANISM, (_P.PRODUCT, _P.COLLECTION, _P.HOMEPAGE),
        "Keep shoppers in flow after add-to-cart.", "Review the cart without leaving the page.",
        "Reduce drop-off between add-to-cart and checkout.", "Confirm the basket transparently.",
        "Use for in-context cart review on add.", "Never together with a mini-cart page — choose one.",
        conversion_effect=_E.MODERATE, friction_effect=_E.MODERATE, data=(_D.CART,),
        conflicts=(_C.MINI_CART,), dependencies=(_C.HEADER,), interactions=(_K.DRAWER_TOGGLE,),
        priority=4, mobile="Slides in from the edge as a full-height sheet on mobile."),
    ComponentSpec(_C.MINI_CART, _A.MOLECULE, (_P.PRODUCT, _P.COLLECTION, _P.HOMEPAGE),
        "Surface cart contents from the header.", "Peek at the cart quickly.",
        "Keep the path to checkout one tap away.", "Show accurate cart totals.",
        "Use for a lightweight header cart preview.", "Never together with a cart drawer — choose one.",
        conversion_effect=_E.MODERATE, friction_effect=_E.MODERATE, data=(_D.CART,),
        conflicts=(_C.CART_DRAWER,), dependencies=(_C.HEADER,), priority=3),
    ComponentSpec(_C.CHECKOUT_BLOCKS, _A.ORGANISM, (_P.CHECKOUT,),
        "Complete the purchase with minimal abandonment.", "Enter details and pay quickly.",
        "Minimise fields and friction to completion.", "Handle personal data securely.",
        "Use as the checkout backbone.", "Never add non-essential fields or distractions.",
        conversion_effect=_E.STRONG, friction_effect=_E.STRONG, data=(_D.ORDER, _D.CUSTOMER),
        dependencies=(_C.FORMS,), interactions=(_K.SUBMIT,), priority=5,
        states=(_S.DEFAULT, _S.LOADING, _S.ERROR, _S.SUCCESS)),
    ComponentSpec(_C.FOOTER, _A.ORGANISM, _ALL,
        "Capture end-of-page intent (support, policies, signup).", "Find support and policies.",
        "Offer secondary conversion paths.", "Surface policies and contact.",
        "Always — it closes every page.", "Never omit legal and policy links.",
        seo=_I.POSITIVE, data=(_D.NAVIGATION,), priority=2),
    ComponentSpec(_C.NEWSLETTER, _A.MOLECULE, (_P.HOMEPAGE, _P.LANDING, _P.BLOG),
        "Grow the marketable audience.", "Opt in to offers and updates.",
        "Convert anonymous visits into leads.", "Set clear expectations for communication.",
        "Use to capture email intent.", "Never with dark patterns or forced signup.",
        conversion_effect=_E.SLIGHT, data=(_D.CUSTOMER,), dependencies=(_C.FORMS,),
        interactions=(_K.SUBMIT,), priority=2),
    ComponentSpec(_C.BLOG_CARDS, _A.MOLECULE, (_P.BLOG, _P.HOMEPAGE),
        "Build authority and organic reach.", "Find relevant content.",
        "Route engaged readers toward products.", "Demonstrate expertise.",
        "Use to present articles for browsing.", "Never as filler on commerce-critical pages.",
        seo=_I.POSITIVE, data=(_D.CONTENT,), priority=2, optional=True),
    ComponentSpec(_C.FORMS, _A.MOLECULE, (_P.CHECKOUT, _P.ACCOUNT, _P.CMS),
        "Collect the data the store needs.", "Enter my details quickly and correctly.",
        "Minimise friction in data entry.", "Handle input securely and validate clearly.",
        "Use wherever structured input is required.", "Never request more than is necessary.",
        friction_effect=_E.MODERATE, accessibility=_I.STRONG_POSITIVE, data=(_D.CUSTOMER,),
        interactions=(_K.SUBMIT,), priority=4, states=(_S.DEFAULT, _S.ERROR, _S.SUCCESS, _S.DISABLED)),
    ComponentSpec(_C.SEARCH, _A.MOLECULE, (_P.HOMEPAGE, _P.COLLECTION, _P.SEARCH, _P.PRODUCT),
        "Turn intent-rich queries into product visits.", "Find exactly what I'm looking for.",
        "Route high-intent shoppers to products fast.", "Show a capable, forgiving search.",
        "Use for catalogs where shoppers arrive with intent.", "Never hide search on large catalogs.",
        conversion_effect=_E.MODERATE, friction_effect=_E.STRONG, data=(_D.SEARCH_RESULT,),
        interactions=(_K.AUTOCOMPLETE, _K.SUBMIT), priority=4),
    ComponentSpec(_C.FILTERS, _A.ORGANISM, _LISTING,
        "Improve findability within results.", "Narrow results to my needs.",
        "Move qualified shoppers to product pages.", "Show organised, controllable results.",
        "Use on large or faceted result sets.", "Never on small result sets where they add friction.",
        friction_effect=_E.STRONG, conversion_effect=_E.MODERATE, data=(_D.FACET,),
        interactions=(_K.FILTER,), priority=4),
    ComponentSpec(_C.SORTING, _A.MOLECULE, _LISTING,
        "Surface the most compelling products first.", "Order results the way I shop.",
        "Bring high-intent products to the top.", "Give control over the view.",
        "Use alongside product grids.", "Never as the only way to narrow a large set — pair with filters.",
        friction_effect=_E.MODERATE, data=(_D.PRODUCT_LIST,), interactions=(_K.SORT,), priority=3),
    ComponentSpec(_C.PAGINATION, _A.ATOM, _LISTING,
        "Manage large result sets performantly.", "Move through results predictably.",
        "Keep results fast and navigable.", "Present a controllable result set.",
        "Use for large result sets.", "Never for short lists where it adds friction.",
        friction_effect=_E.SLIGHT, performance=_I.POSITIVE, data=(_D.PRODUCT_LIST,),
        interactions=(_K.PAGINATE, _K.INFINITE_SCROLL), priority=3),
    ComponentSpec(_C.WISHLIST, _A.MOLECULE, (_P.PRODUCT, _P.ACCOUNT, _P.COLLECTION),
        "Capture future intent and re-engagement.", "Save products for later.",
        "Recover deferred purchases.", "Respect the shopper's saved intent.",
        "Use to let shoppers save products.", "Never when it distracts from immediate conversion.",
        conversion_effect=_E.SLIGHT, data=(_D.PRODUCT_LIST,), priority=2, optional=True),
    ComponentSpec(_C.ACCOUNT, _A.ORGANISM, (_P.ACCOUNT,),
        "Increase retention through self-service.", "Manage my orders and details.",
        "Enable reorders and account-driven purchases.", "Signal secure, in-control management.",
        "Use as the account backbone.", "Never expose account areas without authentication.",
        data=(_D.CUSTOMER,), dependencies=(_C.FORMS,), priority=4),
    ComponentSpec(_C.ORDER_TIMELINE, _A.ORGANISM, (_P.ACCOUNT, _P.CHECKOUT),
        "Reduce post-purchase support load.", "Track my order's progress.",
        "Reassure after purchase to drive repeat.", "Show accurate, honest order status.",
        "Use to communicate order and fulfilment status.", "Never with stale or inaccurate status.",
        trust_effect=_E.MODERATE, data=(_D.ORDER,), priority=3),
)

_BY_COMPONENT: dict[ComponentType, ComponentSpec] = {s.component: s for s in _SPECS}


def spec_for(component: ComponentType) -> ComponentSpec:
    """Return the codified spec for a component."""
    spec = _BY_COMPONENT.get(component)
    if spec is None:
        raise UnknownComponentError(
            f"No spec for component {component.value}.", details={"component": component.value}
        )
    return spec


def all_specs() -> tuple[ComponentSpec, ...]:
    """Return every codified component spec."""
    return _SPECS
