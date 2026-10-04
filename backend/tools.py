"""Tools the Campus Customs chatbot can call.

Every tool reads the existing `catalogue` and `inventory` tables in
data/campus_customs.db, the single source of truth: no price, description or
stock number is written in this file or in the prompt. All queries are
read-only and parameterized, and nothing about users is reachable from a tool.

Each tool returns a model from models.py, with an explicit status or message
whenever a product, a size or a value is missing, so the agent never has to
guess.
"""

import json
import re
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass, field

from pydantic_ai import RunContext

from db import get_connection
from models import (
    Availability,
    Category,
    ConversationContext,
    CurrentProduct,
    CustomerContext,
    GarmentTypeSummary,
    PageContext,
    PageInfo,
    ProductDetailsResult,
    ProductMatch,
    ProductSearchResult,
    RecommendationCriteria,
    RecommendationResult,
    RelaxationSuggestion,
    ShownProduct,
    SizeStatus,
    SizeStock,
    SizeStockResult,
)

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
#: A size with this many items or fewer (but more than zero) is "low_stock".
LOW_STOCK_THRESHOLD = 5
MAX_SEARCH_RESULTS = 12
#: Card text is cut to about this many characters, at a word boundary.
SHORT_DESCRIPTION_LENGTH = 110

# How customers write sizes, mapped to the sizes used in the inventory table.
SIZE_ALIASES = {
    "xs": "XS", "extra small": "XS", "x-small": "XS", "xsmall": "XS",
    "s": "S", "small": "S", "sm": "S",
    "m": "M", "medium": "M", "med": "M",
    "l": "L", "large": "L", "lg": "L",
    "xl": "XL", "extra large": "XL", "x-large": "XL", "xlarge": "XL",
    "xxl": "XXL", "2xl": "XXL", "2x": "XXL", "xx-large": "XXL", "xxlarge": "XXL",
    "extra extra large": "XXL", "double xl": "XXL",
}

STOPWORDS = {
    "a", "all", "an", "and", "any", "are", "available", "can", "do", "does", "for", "got",
    "have", "i", "in", "is", "item", "looking", "me", "my", "of", "on", "or", "please",
    "product", "sell", "show", "some", "something", "stuff", "the", "there", "to", "want",
    "what", "with", "you", "your",
    "yale",  # every product is Yale merchandise, so "yale" does not narrow anything
}

# Customers and the catalogue use different words for the same thing. Keys and
# single-word alternatives are compared after plural "s" is removed (see _stem);
# alternatives with a space are matched as phrases.
SYNONYMS = {
    "hoodie": ["hoodie", "hooded", "hood"],
    "hooded": ["hoodie", "hooded", "hood"],
    "hoody": ["hoodie", "hooded", "hood"],
    "tee": ["t shirt", "tee"],
    "tshirt": ["t shirt"],
    "t shirt": ["t shirt"],
    "sweatshirt": ["sweatshirt", "crewneck", "hoodie", "hooded"],
    "sweater": ["sweater", "sweatshirt", "crewneck", "fleece"],
    "crew": ["crewneck"],
    "quarter zip": ["quarter zip", "1 4 zip"],
    "1 4 zip": ["quarter zip", "1 4 zip"],
    "grey": ["gray", "grey"],
    "gray": ["gray", "grey"],
}

# Category rules over the lowercase garment_type column. Categories describe kinds
# of garment, so new products are categorized automatically from their garment_type.
CATEGORY_RULES: dict[str, Callable[[str], bool]] = {
    "hoodies": lambda g: "hood" in g,
    "crewnecks": lambda g: "crewneck" in g or "mockneck" in g,
    "quarter-zips": lambda g: "quarter-zip" in g,
    "sweatshirts": lambda g: any(k in g for k in ("sweatshirt", "hood", "crewneck", "mockneck", "quarter-zip")),
    "t-shirts": lambda g: "t-shirt" in g,
    "long-sleeve shirts": lambda g: "long-sleeve" in g and "shirt" in g and "sweatshirt" not in g,
    "shirts": lambda g: "t-shirt" in g or ("shirt" in g and "sweatshirt" not in g),
    "jackets": lambda g: "jacket" in g,
}


