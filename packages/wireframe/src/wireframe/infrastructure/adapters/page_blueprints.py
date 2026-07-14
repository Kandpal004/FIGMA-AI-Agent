"""The codified page/section blueprint knowledge base.

This is the deterministic planner's domain knowledge: for each of the ten supported page
types, the sections it contains and — per section — its type, priority, four goals, blocks,
required/optional components, data needs, key interactions, intra-page dependencies, and
approval gate. It encodes established Shopify/Adobe-Commerce ecommerce planning patterns
(NN/g, Baymard) as data, so the planner stays a thin, testable mapping over it.

Only *distinctive* fields live here; the planner adds baseline responsive, accessibility,
SEO, performance, success/failure criteria, and review-checklist requirements to every
section, keeping this knowledge base DRY while every produced section is fully specified.

Pure data + the shared value objects. No I/O, no framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.errors import DesignDirectorError

from wireframe.domain.shared.value_objects import (
    ApprovalGate,
    ApproverRole,
    BlockKind,
    ComponentKind,
    DataKind,
    InteractionKind,
    PageType,
    SectionType,
)

__all__ = ["BlockSpec", "ComponentSpec", "PageSpec", "SectionSpec", "spec_for"]


class UnknownPageTypeError(DesignDirectorError):
    """Raised when no blueprint exists for a page type."""

    code = "wireframe_unknown_page_type"
    http_status = 422


@dataclass(frozen=True, slots=True)
class BlockSpec:
    """A block a section must lay out."""

    kind: BlockKind
    label: str
    data_kinds: tuple[DataKind, ...] = ()
    required: bool = True
    priority: int = 3


@dataclass(frozen=True, slots=True)
class ComponentSpec:
    """A component a section requires or may optionally carry."""

    component: ComponentKind
    required: bool = True
    rationale: str = ""
    fields: tuple[str, ...] = ()
    cardinality: str = "one"
    data_kind: DataKind | None = None
    depends_on: tuple[ComponentKind, ...] = ()


@dataclass(frozen=True, slots=True)
class SectionSpec:
    """A section within a page blueprint."""

    type: SectionType
    purpose: str
    business_goal: str
    user_goal: str
    conversion_goal: str = ""
    trust_goal: str = ""
    required: bool = True
    priority: int = 3
    blocks: tuple[BlockSpec, ...] = ()
    required_components: tuple[ComponentSpec, ...] = ()
    optional_components: tuple[ComponentSpec, ...] = ()
    data: tuple[tuple[DataKind, str], ...] = ()
    interactions: tuple[tuple[InteractionKind, str], ...] = ()
    depends_on: tuple[SectionType, ...] = ()
    success: tuple[str, ...] = ()
    checklist: tuple[str, ...] = ()
    gate: ApprovalGate = ApprovalGate.DESIGN_REVIEW
    approver: ApproverRole = ApproverRole.DESIGNER
    approval_criteria: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PageSpec:
    """A page and the sections that make up its wireframe plan."""

    page_type: PageType
    purpose: str
    sections: tuple[SectionSpec, ...] = field(default_factory=tuple)


# --------------------------------------------------------------------------- #
# Reusable section specs                                                       #
# --------------------------------------------------------------------------- #
def _global_nav() -> SectionSpec:
    return SectionSpec(
        type=SectionType.GLOBAL_NAV,
        purpose="Provide persistent, wayfinding navigation across the store.",
        business_goal="Keep every category and utility reachable to sustain browsing.",
        user_goal="Move confidently to any part of the store from anywhere.",
        conversion_goal="Route shoppers toward products and the cart with minimal friction.",
        trust_goal="Signal a coherent, professional storefront.",
        priority=5,
        blocks=(
            BlockSpec(BlockKind.NAV, "Primary navigation menu", (DataKind.NAVIGATION,), priority=5),
            BlockSpec(BlockKind.CTA, "Cart and account utilities", priority=4),
        ),
        required_components=(
            ComponentSpec(ComponentKind.NAV_MENU, rationale="Expose the category taxonomy.",
                          fields=("label", "url", "children"), cardinality="many",
                          data_kind=DataKind.NAVIGATION),
        ),
        data=((DataKind.NAVIGATION, "The site navigation taxonomy from the IA."),),
        interactions=((InteractionKind.HOVER, "Reveal mega-menu categories."),
                      (InteractionKind.CLICK, "Navigate to a category or utility.")),
        success=("Every top-level category from the IA is reachable in one interaction.",),
        checklist=("Navigation labels match the IA taxonomy.",),
    )


def _footer() -> SectionSpec:
    return SectionSpec(
        type=SectionType.FOOTER,
        purpose="Provide secondary navigation, trust, and legal information site-wide.",
        business_goal="Capture intent that reaches the page bottom (support, policies, signup).",
        user_goal="Find support, policies, and secondary links after the main content.",
        conversion_goal="Offer newsletter signup and secondary conversion paths.",
        trust_goal="Surface policies, guarantees, and contact to reassure shoppers.",
        priority=2,
        depends_on=(SectionType.GLOBAL_NAV,),
        blocks=(
            BlockSpec(BlockKind.FOOTER, "Footer link columns", (DataKind.NAVIGATION,), priority=3),
            BlockSpec(BlockKind.TRUST, "Policy and guarantee links", priority=2),
            BlockSpec(BlockKind.FORM, "Newsletter signup", required=False, priority=2),
        ),
        required_components=(
            ComponentSpec(ComponentKind.FOOTER_COLUMNS, rationale="Group secondary links.",
                          fields=("heading", "links"), cardinality="many",
                          data_kind=DataKind.NAVIGATION),
        ),
        optional_components=(
            ComponentSpec(ComponentKind.NEWSLETTER_FORM, required=False,
                          rationale="Capture email intent at page bottom.",
                          fields=("email",)),
        ),
        success=("Policy, support, and contact links are present and grouped.",),
        checklist=("Legal and policy links are complete.",),
    )


def _breadcrumbs(parent: SectionType = SectionType.GLOBAL_NAV) -> SectionSpec:
    return SectionSpec(
        type=SectionType.BREADCRUMBS,
        purpose="Show the shopper's location in the catalog hierarchy.",
        business_goal="Reduce bounce by making the hierarchy legible and backtrackable.",
        user_goal="Understand where I am and step back up the hierarchy.",
        conversion_goal="Keep shoppers browsing rather than leaving.",
        trust_goal="Convey a well-structured, trustworthy catalog.",
        priority=3,
        depends_on=(parent,),
        blocks=(BlockSpec(BlockKind.BREADCRUMB, "Breadcrumb trail", (DataKind.NAVIGATION,), priority=3),),
        required_components=(
            ComponentSpec(ComponentKind.BREADCRUMB, rationale="Render the hierarchy trail.",
                          fields=("label", "url"), cardinality="many",
                          data_kind=DataKind.NAVIGATION),
        ),
        success=("The trail reflects the true catalog path to the current page.",),
        checklist=("Breadcrumb path matches the IA hierarchy.",),
    )


# --------------------------------------------------------------------------- #
# Page blueprints                                                              #
# --------------------------------------------------------------------------- #
def _homepage() -> PageSpec:
    return PageSpec(
        page_type=PageType.HOMEPAGE,
        purpose="Orient first-time and returning shoppers and route them into the catalog.",
        sections=(
            _global_nav(),
            SectionSpec(
                type=SectionType.HERO,
                purpose="Communicate the core value proposition and route to the catalog.",
                business_goal="Establish positioning and drive entry into shopping.",
                user_goal="Understand what the store offers and where to start.",
                conversion_goal="Drive clicks into collections or featured products.",
                trust_goal="Convey brand quality in the first impression.",
                priority=5, depends_on=(SectionType.GLOBAL_NAV,),
                blocks=(
                    BlockSpec(BlockKind.HERO, "Hero headline and message", priority=5),
                    BlockSpec(BlockKind.MEDIA, "Hero imagery", priority=4),
                    BlockSpec(BlockKind.CTA, "Primary shop CTA", priority=5),
                ),
                required_components=(
                    ComponentSpec(ComponentKind.HERO_BANNER, rationale="Lead with the value message.",
                                  fields=("headline", "subhead", "cta")),
                ),
                interactions=((InteractionKind.CLICK, "Enter the catalog via the hero CTA."),),
                gate=ApprovalGate.DESIGN_DIRECTOR, approver=ApproverRole.DESIGN_DIRECTOR,
                approval_criteria=("Hero message aligns with brand and business positioning.",),
                success=("The primary CTA leads into the catalog above the fold.",),
                checklist=("Hero headline reflects the approved positioning.",),
            ),
            SectionSpec(
                type=SectionType.VALUE_PROPOSITION,
                purpose="Explain the differentiators that justify buying here.",
                business_goal="Convert positioning into a reason to shop.",
                user_goal="Learn why this store is worth my attention.",
                conversion_goal="Increase propensity to browse and buy.",
                trust_goal="Substantiate claims that build confidence.",
                priority=4, depends_on=(SectionType.HERO,),
                blocks=(
                    BlockSpec(BlockKind.CONTENT, "Value proposition points", priority=4),
                    BlockSpec(BlockKind.TRUST, "Supporting proof points", priority=3),
                ),
                required_components=(
                    ComponentSpec(ComponentKind.CONTENT_BLOCK, rationale="Present the differentiators.",
                                  fields=("heading", "body")),
                ),
                success=("Three or fewer differentiators are stated clearly.",),
                checklist=("Value claims are backed by evidence.",),
            ),
            SectionSpec(
                type=SectionType.FEATURED_PRODUCTS,
                purpose="Surface curated products to seed discovery.",
                business_goal="Drive product page visits and merchandising goals.",
                user_goal="See relevant products without searching.",
                conversion_goal="Generate product detail visits and add-to-cart intent.",
                trust_goal="Show real, in-stock products with prices.",
                priority=4, depends_on=(SectionType.VALUE_PROPOSITION,),
                blocks=(BlockSpec(BlockKind.PRODUCT, "Featured product cards",
                                  (DataKind.PRODUCT_LIST, DataKind.PRICE), priority=4),),
                required_components=(
                    ComponentSpec(ComponentKind.PRODUCT_CARD, rationale="Present products for entry.",
                                  fields=("title", "price", "image", "url"), cardinality="many",
                                  data_kind=DataKind.PRODUCT_LIST),
                ),
                data=((DataKind.PRODUCT_LIST, "Curated featured products."),
                      (DataKind.PRICE, "Current price per product.")),
                interactions=((InteractionKind.CLICK, "Open a product detail page."),),
                success=("Featured cards link to valid product pages with prices.",),
                checklist=("Featured products are in stock and priced.",),
            ),
            SectionSpec(
                type=SectionType.CATEGORY_GRID,
                purpose="Expose top collections for hierarchical browsing.",
                business_goal="Distribute traffic across the catalog.",
                user_goal="Jump straight to the category I care about.",
                conversion_goal="Route shoppers to high-intent collections.",
                trust_goal="Demonstrate catalog breadth.",
                required=False, priority=3, depends_on=(SectionType.GLOBAL_NAV,),
                blocks=(BlockSpec(BlockKind.CONTENT, "Category tiles", (DataKind.COLLECTION,), priority=3),),
                required_components=(
                    ComponentSpec(ComponentKind.CATEGORY_TILE, rationale="Link to top collections.",
                                  fields=("name", "image", "url"), cardinality="many",
                                  data_kind=DataKind.COLLECTION),
                ),
                success=("Each tile links to a valid collection.",),
            ),
            SectionSpec(
                type=SectionType.SOCIAL_PROOF,
                purpose="Reinforce credibility with reviews and social proof.",
                business_goal="Lift conversion by reducing first-visit skepticism.",
                user_goal="See that others trust and buy from this store.",
                conversion_goal="Reduce hesitation before browsing deeper.",
                trust_goal="Provide third-party validation.",
                required=False, priority=3, depends_on=(SectionType.FEATURED_PRODUCTS,),
                blocks=(BlockSpec(BlockKind.REVIEW, "Featured reviews or ratings",
                                  (DataKind.REVIEW, DataKind.RATING), required=False, priority=3),),
                optional_components=(
                    ComponentSpec(ComponentKind.REVIEW_SUMMARY, required=False,
                                  rationale="Summarize aggregate sentiment.",
                                  data_kind=DataKind.RATING),
                ),
                success=("Displayed proof is genuine and attributable.",),
            ),
            SectionSpec(
                type=SectionType.NEWSLETTER,
                purpose="Capture email intent from interested visitors.",
                business_goal="Grow the marketable audience.",
                user_goal="Opt in to offers and updates.",
                conversion_goal="Convert anonymous visits into contactable leads.",
                trust_goal="Set clear expectations for communication.",
                required=False, priority=2, depends_on=(SectionType.GLOBAL_NAV,),
                blocks=(BlockSpec(BlockKind.FORM, "Email signup", required=False, priority=2),),
                optional_components=(
                    ComponentSpec(ComponentKind.NEWSLETTER_FORM, required=False,
                                  rationale="Collect email opt-ins.", fields=("email",)),
                ),
                interactions=((InteractionKind.SUBMIT, "Submit the signup form."),
                              (InteractionKind.VALIDATE, "Validate the email inline.")),
                success=("The form validates input and confirms submission.",),
            ),
            _footer(),
        ),
    )


def _collection() -> PageSpec:
    return PageSpec(
        page_type=PageType.COLLECTION,
        purpose="Let shoppers browse, filter, and compare products within a category.",
        sections=(
            _global_nav(),
            _breadcrumbs(),
            SectionSpec(
                type=SectionType.FILTERS,
                purpose="Let shoppers narrow the catalog by facets.",
                business_goal="Help shoppers find relevant products faster.",
                user_goal="Narrow results to what matches my needs.",
                conversion_goal="Move qualified shoppers toward product pages.",
                trust_goal="Show a well-organized, controllable catalog.",
                priority=4, depends_on=(SectionType.BREADCRUMBS,),
                blocks=(BlockSpec(BlockKind.CONTENT, "Facet filters", (DataKind.FACET,), priority=4),),
                required_components=(
                    ComponentSpec(ComponentKind.SEARCH_FACETS, rationale="Enable faceted narrowing.",
                                  fields=("facet", "values"), cardinality="many",
                                  data_kind=DataKind.FACET),
                ),
                interactions=((InteractionKind.FILTER, "Apply and clear facets."),),
                success=("Applying a facet updates the results grid.",),
                checklist=("Facets reflect the collection's available attributes.",),
            ),
            SectionSpec(
                type=SectionType.SORT_BAR,
                purpose="Let shoppers reorder results by relevance, price, or recency.",
                business_goal="Surface high-margin or high-intent products first.",
                user_goal="Order results the way I shop.",
                conversion_goal="Bring the most compelling products to the top.",
                trust_goal="Give shoppers control over the view.",
                priority=3, depends_on=(SectionType.FILTERS,),
                blocks=(BlockSpec(BlockKind.CTA, "Sort selector", priority=3),),
                required_components=(
                    ComponentSpec(ComponentKind.SORT_DROPDOWN, rationale="Reorder the results grid.",
                                  fields=("option",)),
                ),
                interactions=((InteractionKind.SORT, "Change the sort order."),),
                success=("Changing the sort reorders the grid deterministically.",),
            ),
            SectionSpec(
                type=SectionType.RESULTS_GRID,
                purpose="Present the filtered, sorted products for selection.",
                business_goal="Drive product page visits and add-to-cart.",
                user_goal="Scan products and pick ones to inspect.",
                conversion_goal="Move shoppers to product pages efficiently.",
                trust_goal="Show accurate prices and availability.",
                priority=5, depends_on=(SectionType.SORT_BAR,),
                blocks=(BlockSpec(BlockKind.PRODUCT, "Product result cards",
                                  (DataKind.PRODUCT_LIST, DataKind.PRICE, DataKind.INVENTORY), priority=5),),
                required_components=(
                    ComponentSpec(ComponentKind.PRODUCT_CARD, rationale="Represent each result.",
                                  fields=("title", "price", "image", "url"), cardinality="many",
                                  data_kind=DataKind.PRODUCT_LIST),
                    ComponentSpec(ComponentKind.PAGINATION, rationale="Page through large result sets.",
                                  fields=("page", "total")),
                ),
                data=((DataKind.PRODUCT_LIST, "Products matching filters and sort."),
                      (DataKind.PRICE, "Price per product."),
                      (DataKind.INVENTORY, "Availability per product.")),
                interactions=((InteractionKind.CLICK, "Open a product page."),
                              (InteractionKind.PAGINATE, "Load the next page of results.")),
                success=("Every card links to a valid, in-stock-aware product page.",),
                checklist=("Grid respects the active filters and sort.",),
            ),
            _footer(),
        ),
    )


def _product() -> PageSpec:
    return PageSpec(
        page_type=PageType.PRODUCT,
        purpose="Give shoppers everything needed to confidently add the product to cart.",
        sections=(
            _global_nav(),
            _breadcrumbs(),
            SectionSpec(
                type=SectionType.PRODUCT_GALLERY,
                purpose="Show the product clearly from multiple angles.",
                business_goal="Reduce uncertainty that suppresses purchase.",
                user_goal="See exactly what I would receive.",
                conversion_goal="Build confidence toward add-to-cart.",
                trust_goal="Represent the product honestly.",
                priority=5, depends_on=(SectionType.BREADCRUMBS,),
                blocks=(BlockSpec(BlockKind.MEDIA, "Product image gallery", (DataKind.PRODUCT,), priority=5),),
                required_components=(
                    ComponentSpec(ComponentKind.PRODUCT_GALLERY, rationale="Show the product visually.",
                                  fields=("images", "alt"), cardinality="many",
                                  data_kind=DataKind.PRODUCT),
                ),
                interactions=((InteractionKind.ZOOM, "Zoom into product imagery."),
                              (InteractionKind.SWIPE, "Move between gallery images.")),
                success=("Gallery shows multiple angles with descriptive alt text.",),
            ),
            SectionSpec(
                type=SectionType.PRODUCT_INFO,
                purpose="Communicate what the product is and why it fits.",
                business_goal="Convert interest into intent with clear information.",
                user_goal="Understand the product's features and benefits.",
                conversion_goal="Advance shoppers toward the buy decision.",
                trust_goal="Provide accurate, complete product information.",
                priority=5, depends_on=(SectionType.PRODUCT_GALLERY,),
                blocks=(
                    BlockSpec(BlockKind.CONTENT, "Title and description", (DataKind.PRODUCT,), priority=5),
                    BlockSpec(BlockKind.PRODUCT, "Key attributes", (DataKind.PRODUCT,), priority=4),
                ),
                required_components=(
                    ComponentSpec(ComponentKind.CONTENT_BLOCK, rationale="Present title, description, attributes.",
                                  fields=("title", "description", "attributes"), data_kind=DataKind.PRODUCT),
                ),
                data=((DataKind.PRODUCT, "The product's core attributes and copy."),),
                success=("Title, description, and key attributes are present.",),
            ),
            SectionSpec(
                type=SectionType.VARIANT_SELECTOR,
                purpose="Let shoppers choose the variant they want.",
                business_goal="Enable accurate, purchasable selections.",
                user_goal="Pick my size, color, or option.",
                conversion_goal="Unblock add-to-cart with a valid selection.",
                trust_goal="Show real availability per variant.",
                priority=4, depends_on=(SectionType.PRODUCT_INFO,),
                blocks=(BlockSpec(BlockKind.PRODUCT, "Variant options",
                                  (DataKind.PRODUCT, DataKind.INVENTORY), priority=4),),
                required_components=(
                    ComponentSpec(ComponentKind.VARIANT_SELECTOR, rationale="Select a purchasable variant.",
                                  fields=("option", "value", "available"), cardinality="many",
                                  data_kind=DataKind.PRODUCT),
                ),
                interactions=((InteractionKind.CLICK, "Select a variant."),
                              (InteractionKind.VALIDATE, "Reflect availability of the chosen variant.")),
                success=("Selecting a variant updates price and availability.",),
            ),
            SectionSpec(
                type=SectionType.BUY_BOX,
                purpose="Present price and the primary add-to-cart action.",
                business_goal="Capture the purchase decision.",
                user_goal="Add the product to my cart.",
                conversion_goal="Drive the primary add-to-cart conversion.",
                trust_goal="Show transparent pricing and stock.",
                priority=5, depends_on=(SectionType.VARIANT_SELECTOR,),
                blocks=(
                    BlockSpec(BlockKind.PRODUCT, "Price display", (DataKind.PRICE,), priority=5),
                    BlockSpec(BlockKind.CTA, "Add to cart", priority=5),
                ),
                required_components=(
                    ComponentSpec(ComponentKind.PRICE, rationale="Show current price clearly.",
                                  fields=("amount", "currency"), data_kind=DataKind.PRICE),
                    ComponentSpec(ComponentKind.QUANTITY_SELECTOR, rationale="Choose quantity.",
                                  fields=("quantity",)),
                    ComponentSpec(ComponentKind.ADD_TO_CART, rationale="Primary conversion action.",
                                  fields=("variant", "quantity"),
                                  depends_on=(ComponentKind.VARIANT_SELECTOR, ComponentKind.PRICE)),
                ),
                data=((DataKind.PRICE, "Current price for the selected variant."),
                      (DataKind.INVENTORY, "Stock for the selected variant.")),
                interactions=((InteractionKind.ADD_TO_CART, "Add the selected variant to the cart."),),
                gate=ApprovalGate.DESIGN_DIRECTOR, approver=ApproverRole.DESIGN_DIRECTOR,
                approval_criteria=("Primary add-to-cart is unmistakable and above the fold.",),
                success=("Add-to-cart is the dominant action and reflects the selection.",),
                checklist=("Add-to-cart requires a valid variant and shows price.",),
            ),
            SectionSpec(
                type=SectionType.TRUST,
                purpose="Reassure shoppers at the point of decision.",
                business_goal="Remove trust objections that suppress conversion.",
                user_goal="Feel safe buying (returns, guarantees, shipping).",
                conversion_goal="Reduce hesitation immediately around the buy box.",
                trust_goal="Surface guarantees, returns, and secure-checkout signals.",
                priority=4, depends_on=(SectionType.BUY_BOX,),
                blocks=(BlockSpec(BlockKind.TRUST, "Guarantee and returns signals", priority=4),),
                required_components=(
                    ComponentSpec(ComponentKind.TRUST_BADGES, rationale="Address purchase anxiety.",
                                  fields=("label", "detail"), cardinality="many"),
                ),
                success=("Returns, guarantee, and shipping reassurance are visible near the CTA.",),
                checklist=("Trust claims are truthful and policy-backed.",),
            ),
            SectionSpec(
                type=SectionType.REVIEWS,
                purpose="Provide social proof from other buyers.",
                business_goal="Lift conversion through peer validation.",
                user_goal="See what real buyers think.",
                conversion_goal="Reduce risk perception before buying.",
                trust_goal="Show authentic, attributable reviews.",
                priority=4, depends_on=(SectionType.PRODUCT_INFO,),
                blocks=(BlockSpec(BlockKind.REVIEW, "Customer reviews",
                                  (DataKind.REVIEW, DataKind.RATING), priority=4),),
                required_components=(
                    ComponentSpec(ComponentKind.REVIEW_SUMMARY, rationale="Summarize sentiment.",
                                  fields=("average", "count"), data_kind=DataKind.RATING),
                    ComponentSpec(ComponentKind.REVIEW_LIST, rationale="Show individual reviews.",
                                  fields=("author", "rating", "body"), cardinality="many",
                                  data_kind=DataKind.REVIEW),
                ),
                data=((DataKind.REVIEW, "Individual customer reviews."),
                      (DataKind.RATING, "Aggregate rating.")),
                interactions=((InteractionKind.PAGINATE, "Load more reviews."),),
                success=("Aggregate rating and individual reviews are shown honestly.",),
            ),
            SectionSpec(
                type=SectionType.RECOMMENDATIONS,
                purpose="Suggest complementary and alternative products.",
                business_goal="Increase average order value via cross-sell and upsell.",
                user_goal="Discover related products worth considering.",
                conversion_goal="Expand the basket and rescue non-fits.",
                trust_goal="Recommend genuinely relevant products.",
                required=False, priority=3, depends_on=(SectionType.BUY_BOX,),
                blocks=(BlockSpec(BlockKind.RECOMMENDATION, "Recommended products",
                                  (DataKind.RECOMMENDATION,), required=False, priority=3),),
                optional_components=(
                    ComponentSpec(ComponentKind.RECOMMENDATION_CAROUSEL, required=False,
                                  rationale="Surface cross-sell and related items.",
                                  fields=("title", "price", "url"), cardinality="many",
                                  data_kind=DataKind.RECOMMENDATION),
                ),
                success=("Recommendations link to valid, relevant products.",),
            ),
            _footer(),
        ),
    )


def _cart() -> PageSpec:
    return PageSpec(
        page_type=PageType.CART,
        purpose="Let shoppers review their selection and proceed confidently to checkout.",
        sections=(
            _global_nav(),
            SectionSpec(
                type=SectionType.CART_LINE_ITEMS,
                purpose="Show the items the shopper intends to buy.",
                business_goal="Confirm the basket and reduce abandonment.",
                user_goal="Verify what I'm about to purchase.",
                conversion_goal="Advance shoppers to checkout with confidence.",
                trust_goal="Show accurate items, prices, and quantities.",
                priority=5, depends_on=(SectionType.GLOBAL_NAV,),
                blocks=(BlockSpec(BlockKind.PRODUCT, "Cart line items",
                                  (DataKind.CART, DataKind.PRICE), priority=5),),
                required_components=(
                    ComponentSpec(ComponentKind.CART_LINE_ITEM, rationale="Represent each basket item.",
                                  fields=("title", "variant", "quantity", "price"), cardinality="many",
                                  data_kind=DataKind.CART),
                    ComponentSpec(ComponentKind.QUANTITY_SELECTOR, rationale="Adjust quantities.",
                                  fields=("quantity",)),
                ),
                data=((DataKind.CART, "Current cart contents."),),
                interactions=((InteractionKind.VALIDATE, "Update quantity and reflect totals."),),
                success=("Line items reflect the true cart with editable quantities.",),
                checklist=("Quantity edits recompute totals correctly.",),
            ),
            SectionSpec(
                type=SectionType.CART_SUMMARY,
                purpose="Show totals and the path to checkout.",
                business_goal="Convert basket into an order.",
                user_goal="See what I'll pay and proceed.",
                conversion_goal="Drive the proceed-to-checkout action.",
                trust_goal="Show transparent totals with no surprises.",
                priority=5, depends_on=(SectionType.CART_LINE_ITEMS,),
                blocks=(
                    BlockSpec(BlockKind.PRODUCT, "Order totals", (DataKind.CART, DataKind.PRICE), priority=5),
                    BlockSpec(BlockKind.CTA, "Proceed to checkout", priority=5),
                ),
                required_components=(
                    ComponentSpec(ComponentKind.ORDER_SUMMARY, rationale="Show subtotal and totals.",
                                  fields=("subtotal", "shipping", "total"), data_kind=DataKind.CART),
                ),
                interactions=((InteractionKind.CLICK, "Proceed to checkout."),),
                gate=ApprovalGate.DESIGN_DIRECTOR, approver=ApproverRole.DESIGN_DIRECTOR,
                approval_criteria=("Proceed-to-checkout is prominent and totals are transparent.",),
                success=("Totals are itemized and the checkout CTA is prominent.",),
            ),
            SectionSpec(
                type=SectionType.CROSS_SELL,
                purpose="Offer last-moment complementary products.",
                business_goal="Raise average order value before checkout.",
                user_goal="Add a useful complementary item.",
                conversion_goal="Expand the basket without derailing checkout.",
                trust_goal="Suggest only genuinely complementary items.",
                required=False, priority=2, depends_on=(SectionType.CART_LINE_ITEMS,),
                blocks=(BlockSpec(BlockKind.RECOMMENDATION, "Complementary products",
                                  (DataKind.RECOMMENDATION,), required=False, priority=2),),
                optional_components=(
                    ComponentSpec(ComponentKind.RECOMMENDATION_CAROUSEL, required=False,
                                  rationale="Cross-sell without distraction.",
                                  fields=("title", "price", "url"), cardinality="many",
                                  data_kind=DataKind.RECOMMENDATION),
                ),
                success=("Cross-sell does not obstruct the path to checkout.",),
            ),
            _footer(),
        ),
    )


def _checkout() -> PageSpec:
    return PageSpec(
        page_type=PageType.CHECKOUT,
        purpose="Convert intent into a completed order with minimal friction.",
        sections=(
            _global_nav(),
            SectionSpec(
                type=SectionType.CHECKOUT_FORM,
                purpose="Collect the contact and identity details to place the order.",
                business_goal="Complete the purchase with minimal abandonment.",
                user_goal="Enter my details quickly and correctly.",
                conversion_goal="Minimize fields and friction to completion.",
                trust_goal="Handle personal data securely and transparently.",
                priority=5, depends_on=(SectionType.GLOBAL_NAV,),
                blocks=(BlockSpec(BlockKind.FORM, "Contact and identity fields",
                                  (DataKind.CUSTOMER,), priority=5),),
                required_components=(
                    ComponentSpec(ComponentKind.CHECKOUT_FORM, rationale="Collect required details.",
                                  fields=("email", "name"), data_kind=DataKind.CUSTOMER),
                ),
                interactions=((InteractionKind.VALIDATE, "Validate fields inline."),
                              (InteractionKind.SUBMIT, "Advance the checkout step.")),
                gate=ApprovalGate.STRATEGY_SIGNOFF, approver=ApproverRole.STRATEGIST,
                approval_criteria=("Field count is minimized and matches the friction budget.",),
                success=("The form validates inline and minimizes required fields.",),
                checklist=("Only strictly necessary fields are required.",),
            ),
            SectionSpec(
                type=SectionType.SHIPPING,
                purpose="Capture and confirm the shipping method and address.",
                business_goal="Prevent shipping surprises that cause abandonment.",
                user_goal="Choose delivery I understand and can afford.",
                conversion_goal="Keep the shopper moving to payment.",
                trust_goal="Show accurate shipping costs and timelines up front.",
                priority=4, depends_on=(SectionType.CHECKOUT_FORM,),
                blocks=(BlockSpec(BlockKind.FORM, "Shipping address and method",
                                  (DataKind.CUSTOMER,), priority=4),),
                required_components=(
                    ComponentSpec(ComponentKind.ADDRESS_FORM, rationale="Collect the delivery address.",
                                  fields=("address", "city", "postcode"), data_kind=DataKind.CUSTOMER),
                ),
                success=("Shipping cost and timeline are shown before payment.",),
            ),
            SectionSpec(
                type=SectionType.PAYMENT,
                purpose="Collect payment securely to complete the order.",
                business_goal="Capture revenue reliably.",
                user_goal="Pay quickly with a method I trust.",
                conversion_goal="Complete the order with no last-step friction.",
                trust_goal="Convey security and payment legitimacy.",
                priority=5, depends_on=(SectionType.SHIPPING,),
                blocks=(BlockSpec(BlockKind.FORM, "Payment method fields", priority=5),),
                required_components=(
                    ComponentSpec(ComponentKind.PAYMENT_METHODS, rationale="Offer trusted payment options.",
                                  fields=("method",), cardinality="many"),
                ),
                interactions=((InteractionKind.SUBMIT, "Submit payment and place the order."),),
                gate=ApprovalGate.STRATEGY_SIGNOFF, approver=ApproverRole.STRATEGIST,
                approval_criteria=("Payment step conveys security and offers expected methods.",),
                success=("Payment supports the expected methods and signals security.",),
                checklist=("Security and payment-legitimacy signals are present.",),
            ),
            SectionSpec(
                type=SectionType.ORDER_SUMMARY,
                purpose="Confirm exactly what is being purchased and paid.",
                business_goal="Prevent disputes and abandonment from opacity.",
                user_goal="Verify the order and total before paying.",
                conversion_goal="Give confidence to complete the purchase.",
                trust_goal="Show a fully transparent, itemized total.",
                priority=4, depends_on=(SectionType.CHECKOUT_FORM,),
                blocks=(BlockSpec(BlockKind.PRODUCT, "Order line items and total",
                                  (DataKind.ORDER, DataKind.PRICE), priority=4),),
                required_components=(
                    ComponentSpec(ComponentKind.ORDER_SUMMARY, rationale="Confirm items and totals.",
                                  fields=("items", "total"), data_kind=DataKind.ORDER),
                ),
                data=((DataKind.ORDER, "The order being placed."),),
                success=("The itemized total matches the cart with no hidden fees.",),
            ),
            SectionSpec(
                type=SectionType.TRUST,
                purpose="Reassure the shopper through the final steps.",
                business_goal="Reduce last-step abandonment.",
                user_goal="Feel safe completing payment.",
                conversion_goal="Hold confidence through submission.",
                trust_goal="Show security, guarantees, and support access.",
                priority=3, depends_on=(SectionType.PAYMENT,),
                blocks=(BlockSpec(BlockKind.TRUST, "Security and guarantee signals", priority=3),),
                required_components=(
                    ComponentSpec(ComponentKind.TRUST_BADGES, rationale="Reassure at the point of payment.",
                                  fields=("label",), cardinality="many"),
                ),
                success=("Security and support signals are visible during payment.",),
            ),
            _footer(),
        ),
    )


def _landing() -> PageSpec:
    return PageSpec(
        page_type=PageType.LANDING,
        purpose="Convert campaign traffic against a single focused offer.",
        sections=(
            _global_nav(),
            SectionSpec(
                type=SectionType.HERO,
                purpose="State the campaign offer and its single call to action.",
                business_goal="Convert paid/campaign traffic efficiently.",
                user_goal="Understand the offer and act on it.",
                conversion_goal="Drive the single primary campaign action.",
                trust_goal="Match the ad's promise credibly.",
                priority=5, depends_on=(SectionType.GLOBAL_NAV,),
                blocks=(
                    BlockSpec(BlockKind.HERO, "Offer headline", priority=5),
                    BlockSpec(BlockKind.CTA, "Primary campaign CTA", priority=5),
                ),
                required_components=(
                    ComponentSpec(ComponentKind.HERO_BANNER, rationale="Lead with the offer.",
                                  fields=("headline", "cta")),
                ),
                gate=ApprovalGate.DESIGN_DIRECTOR, approver=ApproverRole.DESIGN_DIRECTOR,
                approval_criteria=("Message match with the campaign is verified.",),
                success=("A single primary CTA is dominant above the fold.",),
                checklist=("Offer copy matches the campaign source.",),
            ),
            SectionSpec(
                type=SectionType.VALUE_PROPOSITION,
                purpose="Justify the offer with focused benefits.",
                business_goal="Increase campaign conversion rate.",
                user_goal="See why the offer is worth taking.",
                conversion_goal="Reinforce the single CTA.",
                trust_goal="Substantiate the offer's claims.",
                priority=4, depends_on=(SectionType.HERO,),
                blocks=(BlockSpec(BlockKind.CONTENT, "Focused benefit points", priority=4),),
                required_components=(
                    ComponentSpec(ComponentKind.CONTENT_BLOCK, rationale="Present the offer benefits.",
                                  fields=("heading", "body")),
                ),
                success=("Benefits map directly to the offer.",),
            ),
            SectionSpec(
                type=SectionType.SOCIAL_PROOF,
                purpose="Validate the offer with proof.",
                business_goal="Reduce skepticism on cold traffic.",
                user_goal="See that the offer is credible.",
                conversion_goal="Remove hesitation before the CTA.",
                trust_goal="Show authentic proof.",
                required=False, priority=3, depends_on=(SectionType.VALUE_PROPOSITION,),
                blocks=(BlockSpec(BlockKind.REVIEW, "Testimonials or ratings",
                                  (DataKind.REVIEW,), required=False, priority=3),),
                success=("Proof is genuine and relevant to the offer.",),
            ),
            SectionSpec(
                type=SectionType.FAQ,
                purpose="Resolve the objections that block conversion.",
                business_goal="Recover conversions lost to unanswered questions.",
                user_goal="Get my blocking questions answered.",
                conversion_goal="Clear objections adjacent to the CTA.",
                trust_goal="Answer honestly and completely.",
                required=False, priority=2, depends_on=(SectionType.VALUE_PROPOSITION,),
                blocks=(BlockSpec(BlockKind.FAQ, "Objection-handling questions",
                                  (DataKind.FAQ,), required=False, priority=2),),
                optional_components=(
                    ComponentSpec(ComponentKind.FAQ_ACCORDION, required=False,
                                  rationale="Answer objections compactly.",
                                  fields=("question", "answer"), cardinality="many",
                                  data_kind=DataKind.FAQ),
                ),
                interactions=((InteractionKind.EXPAND_COLLAPSE, "Reveal answers."),),
                success=("Top objections for the offer are addressed.",),
            ),
            _footer(),
        ),
    )


def _blog() -> PageSpec:
    return PageSpec(
        page_type=PageType.BLOG,
        purpose="Publish content that builds authority and routes readers to products.",
        sections=(
            _global_nav(),
            _breadcrumbs(),
            SectionSpec(
                type=SectionType.ARTICLE_LIST,
                purpose="Present articles for readers to browse.",
                business_goal="Build authority and organic reach.",
                user_goal="Find content relevant to my interest.",
                conversion_goal="Route engaged readers toward products.",
                trust_goal="Demonstrate expertise credibly.",
                priority=5, depends_on=(SectionType.BREADCRUMBS,),
                blocks=(BlockSpec(BlockKind.CONTENT, "Article cards", (DataKind.ARTICLE,), priority=5),),
                required_components=(
                    ComponentSpec(ComponentKind.ARTICLE_CARD, rationale="Represent each article.",
                                  fields=("title", "excerpt", "url"), cardinality="many",
                                  data_kind=DataKind.ARTICLE),
                    ComponentSpec(ComponentKind.PAGINATION, rationale="Page through articles.",
                                  fields=("page", "total")),
                ),
                data=((DataKind.ARTICLE, "Published articles."),),
                interactions=((InteractionKind.CLICK, "Open an article."),
                              (InteractionKind.PAGINATE, "Load more articles.")),
                success=("Article cards link to valid articles.",),
            ),
            SectionSpec(
                type=SectionType.NEWSLETTER,
                purpose="Capture email intent from engaged readers.",
                business_goal="Grow the marketable audience from content.",
                user_goal="Subscribe for more content.",
                conversion_goal="Convert readers into subscribers.",
                trust_goal="Set clear expectations for content emails.",
                required=False, priority=2, depends_on=(SectionType.ARTICLE_LIST,),
                blocks=(BlockSpec(BlockKind.FORM, "Email signup", required=False, priority=2),),
                optional_components=(
                    ComponentSpec(ComponentKind.NEWSLETTER_FORM, required=False,
                                  rationale="Collect subscriptions.", fields=("email",)),
                ),
                success=("Signup validates and confirms.",),
            ),
            _footer(),
        ),
    )


def _search() -> PageSpec:
    return PageSpec(
        page_type=PageType.SEARCH,
        purpose="Let shoppers find products by query, then filter and sort the results.",
        sections=(
            _global_nav(),
            SectionSpec(
                type=SectionType.SEARCH_BAR,
                purpose="Accept and refine the shopper's query.",
                business_goal="Turn intent-rich queries into product visits.",
                user_goal="Find exactly what I'm looking for.",
                conversion_goal="Route high-intent shoppers to products fast.",
                trust_goal="Show a capable, forgiving search.",
                priority=5, depends_on=(SectionType.GLOBAL_NAV,),
                blocks=(BlockSpec(BlockKind.FORM, "Search input", priority=5),),
                required_components=(
                    ComponentSpec(ComponentKind.SEARCH_INPUT, rationale="Capture and suggest queries.",
                                  fields=("query",)),
                ),
                interactions=((InteractionKind.AUTOCOMPLETE, "Suggest queries as the shopper types."),
                              (InteractionKind.SUBMIT, "Run the search.")),
                success=("Search accepts a query and returns relevant results.",),
            ),
            SectionSpec(
                type=SectionType.FILTERS,
                purpose="Let shoppers narrow the result set by facets.",
                business_goal="Improve findability within results.",
                user_goal="Refine results to my needs.",
                conversion_goal="Move qualified shoppers to product pages.",
                trust_goal="Show organized, controllable results.",
                priority=3, depends_on=(SectionType.SEARCH_BAR,),
                blocks=(BlockSpec(BlockKind.CONTENT, "Result facets", (DataKind.FACET,), priority=3),),
                required_components=(
                    ComponentSpec(ComponentKind.SEARCH_FACETS, rationale="Narrow the results.",
                                  fields=("facet", "values"), cardinality="many",
                                  data_kind=DataKind.FACET),
                ),
                interactions=((InteractionKind.FILTER, "Apply facets to results."),),
                success=("Facets refine the result set.",),
            ),
            SectionSpec(
                type=SectionType.SORT_BAR,
                purpose="Let shoppers reorder search results.",
                business_goal="Surface the most compelling results first.",
                user_goal="Order results the way I shop.",
                conversion_goal="Bring high-intent products to the top.",
                trust_goal="Give control over the view.",
                priority=2, depends_on=(SectionType.SEARCH_BAR,),
                blocks=(BlockSpec(BlockKind.CTA, "Sort selector", priority=2),),
                required_components=(
                    ComponentSpec(ComponentKind.SORT_DROPDOWN, rationale="Reorder results.",
                                  fields=("option",)),
                ),
                interactions=((InteractionKind.SORT, "Change the sort order."),),
                success=("Sorting reorders results deterministically.",),
            ),
            SectionSpec(
                type=SectionType.RESULTS_GRID,
                purpose="Present matching products for selection.",
                business_goal="Convert search into product visits.",
                user_goal="Scan matches and pick products.",
                conversion_goal="Move shoppers to product pages.",
                trust_goal="Show accurate prices and availability.",
                priority=5, depends_on=(SectionType.SEARCH_BAR,),
                blocks=(BlockSpec(BlockKind.PRODUCT, "Search result cards",
                                  (DataKind.SEARCH_RESULT, DataKind.PRICE), priority=5),),
                required_components=(
                    ComponentSpec(ComponentKind.PRODUCT_CARD, rationale="Represent each result.",
                                  fields=("title", "price", "url"), cardinality="many",
                                  data_kind=DataKind.SEARCH_RESULT),
                ),
                data=((DataKind.SEARCH_RESULT, "Products matching the query."),),
                interactions=((InteractionKind.CLICK, "Open a product page."),),
                success=("Results link to valid product pages.",),
            ),
            SectionSpec(
                type=SectionType.NO_RESULTS,
                purpose="Recover shoppers when a query returns nothing.",
                business_goal="Rescue zero-result sessions.",
                user_goal="Get a path forward when nothing matched.",
                conversion_goal="Redirect to suggestions or popular products.",
                trust_goal="Fail gracefully and helpfully.",
                required=False, priority=2, depends_on=(SectionType.SEARCH_BAR,),
                blocks=(BlockSpec(BlockKind.CONTENT, "Zero-result guidance and suggestions",
                                  required=False, priority=2),),
                success=("A zero-result query offers a helpful recovery path.",),
            ),
            _footer(),
        ),
    )


def _account() -> PageSpec:
    return PageSpec(
        page_type=PageType.ACCOUNT,
        purpose="Let returning customers manage their orders and details.",
        sections=(
            _global_nav(),
            SectionSpec(
                type=SectionType.ACCOUNT_MENU,
                purpose="Provide navigation across account areas.",
                business_goal="Increase retention through self-service.",
                user_goal="Reach the account area I need.",
                conversion_goal="Enable reorders and account-driven purchases.",
                trust_goal="Signal secure, in-control account management.",
                priority=4, depends_on=(SectionType.GLOBAL_NAV,),
                blocks=(BlockSpec(BlockKind.NAV, "Account section menu", (DataKind.CUSTOMER,), priority=4),),
                required_components=(
                    ComponentSpec(ComponentKind.NAV_MENU, rationale="Navigate account areas.",
                                  fields=("label", "url"), cardinality="many"),
                ),
                success=("All account areas are reachable from the menu.",),
            ),
            SectionSpec(
                type=SectionType.ORDER_HISTORY,
                purpose="Show past orders and their status.",
                business_goal="Drive reorders and reduce support load.",
                user_goal="Review and reorder past purchases.",
                conversion_goal="Enable one-click reordering.",
                trust_goal="Show accurate order records.",
                priority=5, depends_on=(SectionType.ACCOUNT_MENU,),
                blocks=(BlockSpec(BlockKind.PRODUCT, "Order history list",
                                  (DataKind.ORDER,), priority=5),),
                required_components=(
                    ComponentSpec(ComponentKind.ORDER_SUMMARY, rationale="Summarize each past order.",
                                  fields=("id", "date", "total", "status"), cardinality="many",
                                  data_kind=DataKind.ORDER),
                ),
                data=((DataKind.ORDER, "The customer's order history."),),
                interactions=((InteractionKind.CLICK, "View or reorder a past order."),),
                success=("Order history is accurate and reorder is available.",),
                checklist=("Order records match the customer's true history.",),
            ),
            _footer(),
        ),
    )


def _cms() -> PageSpec:
    return PageSpec(
        page_type=PageType.CMS,
        purpose="Present editorial or informational content within the store frame.",
        sections=(
            _global_nav(),
            SectionSpec(
                type=SectionType.CONTENT_BODY,
                purpose="Render the CMS content clearly and accessibly.",
                business_goal="Support the store with informational content (about, policies).",
                user_goal="Read the information I came for.",
                conversion_goal="Route interested readers back toward products.",
                trust_goal="Present accurate, well-structured information.",
                priority=5, depends_on=(SectionType.GLOBAL_NAV,),
                blocks=(BlockSpec(BlockKind.CONTENT, "CMS body content", (DataKind.CONTENT,), priority=5),),
                required_components=(
                    ComponentSpec(ComponentKind.CONTENT_BLOCK, rationale="Render the CMS body.",
                                  fields=("heading", "body"), data_kind=DataKind.CONTENT),
                ),
                data=((DataKind.CONTENT, "The CMS page content."),),
                success=("Content renders with a correct heading hierarchy.",),
                checklist=("Content is accurate and links resolve.",),
            ),
            _footer(),
        ),
    )


_SPECS: dict[PageType, PageSpec] = {
    PageType.HOMEPAGE: _homepage(),
    PageType.COLLECTION: _collection(),
    PageType.PRODUCT: _product(),
    PageType.CART: _cart(),
    PageType.CHECKOUT: _checkout(),
    PageType.LANDING: _landing(),
    PageType.BLOG: _blog(),
    PageType.SEARCH: _search(),
    PageType.ACCOUNT: _account(),
    PageType.CMS: _cms(),
}


def spec_for(page_type: PageType) -> PageSpec:
    """Return the blueprint for a page type.

    Raises:
        UnknownPageTypeError: If no blueprint exists for ``page_type``.
    """
    spec = _SPECS.get(page_type)
    if spec is None:  # pragma: no cover - all ten page types are defined
        raise UnknownPageTypeError(
            f"No blueprint for page type {page_type.value}.",
            details={"page_type": page_type.value},
        )
    return spec
