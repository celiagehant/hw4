"""Saved chat history for logged-in customers, stored in the chat_messages table.

Every query is filtered by the authenticated user's id, which the caller takes
from the session cookie, so a customer can only ever read or add to their own
conversation. Guests never reach this module: their conversation lives only in
the browser for the current visit.
"""

import json

from db import get_connection
from models import ChatTurn, ProductMatch, StoredChatMessage
from tools import product_matches

#: Messages sent to the website when the chat is reopened.
MAX_DISPLAY_MESSAGES = 100


def ensure_schema() -> None:
    """Create the chat history table (if missing) and an index for per-user lookups.

    The table already exists in campus_customs.db with exactly this schema; this
    keeps a fresh database working too.
    """
    with get_connection() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                products_json TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )"""
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages (user_id, id)"
        )


def _stored_products(products_json: str | None) -> list[dict]:
    """The product objects in a stored products_json value, ignoring anything malformed."""
    try:
        items = json.loads(products_json) if products_json else []
    except json.JSONDecodeError:
        return []
    if not isinstance(items, list):
        return []
    return [i for i in items if isinstance(i, dict) and isinstance(i.get("product_id"), str)]


def _product_ids(products_json: str | None) -> list[str]:
    return [i["product_id"] for i in _stored_products(products_json)]


def _reasons(products_json: str | None) -> dict[str, str]:
    """Recommendation reasons saved with the cards, so they reappear on reload."""
    return {
        i["product_id"]: i["match_reason"]
        for i in _stored_products(products_json)
        if isinstance(i.get("match_reason"), str)
    }


def _recent_rows(user_id: int, limit: int) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, role, content, products_json, created_at FROM chat_messages"
            " WHERE user_id = ? AND role IN ('user', 'assistant')"
            " ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return list(reversed(rows))


def load_turns(user_id: int, limit: int) -> list[ChatTurn]:
    """The customer's most recent messages as conversation turns for the agent."""
    return [
        ChatTurn(role=r["role"], content=r["content"], product_ids=_product_ids(r["products_json"]))
        for r in _recent_rows(user_id, limit)
    ]


def load_messages(user_id: int) -> list[StoredChatMessage]:
    """The customer's recent messages for display, with product cards rebuilt from the catalogue."""
    return [
        StoredChatMessage(
            id=r["id"],
            role=r["role"],
            content=r["content"],
            product_matches=product_matches(_product_ids(r["products_json"]), _reasons(r["products_json"])),
            created_at=r["created_at"],
        )
        for r in _recent_rows(user_id, MAX_DISPLAY_MESSAGES)
    ]


def save_exchange(user_id: int, message: str, reply: str, matches: list[ProductMatch]) -> None:
    """Store one customer message and the assistant's reply, together, in one transaction.

    Called only after the agent has answered, so a failed request saves nothing and
    a retried message is never stored twice.
    """
    products_json = json.dumps([m.model_dump() for m in matches])
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'user', ?, NULL)",
            (user_id, message),
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
            (user_id, reply, products_json),
        )