@dataclass
class ChatDeps:
    """Per-request context handed to the agent (and every tool) through RunContext.

    Built by the chat endpoint for each message: `customer` comes from the session
    cookie and the users table, `page` from the page the customer is viewing.
    """

    customer: CustomerContext | None = None  # None means a guest: no authenticated customer
    page: PageContext | None = None
    conversation: ConversationContext | None = None
    #: Filled in by recommend_products during a run (product_id -> reason), so the
    #: reasons reach the product cards without the model rewriting them.
    recommendation_reasons: dict[str, str] = field(default_factory=dict)

    @property
    def is_guest(self) -> bool:
        return self.customer is None


#: Display names for categories (used by the Products page filters).
CATEGORY_LABELS = {
    "hoodies": "Hoodies",
    "sweatshirts": "Sweatshirts (all)",
    "crewnecks": "Crewnecks",
    "quarter-zips": "Quarter-zips",
    "t-shirts": "T-shirts",
    "shirts": "Shirts (all)",
    "long-sleeve shirts": "Long-sleeve shirts",
    "jackets": "Jackets",
}

# A customer's color word, mapped to the words that count as that color in the
# catalogue's colors column ("blue" includes "navy blue" and "navy").
COLOR_FAMILIES = {
    "blue": ["blue", "navy"],
    "gray": ["gray", "grey", "charcoal"],
    "grey": ["gray", "grey", "charcoal"],
    "white": ["white", "ivory", "cream"],
    "red": ["red", "crimson", "maroon", "burgundy"],
}


# --- Helpers ------------------------------------------------------------------


def normalize_size(size: str) -> str | None:
    """Map a size as a customer writes it ("medium", "2XL") to an inventory size, or None."""
    key = re.sub(r"\s+", " ", size.strip().lower())
    return SIZE_ALIASES.get(key)


def _size_status(quantity: int) -> SizeStatus:
    if quantity <= 0:
        return "out_of_stock"
    if quantity <= LOW_STOCK_THRESHOLD:
        return "low_stock"
    return "in_stock"


def _availability(sizes: list[SizeStock]) -> Availability:
    if not sizes:
        return "stock_unknown"
    total = sum(s.quantity for s in sizes)
    if total <= 0:
        return "out_of_stock"
    if total <= LOW_STOCK_THRESHOLD:
        return "low_stock"
    return "in_stock"


def _stock_for(conn: sqlite3.Connection, product_id: str) -> list[SizeStock]:
    rows = conn.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
    ).fetchall()
    rank = {size: i for i, size in enumerate(SIZE_ORDER)}
    stock = [
        SizeStock(size=r["size"], quantity=r["quantity"], status=_size_status(r["quantity"]))
        for r in rows
    ]
    return sorted(stock, key=lambda s: rank.get(s.size, len(SIZE_ORDER)))


def _text_or_none(value: str | None) -> str | None:
    return value.strip() if value and value.strip() else None


def _json_list(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value) if value else []
    except json.JSONDecodeError:
        return []
    return [str(v) for v in parsed] if isinstance(parsed, list) else []


def _find_product(conn: sqlite3.Connection, product: str) -> sqlite3.Row | None:
    """Look a product up by its product_id, or by its exact name (case-insensitive)."""
    key = product.strip()
    row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (key.lower(),)).fetchone()
    if row is None:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE lower(name) = lower(?)", (key,)
        ).fetchone()
    return row


def _stem(word: str) -> str:
    """Drop a plural "s" so "hoodies" matches "hoodie" (but "dress" stays "dress")."""
    return word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss") else word


def _words(text: str) -> list[str]:
    return [_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())]


def _searchable(row: sqlite3.Row) -> tuple[set[str], str]:
    """A product's searchable words, and the same words as one string for phrase matching."""
    fields = [row["name"], row["garment_type"], row["description"], row["colors"], row["search_tags"]]
    words = _words(" ".join(f or "" for f in fields))
    return set(words), " " + " ".join(words) + " "


def _query_terms(query: str) -> list[list[str]]:
    """Split a query into terms; each term is a list of alternative words or phrases."""
    text = " ".join(_words(query))
    for phrase in ("t shirt", "quarter zip", "1 4 zip"):  # keep two-word terms together
        text = text.replace(phrase, phrase.replace(" ", "_"))
    terms = []
    for word in text.split():
        word = word.replace("_", " ")
        if word in STOPWORDS:
            continue
        terms.append([" ".join(_words(a)) for a in SYNONYMS.get(word, [word])])
    return terms


