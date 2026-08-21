"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { clientApi } from "@/lib/client-api";
import type { MessengerSocketEvent } from "@/lib/types";

function websocketBase() {
  if (typeof window === "undefined") return "";
  if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    return "ws://localhost:8000/ws/messenger/";
  }
  return `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/messenger/`;
}

export function useMessengerSocket(onEvent: (event: MessengerSocketEvent) => void, enabled = true) {
  const socketRef = useRef<WebSocket | null>(null);
  const callbackRef = useRef(onEvent);
  const retryRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [connected, setConnected] = useState(false);

  callbackRef.current = onEvent;

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;

    const connect = async () => {
      try {
        const { ticket } = await clientApi<{ ticket: string }>("/messenger/ws-ticket/", { method: "POST" });
        if (cancelled) return;
        const socket = new WebSocket(`${websocketBase()}?ticket=${encodeURIComponent(ticket)}`);
        socketRef.current = socket;
        socket.onopen = () => {
          retryRef.current = 0;
          setConnected(true);
          heartbeatRef.current = setInterval(() => {
            if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: "ping" }));
          }, 30000);
        };
        socket.onmessage = event => {
          try { callbackRef.current(JSON.parse(event.data)); } catch { /* ignore malformed realtime payload */ }
        };
        socket.onclose = () => {
          setConnected(false);
          if (heartbeatRef.current) clearInterval(heartbeatRef.current);
          if (!cancelled) {
            const delay = Math.min(1000 * 2 ** retryRef.current++, 10000);
            timerRef.current = setTimeout(connect, delay);
          }
        };
      } catch {
        if (!cancelled) timerRef.current = setTimeout(connect, 3000);
      }
    };
    connect();
    return () => {
      cancelled = true;
      if (timerRef.current) clearTimeout(timerRef.current);
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
      socketRef.current?.close();
    };
  }, [enabled]);

  const sendTyping = useCallback((conversationId: string, active: boolean) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: active ? "typing.start" : "typing.stop", conversation_id: conversationId }));
    }
  }, []);

  return { connected, sendTyping };
}
