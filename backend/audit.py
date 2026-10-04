"""Append-only audit trail of agent-loop activity: output/audit_trail.json.

The file is a JSON array. Each agent run appends:
  * one "run_start" entry (kind of customer, page, message length; no message text),
  * one "tool_call" entry per tool the model called (tool, args summary, result summary),
  * one "run_end" entry with the stop_reason, model-request count and token usage.

Append-only: existing entries are read, never modified or removed, and the new
entries are added at the end. Writes are serialized with a lock and replace the
file atomically, so a crash can never leave a half-written or truncated trail.
If the file cannot be parsed, nothing is written (the existing file is never
overwritten) and the problem is logged.

Privacy: no chat text, names, emails, user IDs, passwords, hashes, tokens, keys or
environment values are ever recorded. Tool arguments and results are summarized,
string values are length-capped, and anything that looks like an email address or
a secret is redacted before writing.
"""

import fcntl
import json
import logging
import os
import re
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic_ai.messages import ModelMessage, ModelResponse, RetryPromptPart, ToolCallPart, ToolReturnPart

from models import ProductDetailsResult, ProductSearchResult, RecommendationResult, SizeStockResult

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
LOCK_PATH = AUDIT_PATH.parent / ".audit_trail.lock"  # hidden, next to the trail
MAX_STRING = 80  # longest string value written to the trail
FINAL_RESULT_TOOL = "final_result"  # PydanticAI's internal tool for the structured answer

logger = logging.getLogger("campus_customs.audit")
_thread_lock = threading.Lock()

# Keys whose values are never written, whatever they contain.
SENSITIVE_KEYS = re.compile(r"pass(word)?|hash|token|secret|api[_-]?key|authorization|cookie|session|email", re.I)
EMAIL = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
# Key prefixes, long unbroken runs of letters/digits (hyphens excluded, so product
# IDs like "brooks-brothers-double-knit-full-zip-hoodie-yale" are kept) and hashes.
SECRET_LIKE = re.compile(r"\b(?:sk|pk|key|tok)[-_][A-Za-z0-9_\-]{8,}\b|\b[A-Za-z0-9_+/=]{32,}\b|\$argon2\S*|pbkdf2_sha256\$\S*")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _clean_text(value: str) -> str:
    value = EMAIL.sub("[redacted-email]", value)
    value = SECRET_LIKE.sub("[redacted]", value)
    return value if len(value) <= MAX_STRING else value[: MAX_STRING - 1] + "…"


def sanitize(value: Any) -> Any:
    """Make a value safe and short enough for the audit trail."""
    if isinstance(value, BaseModel):
        value = value.model_dump()
    if isinstance(value, dict):
        return {
            str(k): "[redacted]" if SENSITIVE_KEYS.search(str(k)) else sanitize(v)
            for k, v in value.items()
            if v not in (None, "", [], {})
        }
    if isinstance(value, (list, tuple)):
        items = [sanitize(v) for v in value[:6]]
        return items + [f"…{len(value) - 6} more"] if len(value) > 6 else items
    if isinstance(value, str):
        return _clean_text(value)
    return value


def summarize_result(content: Any) -> str:
    """One short line describing what a tool returned (no full payloads)."""
    if isinstance(content, ProductSearchResult):
        names = ", ".join(p.name for p in content.products[:3])
        return f"{content.total_matches} matches, {len(content.products)} returned" + (f"; first: {names}" if names else "")
    if isinstance(content, RecommendationResult):
        names = ", ".join(p.name for p in content.recommendations[:3])
        extra = f"; {len(content.suggestions)} relaxation suggestions" if content.suggestions else ""
        return f"{content.total_matches} matches, {len(content.recommendations)} recommended" + (f"; first: {names}" if names else "") + extra
    if isinstance(content, ProductDetailsResult):
        if not content.found:
            return "product not found"
        return f"{content.name}: price {content.price}, total stock {content.total_stock}, availability {content.availability}"
    if isinstance(content, SizeStockResult):
        return f"{content.name or 'unknown product'}: status {content.status}, size {content.size}, quantity {content.quantity}"
    if isinstance(content, list):
        return f"{len(content)} items"
    return _clean_text(str(content))


def _tool_args(part: ToolCallPart) -> Any:
    try:
        return sanitize(part.args_as_dict())
    except Exception:  # malformed JSON from the model
        return "[unparseable arguments]"


def entries_for_run(
    run_id: str,
    started: dict,
    messages: list[ModelMessage],
    stop_reason: str,
    product_ids: list[str] | None = None,
) -> list[dict]:
    """Build the audit entries for one run from its captured PydanticAI messages."""
    entries: list[dict] = [{"run_id": run_id, "event": "run_start", **started}]
    calls: dict[str, dict] = {}
    model_requests = 0
    input_tokens = output_tokens = 0

    for message in messages:
        if isinstance(message, ModelResponse):
            model_requests += 1
            input_tokens += message.usage.input_tokens or 0
            output_tokens += message.usage.output_tokens or 0
        for part in message.parts:
            if isinstance(part, ToolCallPart) and part.tool_name != FINAL_RESULT_TOOL:
                entry = {
                    "run_id": run_id,
                    "event": "tool_call",
                    "time": message.timestamp.isoformat(timespec="milliseconds"),
                    "tool": part.tool_name,
                    "args": _tool_args(part),
                    "result": None,
                }
                calls[part.tool_call_id] = entry
                entries.append(entry)
            elif isinstance(part, ToolReturnPart) and part.tool_call_id in calls:
                calls[part.tool_call_id]["result"] = summarize_result(part.content)
            elif isinstance(part, RetryPromptPart) and part.tool_call_id in calls:
                calls[part.tool_call_id]["result"] = "tool call rejected; model asked to retry"

    end = {
        "run_id": run_id,
        "event": "run_end",
        "time": now(),
        "stop_reason": stop_reason,
        "model_requests": model_requests,
        "tool_calls": len(calls),
        "tokens": {"input": input_tokens, "output": output_tokens},
    }
    if product_ids is not None:
        end["product_cards_returned"] = len(product_ids)
    entries.append(end)
    return entries


def append(entries: list[dict]) -> None:
    """Append entries to the trail, preserving every existing entry."""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _thread_lock, open(LOCK_PATH, "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)  # also serializes separate processes
        try:
            existing = json.loads(AUDIT_PATH.read_text(encoding="utf-8")) if AUDIT_PATH.exists() else []
        except (json.JSONDecodeError, OSError):
            logger.error("Audit trail unreadable; not overwriting it, new entries skipped")
            return
        if not isinstance(existing, list):
            logger.error("Audit trail is not a JSON array; not overwriting it, new entries skipped")
            return
        fd, tmp = tempfile.mkstemp(dir=AUDIT_PATH.parent, prefix=".audit-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(existing + entries, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.chmod(tmp, 0o644)  # mkstemp creates 0600; the trail should be readable like other outputs
        os.replace(tmp, AUDIT_PATH)


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]