def _term_matches(alternatives: list[str], words: set[str], phrase_text: str) -> bool:
    return any(f" {a} " in phrase_text if " " in a else a in words for a in alternatives)


def _short_description(description: str | None) -> str | None:
    if not description:
        return None
    if len(description) <= SHORT_DESCRIPTION_LENGTH:
        return description
    cut = description[:SHORT_DESCRIPTION_LENGTH].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return cut + "…"


def _product_match(row: sqlite3.Row, stock: list[SizeStock]) -> ProductMatch:
    """Build the ProductMatch shared by the search tool and the chat API."""
    description = _text_or_none(row["description"])
    return ProductMatch(
        product_id=row["product_id"],
        name=row["name"],
        price=row["price"],
        image_url=f"/data/{row['image_file_path']}" if row["image_file_path"] else None,
        short_description=_short_description(description),
        description=description,
        garment_type=_text_or_none(row["garment_type"]),
        colors=_json_list(row["colors"]),
        availability=_availability(stock),
        sizes_in_stock=[s.size for s in stock if s.quantity > 0],
    )


# --- Tools --------------------------------------------------------------------


@dataclass
class Candidate:
    """One catalogue product that passed every filter, with what it matched."""

    row: sqlite3.Row
    stock: list[SizeStock]
    score: int  # how many query terms matched
    matched_colors: list[str]

    @property
    def in_stock(self) -> bool:
        return any(s.quantity > 0 for s in self.stock)


def category_of(garment_type: str | None) -> list[str]:
    """Every category a garment type belongs to (categories overlap, e.g. hoodies are sweatshirts)."""
    g = (garment_type or "").lower()
    return [name for name, rule in CATEGORY_RULES.items() if rule(g)]


def _color_matches(wanted: list[str], product_colors: list[str]) -> list[str] | None:
    """The product colors that satisfy every wanted color, or None if one is missing."""
    matched: list[str] = []
    lowered = [c.lower() for c in product_colors]
    for color in wanted:
        family = COLOR_FAMILIES.get(color.strip().lower(), [color.strip().lower()])
        hits = [orig for orig, low in zip(product_colors, lowered) if any(f in low for f in family)]
        if not hits:
            return None
        matched.extend(h for h in hits if h not in matched)
    return matched


def find_products(
    query: str = "",
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    size: str | None = None,
    in_stock_only: bool = False,
    colors: list[str] | None = None,
) -> list[Candidate]:
    """The one catalogue search used by the chat tools and the Products page API.

    `size` must already be an inventory size (see normalize_size). Results are in
    "recommended" order: most query terms matched, then in stock, then name.
    """
    terms = _query_terms(query)
    in_category = CATEGORY_RULES.get(category) if category else None
    found: list[Candidate] = []
    with get_connection() as conn:
        for row in conn.execute("SELECT * FROM catalogue").fetchall():
            if in_category and not in_category((row["garment_type"] or "").lower()):
                continue
            price = row["price"]
            if (min_price is not None or max_price is not None) and price is None:
                continue
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue
            matched_colors: list[str] = []
            if colors:
                matched = _color_matches(colors, _json_list(row["colors"]))
                if matched is None:
                    continue
                matched_colors = matched
            words, phrase_text = _searchable(row)
            score = sum(1 for alternatives in terms if _term_matches(alternatives, words, phrase_text))
            if terms and score == 0:
                continue
            stock = _stock_for(conn, row["product_id"])
            if size and not any(s.size == size and s.quantity > 0 for s in stock):
                continue
            if in_stock_only and not any(s.quantity > 0 for s in stock):
                continue
            found.append(Candidate(row, stock, score, matched_colors))
    found.sort(key=lambda c: (-c.score, not c.in_stock, c.row["name"]))
    return found


