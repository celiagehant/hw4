import { Fragment, useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { fetchChatHistory, pageInfoFromPath, sendChatMessage, type ChatMessage } from "../api/chat";
import { fetchProduct, type ProductDetail } from "../api/products";
import type { User } from "../api/auth";
import { useAuth } from "../auth/AuthContext";
import { useChatUI } from "../chat/ChatUIContext";
import DanAvatar from "./DanAvatar";
import ProductCard from "./ProductCard";

const SUGGESTED_PROMPTS = [
  "Find me a Yale hoodie",
  "What's under $50?",
  "Help me find a gift",
  "Show me what's available in medium",
];
const PRODUCT_PAGE_PROMPTS = ["What sizes are in stock?", "Does this come in other colors?", "Show me similar styles"];

function greetingFor(user: User | null, returning = false): ChatMessage {
  const content = !user
    ? "Hi, I'm Dan, your Campus Customs shopping companion. Looking for something Yale? Ask me about styles, sizes, colors or gift ideas."
    : returning
      ? `Welcome back, ${user.first_name}! Your earlier conversation is above. What can I help you find today?`
      : `Hi ${user.first_name}, I'm Dan, your Campus Customs shopping companion. What are you looking for today?`;
  return { role: "assistant", content, localOnly: true };
}

/** Renders message text; older saved replies may contain **bold** markers. */
function renderText(text: string): ReactNode {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? <strong key={i}>{part.slice(2, -2)}</strong> : <Fragment key={i}>{part}</Fragment>,
  );
}

