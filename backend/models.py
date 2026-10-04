"""Structured types for the Campus Customs chatbot.

Product fields mirror the existing `catalogue` and `inventory` tables (and the
`/api/products` responses) so the chatbot, the API and the frontend all describe
a product the same way.
"""

from typing import Literal

from pydantic import BaseModel, Field


# --- What the tools return to the agent --------------------------------------
#
# Every tool returns one of these models, never free text, so the agent always
# gets the same fields and an explicit status/message when something is missing.

#: Stock status of one size: "low_stock" means 1 to LOW_STOCK_THRESHOLD left.
SizeStatus = Literal["in_stock", "low_stock", "out_of_stock"]
#: Overall availability of a product across all its sizes.
Availability = Literal["in_stock", "low_stock", "out_of_stock", "stock_unknown"]
#: Outcome of a single-size stock check.
SizeCheckStatus = Literal[
    "in_stock", "low_stock", "out_of_stock", "size_not_offered", "invalid_size",
    "stock_unknown", "product_not_found",
]


class SizeStock(BaseModel):
    """Stock for one size of a product: one row of the `inventory` table."""

    size: str
    quantity: int
    status: SizeStatus


#: Product categories the search tool can browse. Each is a keyword rule over the
#: catalogue's garment_type column (see tools.CATEGORY_RULES), not a product list.
Category = Literal[
    "hoodies", "sweatshirts", "crewnecks", "quarter-zips", "t-shirts", "shirts",
    "long-sleeve shirts", "jackets",
]


class ProductMatch(BaseModel):
    """One product found by a search: everything the agent needs to recommend it and
    everything the frontend needs to render its product card.

    The same model is returned by the search tool to the agent and by POST /api/chat
    to the frontend (in ChatResponse.product_matches), so both sides read identical fields.
    """

    product_id: str = Field(description="Unique catalogue ID; the card links to /products/<product_id>.")
    name: str
    price: float | None = Field(description="US dollars; None when the catalogue has no price.")
    image_url: str | None = Field(description="URL of the catalogue photo, e.g. /data/products/x.jpg; None if there is no photo.")
    short_description: str | None = Field(description="Description shortened to fit a card; None when there is no description.")
    description: str | None = Field(description="Full catalogue description; None when there is none.")
    garment_type: str | None
    colors: list[str]
    availability: Availability
    sizes_in_stock: list[str]
    match_reason: str | None = Field(
        None,
        description="Why this product fits the customer's request, built only from catalogue facts. "
        "Set by recommend_products; None for plain searches.",
    )


class ProductSearchResult(BaseModel):
    """Result of search_products."""

    query: str
    category: Category | None = None
    total_matches: int = Field(description="Products that matched, before the result limit.")
    min_price: float | None = Field(None, description="Lowest price across ALL matches, not only those returned.")
    max_price: float | None = Field(None, description="Highest price across ALL matches, not only those returned.")
    products: list[ProductMatch] = Field(description="Best matches first; empty when nothing matched.")
    message: str | None = Field(description="Explains an empty or truncated result; None otherwise.")


class RecommendationCriteria(BaseModel):
    """The customer preferences recommend_products understood, echoed back to the agent."""

    keywords: str = ""
    category: Category | None = None
    colors: list[str] = Field(default_factory=list)
    min_price: float | None = None
    max_price: float | None = None
    size: str | None = Field(None, description="Normalized inventory size, e.g. M.")
    in_stock_only: bool = True


class RelaxationSuggestion(BaseModel):
    """A constraint the customer could drop, and how many products would then match."""

    constraint: Literal["keywords", "category", "colors", "min_price", "max_price", "size", "in_stock_only"]
    suggestion: str = Field(description="Plain-English suggestion, e.g. 'Raise or remove the $40.00 price limit'.")
    matches: int


class RecommendationResult(BaseModel):
    """Result of recommend_products."""

    criteria: RecommendationCriteria
    total_matches: int = Field(description="Products meeting every criterion, before the limit.")
    recommendations: list[ProductMatch] = Field(description="Best first, each with a match_reason; empty if none matched.")
    suggestions: list[RelaxationSuggestion] = Field(
        default_factory=list, description="Only when nothing matched: constraints that, if dropped, give results."
    )
    message: str | None = None


class ProductDetailsResult(BaseModel):
    """Result of get_product_details: description, price and stock for every size."""

    found: bool
    product_id: str | None = Field(description="Catalogue ID; None when no product was found.")
    name: str | None = None
    garment_type: str | None = None
    description: str | None = None
    colors: list[str] = Field(default_factory=list)
    price: float | None = None
    total_stock: int | None = Field(None, description="Items in stock across all sizes; None if stock is unknown.")
    availability: Availability | None = None
    sizes: list[SizeStock] = Field(default_factory=list, description="Every size listed in inventory, XS to XXL.")
    sizes_in_stock: list[str] = Field(default_factory=list)
    sizes_out_of_stock: list[str] = Field(default_factory=list)
    message: str | None = Field(None, description="Says what is missing or not found; None when complete.")


