"""Campus Customs chatbot agent.

Wires together the system prompt (prompts/prompt.md), the course model reached
through Portkey, the catalogue tools (tools.py) and the structured output type
(models.AgentReply). FastAPI calls `chat()`; nothing here knows about HTTP.
"""

import os
from functools import lru_cache
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from dotenv import load_dotenv  # noqa: E402
from pydantic_ai import Agent, RunContext, capture_run_messages  # noqa: E402
from pydantic_ai.messages import (  # noqa: E402
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIResponsesModel  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402
from pydantic_ai.exceptions import UnexpectedModelBehavior, UsageLimitExceeded  # noqa: E402
from pydantic_ai.usage import UsageLimits  # noqa: E402

import audit  # noqa: E402

from models import (  # noqa: E402
    AgentReply,
    ChatResponse,
    ChatTurn,
    ConversationContext,
    CustomerContext,
    PageContext,
)
from tools import TOOLS, ChatDeps, product_matches  # noqa: E402

MODEL_NAME = "gpt-5.6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent  # Homework 4/
REPO_ROOT = PROJECT_DIR.parent  # the course folder, which holds the shared .env
SYSTEM_PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"

#: Most model requests one chat turn may make (tool calls plus the final answer).
MAX_MODEL_REQUESTS = 8
#: Most earlier turns of the conversation passed back to the model as context.
MAX_HISTORY_TURNS = 20
#: Most product matches returned with one reply (same as the search tool's limit).
MAX_PRODUCT_MATCHES = 12


class AgentNotConfigured(RuntimeError):
    """Raised when PORTKEY_API_KEY is missing, so the API can report it clearly."""


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def get_agent() -> Agent[ChatDeps, AgentReply]:
    """Build the agent once, on first use, and reuse it for every request."""
    # Same approach as the rest of the course: the key lives in the shared .env
    # at the course root (a Homework 4/.env, if present, can override it).
    load_dotenv(REPO_ROOT / ".env")
    load_dotenv(PROJECT_DIR / ".env", override=True)

    api_key = os.environ.get("PORTKEY_API_KEY")
    if not api_key:
        raise AgentNotConfigured("PORTKEY_API_KEY is not set.")

    model = OpenAIResponsesModel(
        MODEL_NAME,
        provider=OpenAIProvider(api_key=api_key, base_url=PORTKEY_BASE_URL),
    )
    agent = Agent(
        model,
        deps_type=ChatDeps,
        output_type=AgentReply,
        instructions=load_system_prompt(),
        tools=TOOLS,
        retries=2,
    )

    # Per-request context. These functions run on every agent run and read only
    # ctx.deps, so customer data never lives in prompt.md or in the cached agent.
    @agent.instructions
    def customer_context(ctx: RunContext[ChatDeps]) -> str:
        return describe_customer(ctx.deps.customer)

    @agent.instructions
    def page_context(ctx: RunContext[ChatDeps]) -> str:
        return describe_page(ctx.deps.page)

    @agent.instructions
    def conversation_context(ctx: RunContext[ChatDeps]) -> str:
        return describe_conversation(ctx.deps.conversation)

    return agent


def describe_customer(customer: CustomerContext | None) -> str:
    if customer is None:
        return (
            "## Current customer\n"
            "No authenticated customer: this is a guest who is not logged in. You do not know "
            "their name or any account details, so don't use or guess a name. This conversation "
            "is not saved after the visit ends."
        )
    return (
        "## Current customer\n"
        "Logged in. This record comes from the customer's authenticated session:\n"
        f"{customer.model_dump_json()}\n"
        "Their conversation is saved to their account, and the earlier messages above are "
        "from their saved history."
    )


def describe_page(page: PageContext | None) -> str:
    if page is None:
        return "## Current page\nUnknown: the website did not say which page the customer is on."
    lines = ["## Current page", f"Page type: {page.page_type} (path {page.path})."]
    if page.product is not None:
        lines.append(
            "The customer is viewing this product right now. \"This\", \"this one\", \"it\" or "
            "\"the product I'm looking at\" mean this product unless they clearly mean another:"
        )
        lines.append(page.product.model_dump_json())
    elif page.product_not_found:
        lines.append("This is a product page, but its product is not in the catalogue.")
    else:
        lines.append("No specific product is shown on this page.")
    return "\n".join(lines)


def describe_conversation(conversation: ConversationContext | None) -> str:
    lines = ["## Recent products and selected product"]
    if conversation is None or not conversation.recent_products:
        lines.append("No product cards have been shown in this conversation yet.")
    else:
        if conversation.recent_products_query:
            lines.append(f'Most recent product cards, shown in reply to "{conversation.recent_products_query}", in display order:')
        else:
            lines.append("Most recent product cards, in display order:")
        lines.extend(p.model_dump_json() for p in conversation.recent_products)
    if conversation is not None and conversation.selected_product is not None:
        source = {
            "current_page": "the product page the customer is viewing",
            "only_recent_product": "the only product in the most recent product reply",
        }[conversation.selected_product_source]
        lines.append(f"Selected product ({source}): {conversation.selected_product.model_dump_json()}")
    else:
        lines.append("Selected product: none. No single product is clearly in focus.")
    return "\n".join(lines)


def to_message_history(history: list[ChatTurn]) -> list[ModelMessage]:
    """Turn earlier chat turns into PydanticAI message history.

    The one conversion used for both sources: turns loaded from the chat_messages
    table (logged-in customers) and turns sent by the browser (guests).
    """
    turns = history[-MAX_HISTORY_TURNS:]
    while turns and turns[0].role != "user":  # history must start with a customer message
        turns = turns[1:]
    messages: list[ModelMessage] = []
    for turn in turns:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            content = turn.content
            if turn.product_ids:
                # Keeps "the second one" or "that hoodie" resolvable in later messages.
                content += "\n[Product cards shown with this reply: " + ", ".join(turn.product_ids) + "]"
            messages.append(ModelResponse(parts=[TextPart(content=content)]))
    return messages


def _stop_reason(error: BaseException | None) -> str:
    """Why the agent loop ended, in a few safe words for the audit trail."""
    if error is None:
        return "final_result"  # the model returned a valid AgentReply
    if isinstance(error, UsageLimitExceeded):
        return f"request_limit_reached ({MAX_MODEL_REQUESTS} model requests)"
    if isinstance(error, UnexpectedModelBehavior):
        return "model_error (invalid output after retries)"
    if isinstance(error, AgentNotConfigured):
        return "not_configured"
    return f"error ({type(error).__name__})"


async def chat(message: str, history: list[ChatTurn], deps: ChatDeps) -> ChatResponse:
    """Answer one customer message, given the conversation so far and who/where they are.

    Every run, successful or not, is recorded in the append-only audit trail.
    """
    run_id = audit.new_run_id()
    started = {
        "time": audit.now(),
        "customer": "guest" if deps.is_guest else "authenticated",  # never the identity itself
        "page_type": deps.page.page_type if deps.page else None,
        "page_product_id": deps.page.product.product_id if deps.page and deps.page.product else None,
        "history_turns": len(history),
        "message_chars": len(message),  # length only: chat text is private
    }
    messages: list[ModelMessage] = []
    error: BaseException | None = None
    response: ChatResponse | None = None
    try:
        with capture_run_messages() as messages:
            result = await get_agent().run(
                message,
                message_history=to_message_history(history),
                deps=deps,
                usage_limits=UsageLimits(request_limit=MAX_MODEL_REQUESTS),
            )
        output = result.output
        response = ChatResponse(
            reply=output.reply,
            product_matches=product_matches(output.product_ids[:MAX_PRODUCT_MATCHES], deps.recommendation_reasons),
        )
        return response
    except BaseException as exc:
        error = exc
        raise
    finally:
        # Only this run's new messages (not the replayed history) are audited.
        new_messages = messages[len(to_message_history(history)):] if messages else []
        try:
            audit.append(
                audit.entries_for_run(
                    run_id,
                    started,
                    new_messages,
                    _stop_reason(error),
                    [m.product_id for m in response.product_matches] if response else None,
                )
            )
        except Exception:  # auditing must never break the chat
            audit.logger.exception("Could not write audit entries")
