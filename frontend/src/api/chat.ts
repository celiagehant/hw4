export type ChatRole = "user" | "assistant";

/**
 * One structured product match returned by POST /api/chat.
 * Mirrors backend/models.py ProductMatch field for field.
 */
export interface ProductMatch {
  product_id: string;
  name: string;
  price: number | null;
  image_url: string | null;
  short_description: string | null;
  description: string | null;
  garment_type: string | null;
  colors: string[];
  availability: "in_stock" | "low_stock" | "out_of_stock" | "stock_unknown";
  sizes_in_stock: string[];
  /** Why a recommended product fits the request, from catalogue data; null for plain searches. */
  match_reason: string | null;
}

/** Kinds of page the chat can be opened from. Mirrors backend/models.py PageType. */
export type PageType =
  | "home"
  | "product_list"
  | "product_detail"
  | "about"
  | "login"
  | "create_account"
  | "account"
  | "other";

/** The page the customer is viewing. Mirrors backend/models.py PageInfo. */
export interface PageInfo {
  page_type: PageType;
  path: string;
  product_id: string | null;
}

/** Earlier turn sent for guests. Mirrors backend/models.py ChatTurn. */
interface ChatTurn {
  role: ChatRole;
  content: string;
  product_ids: string[];
}

/** Body of POST /api/chat. Mirrors backend/models.py ChatRequest. */
interface ChatRequest {
  message: string;
  history: ChatTurn[];
  page: PageInfo;
}

/** Response of POST /api/chat. Mirrors backend/models.py ChatResponse. */
interface ChatResponse {
  reply: string;
  product_matches: ProductMatch[];
  saved: boolean;
}

/** One saved message. Mirrors backend/models.py StoredChatMessage. */
interface StoredChatMessage {
  id: number;
  role: ChatRole;
  content: string;
  product_matches: ProductMatch[];
  created_at: string;
}

/** Response of GET /api/chat/history. Mirrors backend/models.py ChatHistoryResponse. */
interface ChatHistoryResponse {
  authenticated: boolean;
  messages: StoredChatMessage[];
}

export interface ChatMessage {
  role: ChatRole;
  content: string;
  productMatches?: ProductMatch[];
  /** Shown in the widget only (greeting, error notices); never sent to the agent. */
  localOnly?: boolean;
  isError?: boolean;
}

/** Works out which page is open from the URL, so the agent knows what "this" refers to. */
export function pageInfoFromPath(path: string): PageInfo {
  const product = path.match(/^\/products\/([^/]+)\/?$/);
  if (product) return { page_type: "product_detail", path, product_id: decodeURIComponent(product[1]) };
  const types: Record<string, PageType> = {
    "/": "home",
    "/products": "product_list",
    "/about": "about",
    "/login": "login",
    "/create-account": "create_account",
    "/account": "account",
  };
  return { page_type: types[path.replace(/\/$/, "") || "/"] ?? "other", path, product_id: null };
}

/**
 * Loads the logged-in customer's saved conversation. The server decides whose
 * history to return from the session cookie; guests always get an empty list.
 */
export async function fetchChatHistory(): Promise<ChatMessage[]> {
  const response = await fetch("/api/chat/history");
  if (!response.ok) throw new Error("Could not load your previous conversation.");
  const data = (await response.json()) as ChatHistoryResponse;
  return data.messages.map((m) => ({ role: m.role, content: m.content, productMatches: m.product_matches }));
}

/**
 * Sends the newest message, the current page and (for guests) the earlier
 * conversation to the FastAPI chat endpoint, which runs the PydanticAI agent,
 * and returns the agent's reply along with any structured product matches.
 *
 * For logged-in customers the server loads the history from the database, so the
 * browser sends none and nothing can be duplicated.
 */
export async function sendChatMessage(
  history: ChatMessage[],
  page: PageInfo,
  loggedIn: boolean,
): Promise<ChatMessage> {
  const turns = history.filter((m) => !m.localOnly);
  const latest = turns[turns.length - 1];
  const body: ChatRequest = {
    message: latest.content,
    history: loggedIn
      ? []
      : turns.slice(0, -1).map((m) => ({
          role: m.role,
          content: m.content,
          product_ids: (m.productMatches ?? []).map((p) => p.product_id),
        })),
    page,
  };

  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof data?.detail === "string" ? data.detail : null;
    throw new Error(detail ?? "Sorry, I couldn't reach the shopping assistant. Please try again.");
  }
  const reply = data as ChatResponse;
  return { role: "assistant", content: reply.reply, productMatches: reply.product_matches ?? [] };
}
