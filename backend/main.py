"""Campus Customs backend: serves the product catalogue, product images, user accounts and the chatbot."""

import json
import logging
import os
import secrets
import sqlite3

from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

import agent
import auth
import chat_history
from db import DATA_DIR, get_connection
from models import ChatHistoryResponse, ChatRequest, ChatResponse, CustomerContext
import tools
from tools import ChatDeps, build_conversation_context, resolve_page_context

logger = logging.getLogger("campus_customs")

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

app = FastAPI(title="Campus Customs API")

chat_history.ensure_schema()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Signed, HTTP-only session cookie holding the logged-in user's id. Without a
# SESSION_SECRET env var a random key is used, so sessions end on restart.
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET") or secrets.token_hex(32),
    session_cookie="campus_customs_session",
    same_site="lax",
)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # FastAPI's default 422 body echoes the submitted values back, which could
    # include a password, so only the field locations and messages are returned.
    errors = [{"loc": e["loc"], "msg": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors})


app.include_router(auth.router)

# Image paths in the catalogue are relative to data/ (e.g. "products/x.jpg"),
# so each image is served at /data/<image_file_path>. Only the products folder
# is mounted, so the database file in data/ is never downloadable.
app.mount("/data/products", StaticFiles(directory=DATA_DIR / "products"), name="product-images")


def product_from_row(row: sqlite3.Row) -> dict:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        "image_url": f"/data/{row['image_file_path']}",
        "price": row["price"],
    }


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


def product_with_stock(c: tools.Candidate) -> dict:
    """A catalogue product plus its stock, as the Products page needs it."""
    product = product_from_row(c.row)
    product["inventory"] = [{"size": s.size, "quantity": s.quantity} for s in c.stock]
    product["sizes_in_stock"] = [s.size for s in c.stock if s.quantity > 0]
    product["availability"] = tools._availability(c.stock)
    product["categories"] = tools.category_of(c.row["garment_type"])
    return product


SortOption = Literal["recommended", "name_asc", "price_asc", "price_desc"]


@app.get("/api/products")
def list_products(
    q: str = Query("", max_length=200, description="Words to find in name, type, description, colors and tags."),
    category: str | None = Query(None, description="One of the categories from /api/products/filters."),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    size: str | None = Query(None, description="Only products with this size in stock."),
    in_stock: bool = Query(False, description="Only products with at least one size in stock."),
    sort: SortOption = "recommended",
) -> list[dict]:
    """Search, filter and sort the catalogue with the same search the chatbot uses."""
    if category is not None and category not in tools.CATEGORY_RULES:
        raise HTTPException(status_code=400, detail=f"Unknown category '{category}'.")
    wanted_size = tools.normalize_size(size) if size else None
    if size and wanted_size is None:
        raise HTTPException(status_code=400, detail=f"Unknown size '{size}'.")

    candidates = tools.find_products(
        q, category=category, min_price=min_price, max_price=max_price,
        size=wanted_size, in_stock_only=in_stock,
    )
    no_price = float("inf")
    if sort == "name_asc":
        candidates.sort(key=lambda c: c.row["name"].lower())
    elif sort == "price_asc":
        candidates.sort(key=lambda c: (c.row["price"] if c.row["price"] is not None else no_price, c.row["name"]))
    elif sort == "price_desc":
        candidates.sort(key=lambda c: (-(c.row["price"] or 0), c.row["name"]))
    # "recommended" keeps find_products' order: best text match, in stock first, then name.
    return [product_with_stock(c) for c in candidates]


@app.get("/api/products/filters")
def product_filters() -> dict:
    """Filter values derived from the catalogue and inventory, so the page never invents any."""
    with get_connection() as conn:
        types = [r[0] for r in conn.execute("SELECT garment_type FROM catalogue").fetchall()]
        prices = conn.execute("SELECT MIN(price), MAX(price) FROM catalogue WHERE price IS NOT NULL").fetchone()
        sizes = {r[0] for r in conn.execute("SELECT DISTINCT size FROM inventory").fetchall()}
        in_stock = conn.execute(
            "SELECT COUNT(DISTINCT product_id) FROM inventory WHERE quantity > 0"
        ).fetchone()[0]
        total = conn.execute("SELECT COUNT(*) FROM catalogue").fetchone()[0]

    categories = []
    for name, label in tools.CATEGORY_LABELS.items():
        count = sum(1 for t in types if name in tools.category_of(t))
        if count:  # only offer categories that actually contain products
            categories.append({"value": name, "label": label, "count": count})
    ordered_sizes = [z for z in tools.SIZE_ORDER if z in sizes] + sorted(sizes - set(tools.SIZE_ORDER))
    return {
        "categories": categories,
        "sizes": ordered_sizes,
        "price": {"min": prices[0], "max": prices[1]},
        "availability": {"in_stock": in_stock, "total": total},
        "sort_options": [
            {"value": "recommended", "label": "Recommended"},
            {"value": "name_asc", "label": "Name A–Z"},
            {"value": "price_asc", "label": "Price: low to high"},
            {"value": "price_desc", "label": "Price: high to low"},
        ],
    }


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        stock_rows = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()

    product = product_from_row(row)
    stock = [{"size": r["size"], "quantity": r["quantity"]} for r in stock_rows]
    stock.sort(key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else len(SIZE_ORDER))
    product["inventory"] = stock
    return product


def customer_context(request: Request) -> CustomerContext | None:
    """The authenticated customer for the agent, or None for a guest."""
    row = auth.current_user(request)
    if row is None:
        return None
    return CustomerContext(
        user_id=row["id"], first_name=row["first_name"], last_name=row["last_name"], email=row["email"]
    )


@app.get("/api/chat/history")
def get_chat_history(request: Request) -> ChatHistoryResponse:
    """The logged-in customer's saved conversation; always empty for guests."""
    customer = customer_context(request)
    if customer is None:
        return ChatHistoryResponse(authenticated=False)
    return ChatHistoryResponse(authenticated=True, messages=chat_history.load_messages(customer.user_id))


@app.post("/api/chat")
async def chat(body: ChatRequest, request: Request) -> ChatResponse:
    """Answer one customer message, with the customer's identity, history and current page."""
    customer = customer_context(request)
    if customer is not None:
        # Logged in: the saved history is the source of truth; the browser's copy is ignored.
        history = chat_history.load_turns(customer.user_id, agent.MAX_HISTORY_TURNS)
    else:
        # Guest: the conversation exists only in the browser, which sends it each time.
        history = body.history
    page = resolve_page_context(body.page)
    deps = ChatDeps(customer=customer, page=page, conversation=build_conversation_context(history, page))

    try:
        response = await agent.chat(body.message, history, deps)
    except agent.AgentNotConfigured:
        logger.error("Chat unavailable: PORTKEY_API_KEY is not set")
        raise HTTPException(status_code=503, detail="The shopping assistant is not available right now.")
    except Exception:
        # Log the failure type only; message contents stay out of the logs.
        logger.exception("Chat agent failed")
        raise HTTPException(
            status_code=502,
            detail="Sorry, the shopping assistant ran into a problem. Please try again.",
        )

    if customer is None:
        return response
    chat_history.save_exchange(customer.user_id, body.message, response.reply, response.product_matches)
    return response.model_copy(update={"saved": True})