def search_products(
    ctx: RunContext[ChatDeps],
    query: str = "",
    category: Category | None = None,
    max_price: float | None = None,
    size: str | None = None,
) -> ProductSearchResult:
    """Search the Campus Customs catalogue and return matching products for product cards.

    Use this whenever the customer asks to see, browse or find a type or category of
    product ("What hoodies do you have?", "Show me Yale shirts", "Do you have mugs?") or
    looks for a specific product by name. For requests with preferences or a budget
    ("something blue under $40", "a gift for a student", "what do you recommend?") use
    recommend_products instead. Returns the best matches first (at most 12) with price,
    short description, image and sizes in stock. An empty `products` list means nothing
    in the catalogue matched.

    Args:
        query: Words describing the product, e.g. "navy", "football", "Davenport", "mugs".
            Matched against name, garment type, description, colors and search tags.
            May be empty when `category` is given.
        category: A kind of garment to browse: hoodies, sweatshirts (hoodies, crewnecks
            and quarter-zips), crewnecks, quarter-zips, t-shirts, shirts (t-shirts and
            long-sleeve shirts), long-sleeve shirts or jackets. Leave empty for anything
            else (e.g. mugs, hats) and put those words in `query` instead.
        max_price: Only return products costing this many US dollars or less.
        size: Only return products with this size in stock, e.g. "M", "medium", "XL".
    """
    wanted_size = normalize_size(size) if size else None
    if size and wanted_size is None:
        return ProductSearchResult(
            query=query,
            category=category,
            total_matches=0,
            products=[],
            message=f"'{size}' is not a size we use. Sizes in the inventory are {', '.join(SIZE_ORDER)}.",
        )
    candidates = find_products(query, category=category, max_price=max_price, size=wanted_size)
    matches = [_product_match(c.row, c.stock) for c in candidates]

    message = None
    if not matches:
        filters = [f"in the {category} category"] if category else []
        if max_price is not None:
            filters.append(f"at or under ${max_price:.2f}")
        if wanted_size:
            filters.append(f"in stock in size {wanted_size}")
        message = "No products in the catalogue matched" + (f" ({', '.join(filters)})" if filters else "") + "."
    elif len(matches) > MAX_SEARCH_RESULTS:
        message = (
            f"Showing the first {MAX_SEARCH_RESULTS} of {len(matches)} matches; "
            "the Products page lists them all."
        )
    prices = [m.price for m in matches if m.price is not None]
    return ProductSearchResult(
        query=query,
        category=category,
        total_matches=len(matches),
        min_price=min(prices) if prices else None,
        max_price=max(prices) if prices else None,
        products=matches[:MAX_SEARCH_RESULTS],
        message=message,
    )


def get_product_details(ctx: RunContext[ChatDeps], product: str) -> ProductDetailsResult:
    """Get one product's description, price and stock quantity for every size.

    Use this whenever the customer asks about a specific product's description, price,
    colors, stock or availability.

    Args:
        product: The product_id from a search result (e.g. "baseball-left-chest-crewneck")
            or the product's exact name (e.g. "Baseball Left Chest Crewneck").
    """
    with get_connection() as conn:
        row = _find_product(conn, product)
        if row is None:
            return ProductDetailsResult(
                found=False,
                product_id=None,
                message=f"No product called '{product}' exists in the catalogue. "
                "Use search_products to look for similar items.",
            )
        stock = _stock_for(conn, row["product_id"])

    description = _text_or_none(row["description"])
    missing = []
    if description is None:
        missing.append("description")
    if row["price"] is None:
        missing.append("price")
    if not stock:
        missing.append("stock information")

    return ProductDetailsResult(
        found=True,
        product_id=row["product_id"],
        name=row["name"],
        garment_type=_text_or_none(row["garment_type"]),
        description=description,
        colors=_json_list(row["colors"]),
        price=row["price"],
        total_stock=sum(s.quantity for s in stock) if stock else None,
        availability=_availability(stock),
        sizes=stock,
        sizes_in_stock=[s.size for s in stock if s.quantity > 0],
        sizes_out_of_stock=[s.size for s in stock if s.quantity <= 0],
        message=f"The catalogue has no {' or '.join(missing)} for this product." if missing else None,
    )