class SizeStockResult(BaseModel):
    """Result of check_size_stock: stock for one size of one product."""

    status: SizeCheckStatus
    requested_size: str = Field(description="The size exactly as the customer asked for it.")
    size: str | None = Field(description="The requested size as an inventory size (XS, S, M, L, XL, XXL); None if not recognized.")
    product_id: str | None = None
    name: str | None = None
    price: float | None = None
    quantity: int | None = Field(None, description="Items in stock in this size; None if the size or product was not found.")
    sizes_offered: list[str] = Field(default_factory=list, description="Every size this product has an inventory row for, in or out of stock.")
    other_sizes_in_stock: list[str] = Field(default_factory=list, description="Alternatives to suggest when this size is unavailable.")
    message: str = Field(description="One-sentence plain-English summary of the result for the agent.")


class GarmentTypeSummary(BaseModel):
    """One kind of item sold, from grouping the catalogue by garment_type."""

    garment_type: str
    product_count: int
    min_price: float | None
    max_price: float | None


# --- What the agent returns (its structured output) --------------------------


class AgentReply(BaseModel):
    """The agent's answer to one customer message."""

    reply: str = Field(
        description="The message shown to the customer: friendly, concise plain text, no markdown."
    )
    product_ids: list[str] = Field(
        default_factory=list,
        description=(
            "product_id of each product to show as a product card, in display order. Only IDs "
            "returned by a tool in this conversation, at most 12. After a product search, list "
            "the relevant matches. Empty when the search found nothing or no product is discussed."
        ),
    )


# --- Who is chatting and where they are (agent dependencies) -----------------


class CustomerContext(BaseModel):
    """The authenticated customer, read from the users table via the session cookie.

    Never built from anything the browser sends, and never present for guests.
    """

    user_id: int
    first_name: str | None
    last_name: str | None
    email: str


#: Kinds of page on the website the chat can be opened from.
PageType = Literal[
    "home", "product_list", "product_detail", "about", "login", "create_account", "account", "other"
]


class CurrentProduct(BaseModel):
    """The product shown on the page the customer is viewing, looked up in the catalogue."""

    product_id: str
    name: str
    garment_type: str | None
    description: str | None
    colors: list[str]
    price: float | None


class PageContext(BaseModel):
    """Where the customer is on the website, resolved on the server for the agent."""

    page_type: PageType
    path: str
    product: CurrentProduct | None = Field(
        None, description="The product on a product page; None on other pages or if the ID is unknown."
    )
    product_not_found: bool = Field(
        False, description="True when a product page was reported but its product_id is not in the catalogue."
    )


class ShownProduct(BaseModel):
    """One product card from the most recent reply that showed products, numbered as displayed."""

    position: int = Field(description="1 for the first card shown, 2 for the second, and so on.")
    product_id: str
    name: str
    garment_type: str | None
    colors: list[str]
    price: float | None


class ConversationContext(BaseModel):
    """Structured memory of what the customer has just been shown, for resolving follow-ups
    such as "the second one", "the blue one" or "which one is cheapest?".

    Built on the server from the conversation history (the database for logged-in
    customers), with every product re-read from the catalogue.
    """

    recent_products: list[ShownProduct] = Field(
        default_factory=list, description="Cards from the most recent assistant reply that showed products."
    )
    recent_products_query: str | None = Field(
        None, description="The customer message that led to those cards."
    )
    selected_product: ShownProduct | None = Field(
        None,
        description="The single product the conversation is about: the product page being viewed, "
        "or the only card in the most recent product reply. None when ambiguous.",
    )
    selected_product_source: Literal["current_page", "only_recent_product"] | None = None


# --- What the chat API exchanges with the frontend ---------------------------


class PageInfo(BaseModel):
    """What the frontend reports about the current page. Only the product_id is trusted
    as a key; everything about the product itself is read from the database."""

    page_type: PageType = "other"
    path: str = Field("/", max_length=300)
    product_id: str | None = Field(None, max_length=200)


class ChatTurn(BaseModel):
    """One earlier message in the conversation."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)
    product_ids: list[str] = Field(
        default_factory=list, description="Products shown as cards with this assistant message."
    )


class ChatRequest(BaseModel):
    """Body of POST /api/chat.

    `history` is only used for guests. For a logged-in customer the server loads the
    history from the chat_messages table and ignores this field, so nothing is duplicated.
    """

    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list)
    page: PageInfo | None = None


class ChatResponse(BaseModel):
    """Body returned by POST /api/chat: the reply text plus structured product matches.

    product_matches is always present; it is an empty list when the agent found or
    recommended no products. Each match is rebuilt from the database, never taken from
    the model's text.
    """

    reply: str
    product_matches: list[ProductMatch] = Field(default_factory=list)
    saved: bool = Field(False, description="True when this exchange was stored in the customer's chat history.")


class StoredChatMessage(BaseModel):
    """One message from the customer's saved chat history."""

    id: int
    role: Literal["user", "assistant"]
    content: str
    product_matches: list[ProductMatch] = Field(default_factory=list)
    created_at: str = Field(description="UTC timestamp, 'YYYY-MM-DD HH:MM:SS'.")


class ChatHistoryResponse(BaseModel):
    """Body returned by GET /api/chat/history."""

    authenticated: bool
    messages: list[StoredChatMessage] = Field(default_factory=list)
