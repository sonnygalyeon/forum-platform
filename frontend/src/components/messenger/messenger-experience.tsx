"use client";

import { WifiOff } from "lucide-react";
import { useEffect, useState } from "react";
import { MessengerShell } from "@/components/messenger/messenger-shell";

function focusListSearch() {
  document.querySelector<HTMLInputElement>(".messenger-search-box input")?.focus();
}

function focusMessageSearch() {
  const input = document.querySelector<HTMLInputElement>(".chat-search-bar input");
  if (input) {
    input.focus();
    return;
  }
  const toggle = document.querySelector<HTMLButtonElement>('.chat-header-actions button[title="Поиск в чате"]');
  toggle?.click();
  window.setTimeout(() => document.querySelector<HTMLInputElement>(".chat-search-bar input")?.focus(), 0);
}

function closeTransientSearch() {
  const close = document.querySelector<HTMLButtonElement>(".chat-search-bar button:last-child");
  if (close) {
    close.click();
    return true;
  }
  return false;
}

export function MessengerExperience({ initialConversationId }: { initialConversationId?: string }) {
  const [online, setOnline] = useState(true);

  useEffect(() => {
    const syncOnlineState = () => setOnline(navigator.onLine);
    syncOnlineState();
    window.addEventListener("online", syncOnlineState);
    window.addEventListener("offline", syncOnlineState);

    const onKeyDown = (event: KeyboardEvent) => {
      const command = event.metaKey || event.ctrlKey;
      if (command && event.key.toLowerCase() === "k") {
        event.preventDefault();
        focusListSearch();
        return;
      }
      if (command && event.key.toLowerCase() === "f" && document.querySelector(".messenger-chat.has-chat")) {
        event.preventDefault();
        focusMessageSearch();
        return;
      }
      if (event.key === "Escape") {
        if (closeTransientSearch()) return;
        if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("online", syncOnlineState);
      window.removeEventListener("offline", syncOnlineState);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, []);

  return (
    <div className="messenger-experience-boundary">
      {!online ? <div className="messenger-offline-banner"><WifiOff size={14}/> Нет сети. Сообщения и черновики сохранятся локально до переподключения.</div> : null}
      <div className="messenger-shortcuts" aria-hidden="true"><kbd>⌘/Ctrl K</kbd> чаты <span>·</span> <kbd>⌘/Ctrl F</kbd> сообщения <span>·</span> <kbd>Esc</kbd> закрыть поиск</div>
      <MessengerShell initialConversationId={initialConversationId}/>
    </div>
  );
}