def check_size_stock(ctx: RunContext[ChatDeps], product: str, size: str) -> SizeStockResult:
    """Check how many of one product are in stock in one specific size.

    Use this whenever the customer asks about a particular size, e.g. "Is the
    Davenport crewneck available in medium?" or "Do you have XL?".

    Args:
        product: The product_id from a search result or the product's exact name.
        size: The size the customer asked about, e.g. "M", "medium", "XL", "2XL".
    """
    wanted = normalize_size(size)
    with get_connection() as conn:
        row = _find_product(conn, product)
        if row is None:
            return SizeStockResult(
                status="product_not_found",
                requested_size=size,
                size=wanted,
                message=f"No product called '{product}' exists in the catalogue. "
                "Use search_products to look for similar items.",
            )
        stock = _stock_for(conn, row["product_id"])

    found = {
        "product_id": row["product_id"],
        "name": row["name"],
        "price": row["price"],
        "requested_size": size,
        "size": wanted,
        "sizes_offered": [s.size for s in stock],
    }
    others = [s.size for s in stock if s.quantity > 0 and s.size != wanted]

    if wanted is None:
        return SizeStockResult(
            **found,
            status="invalid_size",
            other_sizes_in_stock=others,
            message=f"'{size}' is not a size we use. Sizes in the inventory are {', '.join(SIZE_ORDER)}.",
        )

    if not stock:
        return SizeStockResult(
            **found,
            status="stock_unknown",
            message=f"The inventory has no stock information for {row['name']}, so its stock is unknown.",
        )
    entry = next((s for s in stock if s.size == wanted), None)
    if entry is None:
        return SizeStockResult(
            **found,
            status="size_not_offered",
            other_sizes_in_stock=others,
            message=f"{row['name']} is not offered in size {wanted}.",
        )
    if entry.quantity <= 0:
        return SizeStockResult(
            **found,
            status="out_of_stock",
            quantity=0,
            other_sizes_in_stock=others,
            message=f"{row['name']} is out of stock in size {wanted}.",
        )
    return SizeStockResult(
        **found,
        status=entry.status,
        quantity=entry.quantity,
        other_sizes_in_stock=others,
        message=f"{row['name']} has {entry.quantity} in stock in size {wanted}.",
    )


MAX_RECOMMENDATIONS = 6


def _size_range(sizes: list[str]) -> str:
    """"XS–XXL" only when every size in between is included; otherwise a plain list."""
    if not sizes:
        return "no sizes"
    idx = [SIZE_ORDER.index(z) for z in sizes if z in SIZE_ORDER]
    consecutive = len(idx) == len(sizes) and idx == list(range(idx[0], idx[0] + len(idx)))
    if len(sizes) > 2 and consecutive:
        return f"{sizes[0]}–{sizes[-1]}"
    return ", ".join(sizes)


def _matched_keywords(keywords: str, row: sqlite3.Row) -> list[str]:
    """The customer's keywords (as normalized query terms) that this product matches."""
    words, phrase_text = _searchable(row)
    return [alts[0] for alts in _query_terms(keywords) if _term_matches(alts, words, phrase_text)]


def _reason(c: Candidate, criteria: RecommendationCriteria) -> str:
    """Why a product fits, stated only with values read from the catalogue and inventory."""
    row = c.row
    parts: list[str] = []
    if criteria.category and row["garment_type"]:
        parts.append(f"a {row['garment_type']}")
    if c.matched_colors:
        parts.append("comes in " + ", ".join(c.matched_colors))
    price = row["price"]
    if price is not None and criteria.max_price is not None:
        parts.append(f"${price:.2f}, within your ${criteria.max_price:.2f} budget")
    elif price is not None and criteria.min_price is not None:
        parts.append(f"${price:.2f}, at or above ${criteria.min_price:.2f}")
    if criteria.size:
        qty = next((s.quantity for s in c.stock if s.size == criteria.size), 0)
        parts.append(f"size {criteria.size} in stock ({qty} left)" if qty <= LOW_STOCK_THRESHOLD else f"size {criteria.size} in stock")
    elif c.in_stock:
        parts.append("in stock in " + _size_range([s.size for s in c.stock if s.quantity > 0]))
    if criteria.keywords:
        hits = _matched_keywords(criteria.keywords, row)
        if hits:
            parts.append("matches " + ", ".join(f'"{h}"' for h in hits))
    text = "; ".join(parts) if parts else (row["garment_type"] or "catalogue item")
    return text[0].upper() + text[1:]


def _varied_picks(candidates: list[Candidate], limit: int) -> list[Candidate]:
    """With no stated preferences: the best-stocked product of each kind, for variety."""
    ranked = sorted(candidates, key=lambda c: (-sum(1 for s in c.stock if s.quantity > 0), c.row["name"]))
    picks: list[Candidate] = []
    seen_types: set[str] = set()
    for c in ranked:
        kind = (category_of(c.row["garment_type"]) or [c.row["garment_type"] or ""])[0]
        if kind in seen_types:
            continue
        seen_types.add(kind)
        picks.append(c)
        if len(picks) == limit:
            break
    return picks


