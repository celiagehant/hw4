import { createContext, useContext, useState, type ReactNode } from "react";

/**
 * Lets any page open the chat panel, or open it and ask Dan a question
 * (e.g. the home page's "Ask our AI stylist" button or a suggested prompt).
 */
interface ChatUIState {
  isOpen: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
  /** Opens the chat and sends `prompt` as the customer's message. */
  ask: (prompt: string) => void;
  pendingPrompt: string | null;
  consumePrompt: () => void;
}

const ChatUIContext = createContext<ChatUIState | null>(null);

export function ChatUIProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [pendingPrompt, setPendingPrompt] = useState<string | null>(null);

  const value: ChatUIState = {
    isOpen,
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
    toggle: () => setIsOpen((v) => !v),
    ask: (prompt) => {
      setIsOpen(true);
      setPendingPrompt(prompt);
    },
    pendingPrompt,
    consumePrompt: () => setPendingPrompt(null),
  };
  return <ChatUIContext.Provider value={value}>{children}</ChatUIContext.Provider>;
}

export function useChatUI(): ChatUIState {
  const context = useContext(ChatUIContext);
  if (!context) throw new Error("useChatUI must be used inside ChatUIProvider");
  return context;
}