export default function ChatWidget() {
  const { user, loading: authLoading } = useAuth();
  const chat = useChatUI();
  const location = useLocation();
  const [messages, setMessages] = useState<ChatMessage[]>([greetingFor(null)]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [pageProduct, setPageProduct] = useState<ProductDetail | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const userId = user?.id ?? null;
  const page = pageInfoFromPath(location.pathname);

  // Whenever the logged-in customer changes (page load, log in, log out), start from
  // that customer's saved conversation, or a fresh guest conversation. Logging out
  // clears the panel, so the next person on this computer can't see the history.
  useEffect(() => {
    if (authLoading) return;
    let cancelled = false;
    setMessages([greetingFor(user)]);
    if (!user) return;

    setLoadingHistory(true);
    fetchChatHistory()
      .then((saved) => {
        if (!cancelled) setMessages(saved.length ? [...saved, greetingFor(user, true)] : [greetingFor(user)]);
      })
      .catch((err: Error) => {
        if (!cancelled)
          setMessages([greetingFor(user), { role: "assistant", content: err.message, localOnly: true, isError: true }]);
      })
      .finally(() => {
        if (!cancelled) setLoadingHistory(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload only when the account changes
  }, [authLoading, userId]);

  // On a product page, show which product Dan is helping with (name and photo from the API).
  useEffect(() => {
    if (page.page_type !== "product_detail" || !page.product_id) {
      setPageProduct(null);
      return;
    }
    const controller = new AbortController();
    fetchProduct(page.product_id, controller.signal)
      .then(setPageProduct)
      .catch(() => setPageProduct(null));
    return () => controller.abort();
  }, [page.page_type, page.product_id]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending, chat.isOpen]);

  // Focus the message box when the panel opens; Escape closes it.
  useEffect(() => {
    if (!chat.isOpen) return;
    inputRef.current?.focus({ preventScroll: true });
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && chat.close();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chat.isOpen]);

  async function send(text: string) {
    if (!text || sending || loadingHistory) return;
    const userMessage: ChatMessage = { role: "user", content: text };
    const history: ChatMessage[] = [...messages, userMessage];
    setMessages(history);
    setInput("");
    setSending(true);
    try {
      const reply = await sendChatMessage(history, pageInfoFromPath(location.pathname), Boolean(user));
      setMessages((current) => [...current, reply]);
    } catch (err) {
      const content = err instanceof Error ? err.message : "Sorry, something went wrong. Please try again.";
      // Keep the unanswered message and the error notice out of the history sent to the agent.
      setMessages((current) => [
        ...current.map((m) => (m === userMessage ? { ...m, localOnly: true } : m)),
        { role: "assistant", content, localOnly: true, isError: true },
      ]);
    } finally {
      setSending(false);
    }
  }

  // A question asked from elsewhere on the site (e.g. a suggested prompt on the home page).
  useEffect(() => {
    if (chat.pendingPrompt && !sending && !loadingHistory && !authLoading) {
      const prompt = chat.pendingPrompt;
      chat.consumePrompt();
      void send(prompt);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chat.pendingPrompt, sending, loadingHistory, authLoading]);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    void send(input.trim());
  }

  const conversationStarted = messages.some((m) => !m.localOnly);
  const prompts = pageProduct ? PRODUCT_PAGE_PROMPTS : SUGGESTED_PROMPTS;

  return (
    <div className={`chat-widget${chat.isOpen ? " is-open" : ""}`}>
      <section
        id="chat-panel"
        className="chat-panel"
        role="dialog"
        aria-label="Chat with Dan, the Campus Customs shopping companion"
        aria-hidden={!chat.isOpen}
        inert={!chat.isOpen}
      >
        <header className="chat-header">
          <DanAvatar size={40} />
          <div className="chat-header-text">
            <p className="chat-title">Dan</p>
            <p className="chat-subtitle">
              Campus Customs shopping companion
              <span className="chat-save-state">{user ? " · Chat saved to your account" : " · Guest chat, log in to save it"}</span>
            </p>
          </div>
          <button type="button" className="chat-close" onClick={chat.close} aria-label="Close chat">
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </button>
        </header>

        {pageProduct && (
          <Link to={location.pathname} className="chat-context" aria-label={`Dan is helping with ${pageProduct.name}`}>
            <img src={pageProduct.image_url} alt="" />
            <span>
              <span className="chat-context-label">Helping with</span>
              <strong>{pageProduct.name}</strong>
            </span>
          </Link>
        )}

        <div className="chat-messages" aria-live="polite">
          {loadingHistory && <p className="chat-status">Loading your conversation…</p>}
          {messages.map((message, index) => (
            <div key={index} className={`chat-row ${message.role}`}>
              {message.role === "assistant" && <DanAvatar size={28} />}
              <div className="chat-row-content">
                <div className={`chat-bubble ${message.role}${message.isError ? " error" : ""}`}>
                  {renderText(message.content)}
                </div>
                {message.productMatches && message.productMatches.length > 0 && (
                  <div className="chat-product-matches" aria-label="Products from Dan">
                    {message.productMatches.map((match) => (
                      <ProductCard
                        key={match.product_id}
                        compact
                        product={{ ...match, description: match.short_description }}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {!conversationStarted && !loadingHistory && (
            <div className="prompt-chips in-chat" aria-label="Suggested questions">
              {prompts.map((prompt) => (
                <button key={prompt} type="button" className="prompt-chip" onClick={() => void send(prompt)}>
                  {prompt}
                </button>
              ))}
            </div>
          )}

          {sending && (
            <div className="chat-row assistant">
              <DanAvatar size={28} />
              <div className="chat-bubble assistant typing" role="status">
                <span className="typing-dots" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                </span>
                <span className="typing-text">Dan is fetching that…</span>
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <form className="chat-input" onSubmit={handleSubmit}>
          <label htmlFor="chat-message" className="sr-only">
            Message Dan
          </label>
          <input
            id="chat-message"
            ref={inputRef}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder={pageProduct ? "Ask about this product…" : "Ask Dan anything about the shop…"}
            autoComplete="off"
          />
          <button type="submit" disabled={!input.trim() || sending || loadingHistory} aria-label="Send message">
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M4 12l16-8-6 16-2.5-6.5L4 12z" fill="currentColor" />
            </svg>
          </button>
        </form>
      </section>

      <button
        type="button"
        className="chat-launcher"
        onClick={chat.toggle}
        aria-expanded={chat.isOpen}
        aria-controls="chat-panel"
        aria-label={chat.isOpen ? "Close chat with Dan" : "Chat with Dan, your shopping companion"}
      >
        {chat.isOpen ? (
          <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        ) : (
          <>
            <DanAvatar size={40} />
            <span className="chat-launcher-text">Ask Dan</span>
          </>
        )}
      </button>
    </div>
  );
}