def recommend_products(
    ctx: RunContext[ChatDeps],
    keywords: str = "",
    category: Category | None = None,
    colors: list[str] | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    size: str | None = None,
    in_stock_only: bool = True,
) -> RecommendationResult:
    """Recommend products that fit the customer's stated preferences, each with a reason.

    Use this for requests with preferences, a budget or an occasion: "a Yale sweatshirt
    under $60", "something blue", "a gift for a Yale student", "something under $40",
    "a hoodie in medium", "what would you recommend?". Pass only preferences the customer
    actually stated; leave the rest empty. Returns up to 6 products, best first, each with
    a `match_reason` built from catalogue data. When nothing matches, `suggestions` says
    which constraint to relax and how many products that would give.

    Args:
        keywords: Other words to match in name, description and search tags, e.g. "football",
            "Davenport", "dad", "student", "vintage". Empty if none.
        category: hoodies, sweatshirts (hoodies, crewnecks and quarter-zips), crewnecks,
            quarter-zips, t-shirts, shirts, long-sleeve shirts or jackets.
        colors: Colors the product must come in, e.g. ["blue"]. "blue" also matches navy.
        max_price: Budget ceiling in US dollars ("under $60" -> 60).
        min_price: Price floor in US dollars, if the customer gave one.
        size: A size that must be in stock, e.g. "M", "medium", "XL".
        in_stock_only: Only recommend products with stock (default true).
    """
    wanted_size = normalize_size(size) if size else None
    criteria = RecommendationCriteria(
        keywords=keywords.strip(),
        category=category,
        colors=[c.strip().lower() for c in (colors or []) if c.strip()],
        min_price=min_price,
        max_price=max_price,
        size=wanted_size,
        in_stock_only=in_stock_only,
    )
    if size and wanted_size is None:
        return RecommendationResult(
            criteria=criteria, total_matches=0, recommendations=[],
            message=f"'{size}' is not a size we use. Sizes in the inventory are {', '.join(SIZE_ORDER)}.",
        )

    def run(c: RecommendationCriteria) -> list[Candidate]:
        return find_products(
            c.keywords, category=c.category, min_price=c.min_price, max_price=c.max_price,
            size=c.size, in_stock_only=c.in_stock_only, colors=c.colors,
        )

    candidates = run(criteria)
    stated = any([criteria.keywords, criteria.category, criteria.colors, criteria.size,
                  criteria.min_price is not None, criteria.max_price is not None])
    if stated:
        # Best match first; among equals, more sizes in stock, then lower price.
        candidates.sort(key=lambda c: (
            -c.score, not c.in_stock, -sum(1 for s in c.stock if s.quantity > 0),
            c.row["price"] if c.row["price"] is not None else float("inf"), c.row["name"],
        ))
        picks = candidates[:MAX_RECOMMENDATIONS]
    else:
        picks = _varied_picks(candidates, MAX_RECOMMENDATIONS)

    recommendations = []
    for c in picks:
        match = _product_match(c.row, c.stock)
        match.match_reason = _reason(c, criteria)
        ctx.deps.recommendation_reasons[match.product_id] = match.match_reason
        recommendations.append(match)

    suggestions: list[RelaxationSuggestion] = []
    message = None
    if not candidates:
        message = "No products in the catalogue meet all of these preferences."
        relaxations = [
            ("keywords", {"keywords": ""}, f'Drop the keywords "{criteria.keywords}"'),
            ("category", {"category": None}, f"Look beyond {criteria.category}"),
            ("colors", {"colors": []}, f"Consider colors other than {', '.join(criteria.colors)}"),
            ("max_price", {"max_price": None}, f"Raise or remove the ${criteria.max_price:.2f} price limit" if criteria.max_price is not None else ""),
            ("min_price", {"min_price": None}, "Remove the minimum price"),
            ("size", {"size": None}, f"Consider sizes other than {criteria.size}"),
            ("in_stock_only", {"in_stock_only": False}, "Include items that are currently out of stock"),
        ]
        for constraint, change, text in relaxations:
            value = getattr(criteria, constraint)
            if value in ("", None, [], False):
                continue
            count = len(run(criteria.model_copy(update=change)))
            if count:
                suggestions.append(RelaxationSuggestion(constraint=constraint, suggestion=text, matches=count))
    elif not stated:
        message = "No preferences given: a varied selection, one of each kind, best stocked first."

    return RecommendationResult(
        criteria=criteria,
        total_matches=len(candidates),
        recommendations=recommendations,
        suggestions=suggestions,
        message=message,
    )


def list_garment_types(ctx: RunContext[ChatDeps]) -> list[GarmentTypeSummary]:
    """List every kind of item sold, with how many products there are and the price range.

    Use this to answer "what do you sell?" or to see which kinds of items exist.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT garment_type, COUNT(*) AS product_count,"
            " MIN(price) AS min_price, MAX(price) AS max_price"
            " FROM catalogue GROUP BY lower(garment_type) ORDER BY product_count DESC"
        ).fetchall()
    return [GarmentTypeSummary(**dict(row)) for row in rows]


#: Every tool the agent can call; agent.py registers this list.
TOOLS = [search_products, recommend_products, get_product_details, check_size_stock, list_garment_types]


# --- Used by the API, not the agent --------------------------------------------


def resolve_page_context(info: PageInfo | None) -> PageContext | None:
    """Turn the page the frontend reports into trusted page context for the agent.

    Only the product_id is taken from the browser; the product's name, description,
    colors and price are read from the catalogue. Stock is left out on purpose so the
    agent checks it with a tool and always quotes current numbers.
    """
    if info is None:
        return None
    if info.page_type != "product_detail" or not info.product_id:
        return PageContext(page_type=info.page_type, path=info.path)

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (info.product_id,)
        ).fetchone()
    if row is None:
        return PageContext(page_type=info.page_type, path=info.path, product_not_found=True)
    return PageContext(
        page_type=info.page_type,
        path=info.path,
        product=CurrentProduct(
            product_id=row["product_id"],
            name=row["name"],
            garment_type=_text_or_none(row["garment_type"]),
            description=_text_or_none(row["description"]),
            colors=_json_list(row["colors"]),
            price=row["price"],
        ),
    )



def product_matches(product_ids: list[str], reasons: dict[str, str] | None = None) -> list[ProductMatch]:
    """Build the structured product matches for the IDs the agent chose to show.

    Each match is rebuilt from the database with the same builder the search tool
    uses, so the frontend receives exactly the fields and values the tool saw, and a
    name, price or image can never come from the model's text. Unknown IDs and
    duplicates are dropped.
    """
    matches: list[ProductMatch] = []
    seen: set[str] = set()
    with get_connection() as conn:
        for product_id in product_ids:
            if product_id in seen:
                continue
            seen.add(product_id)
            row = conn.execute(
                "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
            ).fetchone()
            if row is not None:
                match = _product_match(row, _stock_for(conn, product_id))
                match.match_reason = (reasons or {}).get(product_id)
                matches.append(match)
    return matches


def _shown_product(position: int, row: sqlite3.Row) -> ShownProduct:
    return ShownProduct(
        position=position,
        product_id=row["product_id"],
        name=row["name"],
        garment_type=_text_or_none(row["garment_type"]),
        colors=_json_list(row["colors"]),
        price=row["price"],
    )


def build_conversation_context(history: list, page: PageContext | None) -> ConversationContext:
    """Structured follow-up context: the cards most recently shown and the selected product.

    `history` is the list of ChatTurn the agent will see (from the database for
    logged-in customers, from the browser for guests). Product IDs are re-read from
    the catalogue, so names, colors and prices are real and unknown IDs are dropped.
    """
    recent: list[ShownProduct] = []
    query = None
    for i in range(len(history) - 1, -1, -1):
        turn = history[i]
        if turn.role == "assistant" and turn.product_ids:
            with get_connection() as conn:
                for pid in turn.product_ids:
                    row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (pid,)).fetchone()
                    if row is not None:
                        recent.append(_shown_product(len(recent) + 1, row))
            query = next((history[j].content for j in range(i - 1, -1, -1) if history[j].role == "user"), None)
            break

    if page is not None and page.product is not None:
        p = page.product
        selected = ShownProduct(position=1, product_id=p.product_id, name=p.name,
                                garment_type=p.garment_type, colors=p.colors, price=p.price)
        source = "current_page"
    elif len(recent) == 1:
        selected, source = recent[0], "only_recent_product"
    else:
        selected, source = None, None
    return ConversationContext(
        recent_products=recent, recent_products_query=query,
        selected_product=selected, selected_product_source=source,
    )
